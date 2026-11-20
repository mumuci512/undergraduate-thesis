"""Offline archive, source/config, training-record and matrix audit for step 2.

Run with Python's standard library; archived Python files are parsed or read,
never imported/executed. Writes only the sibling REVIEW_*_checks.json.
"""

import ast
import csv
import hashlib
import json
import math
import struct
import tarfile
from fractions import Fraction
from pathlib import Path, PurePosixPath

HERE = Path(__file__).resolve().parent
RUN = "formal-seed0-plan-20261110-153000"
RECEIVED = HERE / RUN
ROOT = RECEIVED / RUN
ARCHIVE = RECEIVED / (RUN + "-light.tar.gz")
OLD = HERE.parent / "road_clear_to_fog/formal-seed0-20261108-resume01"
SEVERITY = HERE.parent / "road_fog_severity/eval-final-seed0-20261109-182100/eval-final-seed0-20261109-182100-complete-20261110"
MODELS = ("source", "ft", "gsmf", "lwf", "gsmf_teacher_bn")
NEW = MODELS[-2:]
CONDITIONS = {"clear": "0", "fog005": "0.005", "fog010": "0.01", "fog020": "0.02", "acdc": None}
CHECKS = []


def js(path):
    return json.loads(path.read_text(encoding="utf-8"))


def rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def check(name, condition):
    CHECKS.append({"name": name, "passed": bool(condition)})


def close(a, b, tolerance=1e-9):
    return math.isclose(float(a), float(b), rel_tol=0, abs_tol=tolerance)


def static_value(node):
    """Closed evaluator for resolved config literals and dict(...) only."""
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, (ast.List, ast.Tuple)):
        result = [static_value(v) for v in node.elts]
        return tuple(result) if isinstance(node, ast.Tuple) else result
    if isinstance(node, ast.Dict):
        return {static_value(k): static_value(v) for k, v in zip(node.keys, node.values)}
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        value = static_value(node.operand)
        return -value if isinstance(node.op, ast.USub) else value
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "dict" and not node.args:
        if any(k.arg is None for k in node.keywords):
            raise ValueError("Config expansion is not allowed")
        return {k.arg: static_value(k.value) for k in node.keywords}
    raise ValueError("Unsupported config syntax: " + ast.dump(node))


def config(path):
    result = {}
    for statement in ast.parse(path.read_text(encoding="utf-8")).body:
        if not isinstance(statement, ast.Assign) or len(statement.targets) != 1 or not isinstance(statement.targets[0], ast.Name):
            raise ValueError("Nonliteral resolved config statement")
        result[statement.targets[0].id] = static_value(statement.value)
    return result


def calculate(matrix):
    gt = [sum(row) for row in matrix]
    pred = [sum(row[i] for row in matrix) for i in range(19)]
    inter = [matrix[i][i] for i in range(19)]
    union = [gt[i] + pred[i] - inter[i] for i in range(19)]
    exact = [Fraction(inter[i] * 100, union[i]) if union[i] else None for i in range(19)]
    valid = [value for value in exact if value is not None]
    return gt, pred, inter, union, [float(v) if v is not None else None for v in exact], float(sum(valid) / len(valid))


def main():
    external = js(RECEIVED / "handoff-verification.json")
    check("archive_sha256", sha(ARCHIVE) == ARCHIVE.with_suffix(".gz.sha256").read_text().split()[0] == external["archive_sha256"])
    with tarfile.open(ARCHIVE, "r:gz") as archive:
        members = archive.getmembers()
        check("archive_paths_types", all(not PurePosixPath(m.name).is_absolute()
              and ".." not in PurePosixPath(m.name).parts and (m.isfile() or m.isdir())
              and PurePosixPath(m.name).parts[0] == RUN for m in members))
        files = [m for m in members if m.isfile()]
        check("extracted_bytes_equal_archive", all(sha(RECEIVED / m.name) == hashlib.sha256(archive.extractfile(m).read()).hexdigest() for m in files))
    manifest = {}
    for line in (ROOT / "MANIFEST.sha256").read_text().splitlines():
        digest, name = line.split("  ", 1)
        manifest[PurePosixPath(name).as_posix().removeprefix("./")] = digest
        check("manifest:" + name, sha(ROOT / name) == digest)
    check("manifest_exact_coverage", set(manifest) == {f.relative_to(ROOT).as_posix() for f in ROOT.rglob("*") if f.is_file()} - {"MANIFEST.sha256"})
    check("manifest_external_count", len(manifest) == external["manifest_files"])

    provenance = js(ROOT / "provenance.json")
    ready = js(ROOT / "preparation/READY.json")
    check("ready_binding", sha(ROOT / "preparation/READY.json") == provenance["ready_sha256"])
    check("authorization_binding", js(ROOT / "authorization.json") == provenance["authorization"]
          and provenance["authorization"]["prompt_two_confirmed"] is True
          and provenance["authorization"]["ready_sha256"] == provenance["ready_sha256"])
    code = provenance["code"]
    check("code_fingerprint", code == ready["code"] and code["sha256"] == hashlib.sha256(json.dumps(code["files"], sort_keys=True).encode()).hexdigest())
    with tarfile.open(ROOT / "source/validated-training-source.tar.gz") as archive:
        source = {m.name: archive.extractfile(m).read() for m in archive.getmembers() if m.isfile()}
        check("training_source_exact_fingerprint", set(source) == set(code["files"]))
        for name, data in source.items():
            check("source_sha:" + name, hashlib.sha256(data).hexdigest() == code["files"][name])
    with tarfile.open(ROOT / "preparation/validated-source.tar.gz") as archive:
        prep_source = {m.name: archive.extractfile(m).read() for m in archive.getmembers() if m.isfile()}
        check("prepared_and_training_code_equal", all(prep_source.get(name) == data for name, data in source.items()))
    prior_hashes = dict((name, digest) for digest, name in (line.split("  ", 1) for line in (SEVERITY / "evidence/code-sha256.txt").read_text().splitlines()))
    unchanged_model_files = [name for name in source if name.startswith("mmseg/") and name in prior_hashes]
    check("upstream_model_loss_files_unchanged", all(hashlib.sha256(source[name]).hexdigest() == prior_hashes[name] for name in unchanged_model_files))
    check("bridge_snapshot_hash", sha(ROOT / "source/gsmf_rs_dil/__init__.py") == prior_hashes["gsmf_rs_dil/__init__.py"])

    old_manifests = {}
    for name in ("A_train", "A_val", "B_train", "B_val"):
        path = ROOT / "data-index/original-road-manifests" / (name + ".jsonl")
        old_manifests[name] = jsonl(path)
        check("historical_data_manifest:" + name, sha(path) == sha(OLD / "data" / (name + ".jsonl")))
    scenes = js(ROOT / "data-index/paired-scene-ids.json")
    check("scene_and_sample_identity", scenes == js(SEVERITY / "prepared-20261110/scene_ids.json")
          and js(ROOT / "data-index/fixed-sample-ids.json") == js(SEVERITY / "prepared-20261110/sample_ids.json"))
    for condition, beta in CONDITIONS.items():
        if beta is None:
            continue
        path = ROOT / "data-index/evaluation-manifests/full" / beta / "A_val.jsonl"
        check("paired_eval_manifest:" + condition, sha(path) == sha(SEVERITY / "prepared-20261110/full" / beta / "A_val_debug.jsonl")
              and [r["id"] for r in jsonl(path)] == sorted(scenes))
    gt_by_condition = {}
    for condition in CONDITIONS:
        records = old_manifests["B_val" if condition == "acdc" else "A_val"]
        gt_by_condition[condition] = [sum(r["label_histogram"].get(str(i), 0) for r in records) for i in range(19)]

    training = js(ROOT / "results/training-check.json")["models"]
    conversion = js(ROOT / "preparation/conversion/conversion.json")
    old_conversion = js(OLD / "runs/formal-seed0-20261108-resume01/conversion/conversion.json")
    old_keys = {r["target"]: (r["source"], r["shape"], r["sha256"]) for r in old_conversion["stages"]["gsmf"]["keys"]}
    check("shared_source_initialization", conversion["source_sha256"] == "a66c958ee774d27566b901ad6570c0a3b83263e9d74389e1c2e025c6c2673d93")
    configs = {}
    for model in NEW:
        current = config(ROOT / "training" / model / "resolved.py")
        configs[model] = current
        prepared = config(ROOT / "preparation" / (model + "-formal-resolved.py"))
        ignored = {"work_dir", "load_from", "resume"}
        check("actual_config_matches_prepared:" + model, {k: v for k, v in current.items() if k not in ignored} == {k: v for k, v in prepared.items() if k not in ignored})
        inv = js(ROOT / "training" / model / "invocation.json")
        converted = conversion["stages"][model]
        check("converted_tensor_provenance:" + model, {r["target"]: (r["source"], r["shape"], r["sha256"]) for r in converted["keys"]} == old_keys
              and converted["exact_value_copy_verified"] and not any(converted[k] for k in ("missing_keys", "unexpected_keys", "shape_mismatches")))
        check("invocation_initialization_seed:" + model, inv["initialization_sha256"] == converted["sha256"] == training[model]["initialization_sha256"]
              and inv["seed"] == current["randomness"]["seed"] == 0 and inv["optimizer"] == "fresh"
              and inv["debug"] is False and inv["synthetic_fixture"] is False
              and Path(current["train_dataloader"]["dataset"]["ann_file"]).name == "B_train.jsonl")
        check("formal_budget:" + model, current["train_cfg"]["max_iters"] == current["param_scheduler"][0]["end"] == 4000
              and current["train_dataloader"]["batch_size"] == 2 and current["model"]["data_preprocessor"]["size"] == (512, 512)
              and current["optim_wrapper"]["optimizer"]["lr"] == 1e-5 and not current["resume"])
        audit = js(ROOT / "training" / model / "audit-end-4000.json")
        check("finite_training_and_completed_steps:" + model, len(audit["losses"]) == len(audit["step_seconds"]) == 4000
              and all(math.isfinite(x) for x in audit["losses"]) and audit["finite_first_step_gradients"]
              and audit["finite_all_checked_gradients"] and training[model]["iterations"] == 4000
              and training[model]["optimizer_saved"] and training[model]["scheduler_saved"]
              and training[model]["optimizer_active_parameter_steps_all_4000"]
              and (ROOT / "execution" / ("train-" + model + ".exit")).read_text().strip() == "0")
        groups = audit["groups"]
        check("teacher_frozen_and_student_update:" + model, training[model]["teacher_state_tensors_exact_source"] == 698
              and all(groups[k]["changed_parameters"] == groups[k]["gradient_tensors_first_step"] == groups[k]["changed_bn_buffers"] == 0 for k in ("backbone", "decode_head"))
              and all(groups[k]["changed_parameters"] > 0 for k in ("backbone_1", "decode_head_1")))
        expected_frozen = model == "gsmf_teacher_bn"
        check("student_shallow_policy:" + model, all((groups[k]["changed_parameters"] == 0 if expected_frozen else groups[k]["changed_parameters"] > 0)
              and groups[k]["changed_bn_buffers"] > 0 for k in ("backbone_1.stem", "backbone_1.layer1")))
    shared_fields = ("train_dataloader", "val_dataloader", "optim_wrapper", "param_scheduler", "train_cfg", "randomness", "env_cfg")
    old_cfg = config(OLD / "runs/formal-seed0-20261108-resume01/gsmf/resolved.py")
    check("common_training_recipe_matches_old_gsmf", all(configs[m][k] == old_cfg[k] for m in NEW for k in shared_fields))
    old_model = config(ROOT / "preparation/gsmf-formal-resolved.py")["model"]
    variant = dict(configs["gsmf_teacher_bn"]["model"])
    variant.pop("teacher_policy")
    variant["type"] = "DIL_EncoderDecoder"
    check("BN_model_config_only_policy_and_class_differ", variant == old_model)
    check("lwf_only_ce_output_kd", configs["lwf"]["model"]["DIL_type"] == "LwF" and not configs["lwf"]["model"]["frozen_backbone_1"]
          and configs["lwf"]["model"]["teacher_policy"] == "fixed_eval"
          and [x["loss_name"] for x in configs["lwf"]["model"]["decode_head_1"]["loss_decode"]] == ["loss_ce", "loss_dilhin"])
    controlled = js(ROOT / "preparation/controlled-real-check.json")
    check("controlled_real_evidence", all(controlled[k] is True for k in ("initial_values_equal", "trainable_sets_equal", "training_flags_differ_only_teacher_BN", "FT_LwF_initial_student_logits_bit_equal")))

    summary_rows = js(ROOT / "results/five-model-summary.json")
    summary = {(r["model"], r["condition"]): r for r in summary_rows}
    wide = rows(ROOT / "results/class-iou-wide.csv")
    long_rows = rows(ROOT / "results/class-iou-long.csv")
    long = {(r["model"], r["condition"], int(r["trainId"])): r for r in long_rows}
    hist = js(ROOT / "results/gt-histograms.json")
    check("table_coverage", len(summary_rows) == len(summary) == 25 and len(wide) == 19 and len(long_rows) == len(long) == 475)
    means, values_by_cell = {}, {}
    for model in MODELS:
        for condition, beta in CONDITIONS.items():
            key = model, condition
            label = model + "/" + condition
            data = js(ROOT / "results/matrices" / (model + "_" + condition + ".json"))
            matrix = data["matrix"]
            check("matrix_counts:" + label, len(matrix) == 19 and all(len(r) == 19 and all(type(v) is int and v >= 0 for v in r) for r in matrix))
            gt, pred, inter, union, values, mean = calculate(matrix)
            means[key], values_by_cell[key] = mean, values
            check("matrix_gt_and_arithmetic:" + label, gt == gt_by_condition[condition] == hist[condition]["gt_histogram"] == data["gt_histogram"]
                  and pred == data["prediction_histogram"] and inter == data["intersection"] and union == data["union"]
                  and sum(gt) == data["valid_pixels"] == hist[condition]["valid_pixels"]
                  and all(close(a, b) for a, b in zip(values, data["iou_percent"]))
                  and close(mean, data["mIoU_percent"]) and close(mean, summary[key]["mIoU_percent"]))
            check("per_class_tables:" + label, all(close(values[i], wide[i][model + "_" + condition])
                  and close(values[i], long[model, condition, i]["IoU_percent"])
                  and [int(long[model, condition, i][k]) for k in ("GT_pixels", "predicted_pixels", "intersection", "union")] == [gt[i], pred[i], inter[i], union[i]] for i in range(19)))
            matrix_csv = rows(ROOT / "results/matrices" / (model + "_" + condition + ".csv"))
            classes = [r["classname"] for r in wide]
            check("matrix_csv:" + label, [[int(r[c]) for c in classes] for r in matrix_csv] == matrix)
            if model not in NEW:
                prior_path = (OLD / "runs/formal-seed0-20261108-resume01" / ("eval_" + model + "_B") / "independent-metrics.json"
                              if condition == "acdc" else SEVERITY / "cells/full" / model / beta / "independent-metrics.json")
                check("reused_matrix_exact:" + label, matrix == js(prior_path)["confusion_matrix"] and data["origin"] == "reused_verified_previous_run")
            else:
                directory = "eval-" + model + "-" + ("acdc" if condition == "acdc" else "beta" + beta)
                cell = ROOT / "evaluation" / directory
                ev = js(cell / "evaluation.json")
                met = js(cell / "independent-metrics.json")
                again = js(cell / "reloaded-prediction-metrics.json")
                check("new_matrix_original_and_reread:" + label, met["confusion_matrix"] == again["confusion_matrix"] == matrix
                      and close(mean, met["mIoU"]) and close(mean, again["mIoU"]) and data["origin"] == "new_inference_this_run")
                check("new_eval_checkpoint_state_count_branch:" + label, ev["checkpoint_sha256"] == training[model]["checkpoint_sha256"] == data["checkpoint_sha256"]
                      and ev["evaluated_images"] == (100 if condition == "acdc" else 500) == data["images"]
                      and ev["checkpoint_training_iterations"] == 4000 and ev["state_unchanged"] is True
                      and ev["full_official_split"] is True and not ev["debug"] and not ev["synthetic_fixture"]
                      and ev["forward_calls"]["backbone"] == ev["forward_calls"]["decode_head.conv_seg"] == 0
                      and ev["forward_calls"]["backbone_1"] == ev["forward_calls"]["decode_head_1.conv_seg"] == data["images"] * 18
                      and (ROOT / "execution" / (directory + ".exit")).read_text().strip() == "0")
                predictions = js(ROOT / "results/verification" / (model + "_" + condition + "_predictions.json"))
                check("full_prediction_index_count:" + label, len(predictions) == len({r["id"] for r in predictions}) == data["images"])
    for r in rows(ROOT / "results/five-model-summary.csv"):
        key = r["model"], r["condition"]
        expected_drop = means[key[0], "clear"] - means[key] if key[1] != "acdc" else None
        check("summary_derived_values:" + "/".join(key), close(r["mIoU_percent"], means[key])
              and close(r["delta_vs_source_same_condition_pp"], means[key] - means["source", key[1]])
              and (expected_drop is None or close(r["drop_vs_own_clear_pp"], expected_drop)))
    sample_index = js(ROOT / "results/fixed-samples/prediction-index.json")
    samples = js(ROOT / "data-index/fixed-sample-ids.json")["ids"]
    check("fixed_sample_coverage", len(sample_index) == 48 and {(r["scene"], r["model"], r["condition"]) for r in sample_index} == {(s, m, c) for s in samples for m in NEW for c in CONDITIONS if c != "acdc"})
    for row in sample_index:
        label = "/".join(row[k] for k in ("scene", "model", "condition"))
        path = ROOT / "results/fixed-samples/raw-predictions" / row["scene"] / row["model"] / (row["condition"] + ".png")
        predictions = js(ROOT / "results/verification" / (row["model"] + "_" + row["condition"] + "_predictions.json"))
        original = next(r for r in predictions if r["id"] == row["scene"])
        head = path.read_bytes()[:24]
        check("sample_png_and_index:" + label, sha(path) == row["sha256"] == original["sha256"]
              and head[:8] == b"\x89PNG\r\n\x1a\n" and struct.unpack(">II", head[16:24]) == (2048, 1024))
    check("formal_pipeline_exit", (ROOT / "exit-code.txt").read_text().strip() == "0")
    contrasts = {m: {c: {"vs_gsmf_pp": means[m, c] - means["gsmf", c], "vs_ft_pp": means[m, c] - means["ft", c],
                        "classes_better_than_gsmf": sum(a > b for a, b in zip(values_by_cell[m, c], values_by_cell["gsmf", c]))}
                     for c in CONDITIONS} for m in NEW}
    output = {"verification_status": "ANALYZED", "date": "2026-11-10", "scope": "offline artifact/source/config/matrix consistency; no model rerun or remote data access",
              "status": "PASS" if all(c["passed"] for c in CHECKS) else "FAIL", "checks_passed": sum(c["passed"] for c in CHECKS), "checks_total": len(CHECKS),
              "archive_sha256": sha(ARCHIVE), "archive_files": len(files), "manifest_files": len(manifest), "training_source_files": len(source),
              "unchanged_upstream_model_files": len(unchanged_model_files), "new_cells": 10, "reused_cells": 15, "contrasts": contrasts,
              "results": [{"model": m, "condition": c, "mIoU_percent": means[m, c]} for m in MODELS for c in CONDITIONS],
              "limits": ["single seed; no seed 1/2 repeats", "weights/raw data/full predictions remain remote", "training state claims are archived evidence, not local tensor recomputation", "cross-method RNG consumption not fully isolated", "LwF T2/0.5 all-logit-pixel KD without T-squared; no parameter search"], "checks": CHECKS}
    (HERE / ("REVIEW_" + RUN + "_checks.json")).write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: output[k] for k in ("status", "checks_passed", "checks_total", "archive_files", "manifest_files", "training_source_files", "unchanged_upstream_model_files", "contrasts")}, ensure_ascii=False, indent=2))
    for failed in (c for c in CHECKS if not c["passed"]):
        print("FAILED", failed["name"])
    raise SystemExit(0 if output["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
