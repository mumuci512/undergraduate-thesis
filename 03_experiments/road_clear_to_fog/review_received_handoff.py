"""Read-only checks of a received road-DIL handoff; no model or dataset execution."""

import argparse
import ast
import csv
import hashlib
import json
import math
import pathlib
import re


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def literal(node):
    """Read resolved MMEngine configuration literals without executing Python."""
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, (ast.List, ast.Tuple)):
        return [literal(item) for item in node.elts]
    if isinstance(node, ast.Dict):
        return {literal(k): literal(v) for k, v in zip(node.keys, node.values)}
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -literal(node.operand)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        if node.func.id == "dict" and not node.args:
            if any(item.arg is None for item in node.keywords):
                raise ValueError("Configuration contains dict unpacking")
            return {item.arg: literal(item.value) for item in node.keywords}
    raise ValueError("Nonliteral configuration: " + ast.dump(node)[:180])


def read_config(path):
    required = {"model", "train_dataloader", "optim_wrapper", "param_scheduler",
                "train_cfg", "randomness"}
    result = {}
    for node in ast.parse(path.read_text(encoding="utf-8-sig")).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id in required:
                result[target.id] = literal(node.value)
    return result


def review(root):
    checks, details = [], {}

    def check(name, condition, evidence=None):
        checks.append({"name": name, "pass": bool(condition), "evidence": evidence})

    archive = root / (root.name + "_20261108-174551.tar.gz")
    expected_archive = pathlib.Path(str(archive) + ".sha256").read_text().split()[0]
    check("archive_sha256", sha256(archive) == expected_archive, expected_archive)
    manifest = {}
    for line in (root / "MANIFEST.sha256").read_text(encoding="utf-8-sig").splitlines():
        match = re.fullmatch(r"([0-9a-fA-F]{64})\s+[ *]?(.+)", line)
        if not match:
            raise ValueError("Invalid manifest line")
        rel = match.group(2).removeprefix("./")
        target = (root / rel).resolve()
        if root not in target.parents or rel in manifest:
            raise ValueError("Unsafe or duplicate manifest entry: " + rel)
        manifest[rel] = match.group(1).lower()
    bad = [rel for rel, expected in manifest.items()
           if not (root / rel).is_file() or sha256(root / rel) != expected]
    check("manifest_file_hashes", not bad, {"entries": len(manifest), "mismatches": bad})

    data = {}
    audit = read_json(root / "data/audit.json")
    for group, expected in {"A_train": 2975, "A_val": 500,
                            "B_train": 400, "B_val": 100}.items():
        path = root / "data" / (group + ".jsonl")
        data[group] = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        check(group + "_count", len(data[group]) == expected, len(data[group]))
        check(group + "_recorded_hash", sha256(path) == audit["manifest_sha256"][path.name])
        check(group + "_label_values", all(
            set(map(int, row["label_histogram"])) <= set(range(19)) | {255}
            for row in data[group]))
        check(group + "_pixel_totals", all(
            sum(row["label_histogram"].values()) == math.prod(row["shape"])
            for row in data[group]))
    overlaps = {}
    for domain in "AB":
        train, val = data[domain + "_train"], data[domain + "_val"]
        for key in ["image_sha256", "rgb_pixels_sha256"]:
            shared = set(row[key] for row in train) & set(row[key] for row in val)
            check(domain + "_no_train_val_" + key + "_overlap", not shared, len(shared))
        overlaps[domain] = sorted(set(row["sequence"] for row in train) &
                                  set(row["sequence"] for row in val))
    check("A_sequence_disjoint", not overlaps["A"], overlaps["A"])
    declared = read_json(root / "data/split-review.json")["accepted_shared_sequences"]
    check("B_recording_overlap_matches_declared", overlaps["B"] == sorted(declared), overlaps["B"])
    details["data_counts"] = {name: len(rows) for name, rows in data.items()}
    details["sequence_overlaps"] = overlaps

    run = root / "runs" / root.name
    final = read_json(run / "final-independent-verification.json")
    summary_rows = list(csv.DictReader((root / "results/results_summary.csv").open(encoding="utf-8-sig")))
    summary = {row["model"]: row for row in summary_rows}
    classes = list(final["metrics"]["source"]["A"]["IoU"])
    per_class = list(csv.DictReader((root / "results/per_class_IoU.csv").open(encoding="utf-8-sig")))
    check("nineteen_consistent_class_names", len(classes) == 19 and
          [row["class"] for row in per_class] == classes)
    recomputed = {}
    for model in ["source", "ft", "gsmf"]:
        recomputed[model] = {}
        for domain in "AB":
            rows = list(csv.DictReader((root / "results" / ("confusion_" + model + "_" + domain + ".csv")).open(encoding="utf-8-sig")))
            matrix = [[int(row[name]) for name in classes] for row in rows]
            check(model + "_" + domain + "_matrix_structure", len(matrix) == 19 and
                  [int(row["GT_trainId"]) for row in rows] == list(range(19)) and
                  [row["GT_class"] for row in rows] == classes and
                  all(value >= 0 for row in matrix for value in row))
            gt_support = [sum(row) for row in matrix]
            expected_support = [sum(row["label_histogram"].get(str(i), 0)
                                    for row in data[domain + "_val"]) for i in range(19)]
            check(model + "_" + domain + "_GT_histogram", gt_support == expected_support)
            pred_support = [sum(row[i] for row in matrix) for i in range(19)]
            ious = [100.0 * matrix[i][i] / (gt_support[i] + pred_support[i] - matrix[i][i])
                    if gt_support[i] + pred_support[i] - matrix[i][i] else None for i in range(19)]
            miou = sum(value for value in ious if value is not None) / sum(value is not None for value in ious)
            check(model + "_" + domain + "_final_JSON_matrix", matrix == final["metrics"][model][domain]["confusion_matrix"])
            check(model + "_" + domain + "_final_JSON_metric", abs(miou - final["metrics"][model][domain]["mIoU"]) < 1e-9)
            column = "A_Cityscapes_val_mIoU_percent" if domain == "A" else "B_ACDC_fog_val_mIoU_percent"
            check(model + "_" + domain + "_summary_csv", abs(miou - float(summary[model][column])) < 1e-9)
            check(model + "_" + domain + "_per_class_csv", all(
                (value is None and per_class[i][model + "_" + domain] in ["", "null"]) or
                (value is not None and abs(value - float(per_class[i][model + "_" + domain])) < 1e-9)
                for i, value in enumerate(ious)))
            evaluation = read_json(run / ("eval_" + model + "_" + domain) / "evaluation.json")
            check(model + "_" + domain + "_evaluation_metadata",
                  evaluation["checkpoint_sha256"] == final["models"][model]["checkpoint_sha256"] and
                  evaluation["evaluated_images"] == len(data[domain + "_val"]) and
                  evaluation["state_unchanged"] is True and
                  abs(evaluation["metrics"]["mIoU"] - miou) <= 0.005001)
            if model == "gsmf":
                forward = evaluation["forward_calls"]
                check("gsmf_" + domain + "_incremental_branch_only",
                      forward["backbone"] == 0 and forward["decode_head.conv_seg"] == 0 and
                      forward["backbone_1"] > 0 and forward["decode_head_1.conv_seg"] > 0)
            recomputed[model][domain] = miou
        for field, value in {
            "old_domain_drop_pp": recomputed["source"]["A"] - recomputed[model]["A"],
            "new_domain_gain_pp": recomputed[model]["B"] - recomputed["source"]["B"],
            "equal_domain_mean_percent": sum(recomputed[model].values()) / 2,
        }.items():
            check(model + "_" + field, abs(value - float(summary[model][field])) < 1e-9)
    details["recomputed_mIoU_percent"] = recomputed
    details["gsmf_minus_ft_pp"] = {domain: recomputed["gsmf"][domain] - recomputed["ft"][domain] for domain in "AB"}

    configs = {model: read_config(run / model / "resolved.py") for model in ["ft", "gsmf"]}
    for field in ["train_dataloader", "optim_wrapper", "param_scheduler", "train_cfg", "randomness"]:
        check("FT_GSMF_matching_" + field, configs["ft"][field] == configs["gsmf"][field])
    for field in ["data_preprocessor", "test_cfg"]:
        check("FT_GSMF_matching_model_" + field, configs["ft"]["model"][field] == configs["gsmf"]["model"][field])
    details["shared_B_configuration"] = {field: configs["ft"][field] for field in
        ["optim_wrapper", "param_scheduler", "train_cfg", "randomness"]}
    details["shared_B_configuration"]["batch_size"] = configs["ft"]["train_dataloader"]["batch_size"]
    details["shared_B_configuration"]["crop"] = configs["ft"]["model"]["data_preprocessor"]["size"]
    conversion = read_json(run / "conversion/conversion.json")
    check("conversion_shared_source_checkpoint", conversion["source_sha256"] == final["models"]["source"]["checkpoint_sha256"])
    for model in ["ft", "gsmf"]:
        invocation = read_json(run / model / "invocation.json")
        stage = conversion["stages"][model]
        check(model + "_conversion_and_initialization", invocation["initialization_sha256"] == stage["sha256"] and
              stage["exact_value_copy_verified"] and not stage["missing_keys"] and
              not stage["unexpected_keys"] and not stage["shape_mismatches"] and invocation["optimizer"] == "fresh")
    snapshots = read_json(root / "version/training-snapshots.json")
    check("source_initial_and_recovery_code_hashes", snapshots[0]["members"] == snapshots[1]["members"], len(snapshots[0]["members"]))
    git_files = {row["repository_path"]: row for row in read_json(root / "GIT_FILES.json")}
    check("snapshot_hashes_crossmatch_Git_index", all(
        name in git_files and git_files[name]["sha256"] == value for name, value in snapshots[0]["members"].items()))
    status = read_json(run / "status.json")
    check("pipeline_completion_record", status["state"] == "complete" and status["exit_code"] == 0)
    audit_gsmf = read_json(run / "gsmf/audit-end-4000.json")
    details["GSMF_parameter_and_BN_audit"] = audit_gsmf["groups"]
    for name in ["backbone", "decode_head", "backbone_1.stem", "backbone_1.layer1"]:
        group = audit_gsmf["groups"][name]
        check("frozen_parameter_record_" + name, group["changed_parameters"] == 0 and
              group["trainable_elements"] == 0 and group["gradient_tensors_first_step"] == 0)
    return {"status": "PASS" if all(item["pass"] for item in checks) else "FAIL",
            "scope": "archive/file integrity and offline artifact consistency; no model, raw image/label, checkpoint or remote Git re-execution",
            "checks": checks, "details": details}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()
    result = review(args.root.resolve())
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "checks": len(result["checks"]),
                      "failures": [item for item in result["checks"] if not item["pass"]],
                      "metrics": result["details"]["recomputed_mIoU_percent"]}, ensure_ascii=True, indent=2))
    raise SystemExit(0 if result["status"] == "PASS" else 1)
