"""Audit the received fog-severity archive offline, using Python's standard library.

Run from any directory: python -X utf8 path/to/review_received_eval.py
Reads the extracted package and prior road handoff; writes only the sibling checks
JSON. Does not execute archived scripts, load models, or access remote data.
"""

import csv
import hashlib
import json
import math
import random
import struct
import tarfile
from fractions import Fraction
from pathlib import Path, PurePosixPath


HERE = Path(__file__).resolve().parent
RUN = "eval-final-seed0-20261109-182100"
PACKAGE = RUN + "-complete-20261110"
ARCHIVE = HERE / RUN / (PACKAGE + ".tar.gz")
ROOT = HERE / RUN / PACKAGE
OLD = HERE.parent / "road_clear_to_fog" / "formal-seed0-20261108-resume01"
MODELS = ("source", "ft", "gsmf")
BETAS = ("0", "0.005", "0.01", "0.02")
CHECKS = []


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def check(name, condition):
    CHECKS.append({"name": name, "passed": bool(condition)})


def close(a, b, tolerance=1e-9):
    return math.isclose(float(a), float(b), rel_tol=0, abs_tol=tolerance)


def read_csv(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def metrics(matrix):
    gt = [sum(row) for row in matrix]
    pred = [sum(row[j] for row in matrix) for j in range(19)]
    union = [gt[i] + pred[i] - matrix[i][i] for i in range(19)]
    values = [Fraction(matrix[i][i] * 100, union[i]) if union[i] else None
              for i in range(19)]
    included = [v for v in values if v is not None]
    return gt, pred, union, [None if v is None else float(v) for v in values], float(sum(included) / len(included))


def main():
    check("external_archive_sha256", sha(ARCHIVE) == ARCHIVE.with_suffix(".gz.sha256").read_text().split()[0])
    with tarfile.open(ARCHIVE, "r:gz") as archive:
        members = archive.getmembers()
        check("archive_paths_and_types", all(
            not PurePosixPath(m.name).is_absolute()
            and ".." not in PurePosixPath(m.name).parts
            and (m.isfile() or m.isdir())
            and PurePosixPath(m.name).parts[0] == PACKAGE for m in members))
        files = [m for m in members if m.isfile()]
        check("extracted_files_equal_archive", all(
            (ROOT.parent / m.name).is_file()
            and sha(ROOT.parent / m.name) == hashlib.sha256(archive.extractfile(m).read()).hexdigest()
            for m in files))

    manifest = {}
    for line in (ROOT / "MANIFEST.sha256").read_text().splitlines():
        expected, name = line.split("  ", 1)
        check("manifest_sha256:" + name, sha(ROOT / name) == expected)
        manifest[PurePosixPath(name).as_posix().removeprefix("./")] = expected
    check("manifest_coverage", set(manifest) == {
        f.relative_to(ROOT).as_posix() for f in ROOT.rglob("*") if f.is_file()
    } - {"MANIFEST.sha256"})

    audit = read_json(ROOT / "data-audit-20261110/audit.json")
    rows = read_csv(ROOT / "data-audit-20261110/available_manifest.csv")
    scenes = read_json(ROOT / "prepared-20261110/scene_ids.json")
    records = {(r["base_scene_id"], r["beta"]): r for r in rows}
    check("matched_500_scenes_2000_inputs", len(rows) == len(records) == 2000
          and len(scenes) == len(set(scenes)) == 500
          and sorted(scenes) == sorted(audit["common_scene_ids"])
          and set(records) == {(s, b) for s in scenes for b in BETAS})
    check("audit_no_reported_errors_or_overlap", not any(audit[k] for k in (
        "errors", "source_id_or_acdc_file_hash_overlap", "acdc_decoded_rgb_hash_overlap", "source_sequence_overlap")))
    check("four_conditions_share_gt_and_dimensions", all(
        len({records[s, b]["gt_sha256"] for b in BETAS}) == 1
        and len({records[s, b]["gt"] for b in BETAS}) == 1
        and all((records[s, b]["width"], records[s, b]["height"], records[s, b]["gt_encoding"])
                == ("2048", "1024", "labelIds") for b in BETAS) for s in scenes))

    old_val = jsonl(OLD / "data/A_val.jsonl")
    old_train = jsonl(OLD / "data/A_train.jsonl")
    old_fog = jsonl(OLD / "data/B_train.jsonl")
    val_by_scene = {Path(r["image"]).name.removesuffix("_leftImg8bit.png"): r for r in old_val}
    check("clear_inputs_and_gt_match_prior_val_hashes", set(val_by_scene) == set(scenes) and all(
        records[s, "0"]["image_sha256"] == val_by_scene[s]["image_sha256"]
        and all(records[s, b]["gt_sha256"] == val_by_scene[s]["label_sha256"] for b in BETAS)
        for s in scenes))
    check("source_train_scene_sequence_disjoint", not set(scenes).intersection(
        Path(r["image"]).name.removesuffix("_leftImg8bit.png") for r in old_train)
        and not {s.rsplit("_", 1)[0] for s in scenes}.intersection(r["sequence"] for r in old_train))
    check("all_condition_file_hashes_disjoint_from_train", not {r["image_sha256"] for r in rows}.intersection(
        r["image_sha256"] for r in old_train + old_fog))
    gt_hist = [sum(r["label_histogram"].get(str(i), 0) for r in old_val) for i in range(19)]

    sample_info = read_json(ROOT / "prepared-20261110/sample_ids.json")
    samples = sample_info["ids"]
    check("sample_selection_replays", samples == sorted(random.Random(sample_info["seed"]).sample(sorted(scenes), 6)))
    fp = read_json(ROOT / "fingerprint.json")
    snap = fp["snapshot"]
    check("fingerprint_signature", fp["signature"] == hashlib.sha256(json.dumps(snap, sort_keys=True).encode()).hexdigest())
    bound_files = {
        "code_manifest_sha256": "evidence/code-sha256.txt",
        "data_manifest_sha256": "data-audit-20261110/available_manifest.csv",
        "audit_sha256": "data-audit-20261110/audit.json",
        "scenes_sha256": "prepared-20261110/scene_ids.json",
        "samples_sha256": "prepared-20261110/sample_ids.json",
    }
    check("fingerprint_local_bindings", all(sha(ROOT / name) == snap[key] for key, name in bound_files.items())
          and all(sha(ROOT / "scripts" / name) == expected for name, expected in snap["scripts"].items())
          and all(sha(ROOT / "prepared-20261110" / name) == expected for name, expected in snap["prepared_manifests"].items()))
    snapshots = read_json(OLD / "version/training-snapshots.json")
    code_hashes = dict((name, digest) for digest, name in (
        line.split("  ", 1) for line in (ROOT / "evidence/code-sha256.txt").read_text().splitlines()))
    shared_code = set(code_hashes).intersection(snapshots[-1]["members"])
    check("shared_code_hashes_match_training_snapshot_metadata", all(
        code_hashes[name] == snapshots[-1]["members"][name] for name in shared_code))

    for phase, ids in (("precheck", sorted(scenes)[:2]), ("full", sorted(scenes))):
        for beta in BETAS:
            d = ROOT / "prepared-20261110" / phase / beta
            prepared = jsonl(d / "A_val_debug.jsonl")
            info = read_json(d / "audit.json")
            check(f"prepared:{phase}/{beta}", [r["id"] for r in prepared] == ids
                  and info["actual_n"] == len(ids)
                  and info["manifest_sha256"]["A_val_debug.jsonl"] == sha(d / "A_val_debug.jsonl")
                  and info["source_manifest_sha256"] == snap["data_manifest_sha256"]
                  and all((r["image"], r["label"], r["encoding"]) == (
                      records[r["id"], beta]["image"], records[r["id"], beta]["gt"], "labelIds") for r in prepared))

    index = read_json(ROOT / "prediction-index.json")
    results = read_json(ROOT / "results/results.json")
    result_map = {(r["model"], r["beta"]): r for r in results}
    csv_results = read_csv(ROOT / "results/results.csv")
    wide = read_csv(ROOT / "results/class_iou_wide.csv")
    long = read_csv(ROOT / "results/class_iou_long.csv")
    long_map = {(r["model"], r["beta"], int(r["trainId"])): r for r in long}
    check("summary_table_coverage", len(result_map) == len(results) == len(csv_results) == 12
          and len(wide) == 19 and len(long_map) == len(long) == 228)
    summaries, class_values, historical_diffs = {}, {}, {}
    for phase, n in (("precheck", 2), ("full", 500)):
        expected_gt = gt_hist if phase == "full" else [
            sum(val_by_scene[s]["label_histogram"].get(str(i), 0) for s in sorted(scenes)[:2]) for i in range(19)]
        for model in MODELS:
            for beta in BETAS:
                label = f"{phase}/{model}/{beta}"
                cell = ROOT / "cells" / phase / model / beta
                ev = read_json(cell / "evaluation.json")
                met = read_json(cell / "independent-metrics.json")
                again = read_json(cell / "reloaded-prediction-metrics.json")
                proof = read_json(cell / "cell-proof.json")
                check("cell_proof:" + label, proof["signature"] == fp["signature"]
                      and (proof["phase"], proof["stage"], proof["beta"]) == (phase, model, beta)
                      and len(proof["files"]) == n + 4
                      and all(sha(cell / name) == proof["files"][name] for name in (
                          "evaluation.json", "independent-metrics.json", "reloaded-prediction-metrics.json", "exit-code.txt")))
                check("exit_checkpoint_state_count:" + label, (cell / "exit-code.txt").read_text().strip() == "0"
                      and ev["checkpoint_sha256"] == snap["checkpoints"][model]
                      and ev["state_unchanged"] is True and ev["evaluated_images"] == n
                      and ev["synthetic_fixture"] is False
                      and ev["checkpoint_training_iterations"] == (60000 if model == "source" else 4000))
                calls = ev["forward_calls"]
                check("branch_and_logits:" + label, (
                    calls.get("backbone") == calls.get("decode_head.conv_seg") == 0
                    and calls.get("backbone_1", 0) == calls.get("decode_head_1.conv_seg", 0) == n * 18
                    if model == "gsmf" else calls.get("backbone") == calls.get("decode_head.conv_seg") == n * 18)
                    and met["actual_logit_shapes"] == [[19, 1024, 2048]])
                matrix = met["confusion_matrix"]
                check("matrix_shape_counts_reload:" + label, len(matrix) == 19
                      and all(len(r) == 19 and all(type(v) is int and v >= 0 for v in r) for r in matrix)
                      and matrix == again["confusion_matrix"])
                gt, pred, union, values, mean = metrics(matrix)
                check("matrix_arithmetic_and_prior_gt:" + label, gt == expected_gt
                      and sum(gt) == met["valid_pixels"] == again["valid_pixels"]
                      and close(mean, met["mIoU"]) and close(mean, again["mIoU"])
                      and all(v is None and met["IoU"][name] is None or v is not None and close(v, met["IoU"][name])
                              for name, v in zip(met["IoU"], values)))
                if phase != "full":
                    continue
                summaries[model, beta] = mean
                class_values[model, beta] = values
                export = read_json(ROOT / "results/matrices" / f"{model}_beta_{beta}.json")
                classes = export["classes"]
                check("export_matrix_and_summary:" + label, export["matrix"] == matrix
                      and export["rows"] == "GT" and export["columns"] == "prediction"
                      and export["n_images"] == 500 and export["valid_pixels"] == sum(gt)
                      and close(mean, export["mIoU_percent"])
                      and close(mean, result_map[model, beta]["mIoU_percent"])
                      and result_map[model, beta]["checkpoint_sha256"] == ev["checkpoint_sha256"]
                      and result_map[model, beta]["data_manifest_sha256"] == snap["data_manifest_sha256"]
                      and result_map[model, beta]["n_images"] == 500)
                table = read_csv(ROOT / "results/matrices" / f"{model}_beta_{beta}.csv")
                check("matrix_csv:" + label, [[int(r[name]) for name in classes] for r in table] == matrix)
                check("per_class_tables:" + label, all(
                    close(values[i], wide[i][f"{model}_beta_{beta}"])
                    and close(values[i], long_map[model, beta, i]["iou_percent"])
                    and long_map[model, beta, i]["classname"] == classes[i] == wide[i]["classname"]
                    and [int(long_map[model, beta, i][key]) for key in ("gt_pixels", "pred_pixels", "intersection", "union")]
                    == [gt[i], pred[i], matrix[i][i], union[i]] for i in range(19)))
                expected_preds = {k: v for k, v in proof["files"].items() if k.startswith("predictions/")}
                check("remote_prediction_index:" + label, len(expected_preds) == 500
                      and index[f"{model}/{beta}"]["files"] == expected_preds)
                for scene in samples:
                    png = ROOT / "results/samples" / scene / model / f"beta_{beta}.png"
                    original_name = "predictions/" + Path(records[scene, beta]["image"]).stem + ".png"
                    header = png.read_bytes()[:24]
                    check(f"sample_prediction:{model}/{beta}/{scene}", sha(png) == expected_preds[original_name]
                          and header[:8] == b"\x89PNG\r\n\x1a\n" and struct.unpack(">II", header[16:24]) == (2048, 1024))
                if beta == "0":
                    prior = read_json(OLD / "runs" / "formal-seed0-20261108-resume01" / f"eval_{model}_A" / "independent-metrics.json")
                    historical_diffs[model] = mean - prior["mIoU"]
                    check("historical_clear_agreement:" + model, abs(historical_diffs[model]) < 0.0001)
                    check("historical_clear_matrix_exact:" + model, matrix == prior["confusion_matrix"])
                    old_ev = read_json(OLD / "runs" / "formal-seed0-20261108-resume01" / f"eval_{model}_A" / "evaluation.json")
                    check("checkpoint_matches_prior_eval:" + model, old_ev["checkpoint_sha256"] == ev["checkpoint_sha256"])

    for r in csv_results:
        key = r["model"], r["beta"]
        check("summary_csv:" + "/".join(key), close(r["mIoU_percent"], summaries[key])
              and close(r["drop_vs_clear_pp"], summaries[key[0], "0"] - summaries[key]))
    status = read_json(ROOT / "status.json")
    check("completed_status_24_cells", set(status["completed"]) == {
        f"{phase}/{model}/{beta}" for phase in ("precheck", "full") for model in MODELS for beta in BETAS})
    contrasts = []
    for beta in BETAS:
        contrasts.append({"beta": beta,
            "gsmf_minus_ft_pp": summaries["gsmf", beta] - summaries["ft", beta],
            "gsmf_minus_source_pp": summaries["gsmf", beta] - summaries["source", beta],
            "gsmf_classes_better_than_ft": sum(a > b for a, b in zip(class_values["gsmf", beta], class_values["ft", beta])),
            "gsmf_classes_worse_than_ft": sum(a < b for a, b in zip(class_values["gsmf", beta], class_values["ft", beta]))})
    output = {"verification_status": "ANALYZED", "date": "2026-11-10", "scope": "offline artifact/hash/matrix consistency; no model or remote-data rerun",
        "archive_sha256": sha(ARCHIVE), "archive_file_count": len(files), "manifest_file_count": len(manifest),
        "checks_passed": sum(c["passed"] for c in CHECKS), "checks_total": len(CHECKS),
        "status": "PASS" if all(c["passed"] for c in CHECKS) else "FAIL", "gt_valid_pixels": sum(gt_hist),
        "shared_training_code_metadata_count": len(shared_code), "code_absent_from_training_snapshot_metadata": sorted(set(code_hashes) - shared_code),
        "clear_miou_differences_vs_prior_pp": historical_diffs, "contrasts": contrasts,
        "results": [{"model": m, "beta": b, "mIoU_percent": summaries[m, b]} for m in MODELS for b in BETAS],
        "limits": ["weights, raw RGB/GT and 6000 complete prediction masks remain remote", "training code entries compared as metadata, not downloaded source bytes", "single training seed; no CI or significance test", "ACDC fog intensity support and cross-dataset geography unresolved"], "checks": CHECKS}
    destination = HERE / ("REVIEW_" + RUN + "_checks.json")
    destination.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: output[k] for k in ("status", "checks_passed", "checks_total", "archive_file_count", "manifest_file_count", "shared_training_code_metadata_count", "code_absent_from_training_snapshot_metadata", "clear_miou_differences_vs_prior_pp", "contrasts")}, ensure_ascii=False, indent=2))
    for failed in (c for c in CHECKS if not c["passed"]):
        print("FAILED", failed["name"])
    raise SystemExit(0 if output["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
