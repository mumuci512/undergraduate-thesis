"""Offline audit of the received Rain chain, without executing archived code.

Uses only the standard library. Reads the existing extraction and final remote
receipts; writes a separate REVIEW_*_checks.json beside this script.
"""
import ast
import csv
import hashlib
import json
import math
import tarfile
from fractions import Fraction
from pathlib import Path, PurePosixPath

HERE = Path(__file__).resolve().parent
RUN = "formal-seed0-plan-20261110-180543"
RECEIVED = HERE / RUN
ROOT = RECEIVED / RUN
PRIOR = HERE.parent / "road_lwf_bn/formal-seed0-plan-20261110-153000/formal-seed0-plan-20261110-153000"
OLD_DATA = HERE.parent / "road_clear_to_fog/formal-seed0-20261108-resume01/data"
METHODS = ("ft", "gsmf", "lwf")
CONDITIONS = ("clear", "fog005", "fog010", "fog020", "fog", "rain")
PARENTS = {
    "ft": "99914df527d8506c33178ef6ea1caf7f0ed1d07369858e37275205d60a57d516",
    "gsmf": "fc227c57dc3e47a134ef51b282964654a0210f3c06f00bd0d3e81b706850b24a",
    "lwf": "854d83357a912713a27cf27283b024f3e7fd7dab47043434d312b136ec9b6843",
}
CHECKS = []


def js(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def check(name, condition):
    CHECKS.append({"name": name, "passed": bool(condition)})


def close(a, b):
    return math.isclose(float(a), float(b), rel_tol=0, abs_tol=1e-9)


def jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def literal(node):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, (ast.List, ast.Tuple)):
        return [literal(n) for n in node.elts]
    if isinstance(node, ast.Dict):
        return {literal(k): literal(v) for k, v in zip(node.keys, node.values)}
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        v = literal(node.operand)
        return -v if isinstance(node.op, ast.USub) else v
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "dict" and not node.args:
        assert all(k.arg is not None for k in node.keywords)
        return {k.arg: literal(k.value) for k in node.keywords}
    raise ValueError("Unsupported resolved configuration syntax")


def config(path):
    result = {}
    for n in ast.parse(path.read_text(encoding="utf-8")).body:
        assert isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name)
        result[n.targets[0].id] = literal(n.value)
    return result


def calculate(matrix):
    assert len(matrix) == 19 and all(len(row) == 19 for row in matrix)
    assert all(type(v) is int and v >= 0 for row in matrix for v in row)
    gt = [sum(row) for row in matrix]
    pred = [sum(row[c] for row in matrix) for c in range(19)]
    union = [gt[c] + pred[c] - matrix[c][c] for c in range(19)]
    iou = [Fraction(100 * matrix[c][c], union[c]) if union[c] else None for c in range(19)]
    valid = [v for v in iou if v is not None]
    return gt, pred, union, iou, float(sum(valid) / len(valid))


def main():
    archive = RECEIVED / (RUN + "-light.tar.gz")
    external = js(RECEIVED / "handoff-verification.json")
    completion = js(RECEIVED / "completion.json")
    final_status = js(RECEIVED / "remote-final-status.json")
    check("external_archive_sha", sha(archive) == external["archive_sha256"]
          == completion["handoff"]["archive_sha256"]
          == (RECEIVED / (RUN + "-light.tar.gz.sha256")).read_text().split()[0])
    check("remote_complete", completion["status"] == final_status["state"] == "complete"
          and final_status["exit_code"] == 0
          and sha(RECEIVED / "completion.json") == final_status["completion_sha256"]
          and sha(RECEIVED / "handoff-verification.json") == final_status["handoff_verification_sha256"])
    with tarfile.open(archive) as tar:
        members = tar.getmembers()
        names = [str(PurePosixPath(m.name)).casefold() for m in members]
        check("safe_archive_members", len(names) == len(set(names)) and all(
            PurePosixPath(m.name).parts[0] == RUN and not PurePosixPath(m.name).is_absolute()
            and ".." not in PurePosixPath(m.name).parts and "\\" not in m.name
            and ":" not in m.name and (m.isfile() or m.isdir()) for m in members))
        check("extracted_files_match_archive", all(
            sha(RECEIVED / m.name) == hashlib.sha256(tar.extractfile(m).read()).hexdigest()
            for m in members if m.isfile()))
    files = {p.relative_to(ROOT).as_posix(): p for p in ROOT.rglob("*") if p.is_file()}
    manifest = {}
    for line in (ROOT / "MANIFEST.sha256").read_text().splitlines():
        digest, name = line.split("  ", 1)
        check("sha_manifest:" + name, name not in manifest and sha(ROOT / name) == digest)
        manifest[name] = digest
    payload = js(ROOT / "MANIFEST.json")["files"]
    check("sha_manifest_exact_coverage", set(manifest) == set(files) - {"MANIFEST.sha256"})
    check("json_manifest_exact_coverage", set(payload) == set(files) - {"MANIFEST.sha256", "MANIFEST.json"}
          and len(payload) == external["payload_files"] == 671)
    check("json_manifest_hashes_and_sizes", all(sha(ROOT / n) == v["sha256"]
          and (ROOT / n).stat().st_size == v["bytes"] for n, v in payload.items()))

    provenance = js(ROOT / "provenance.json")
    ready = js(ROOT / "preparation/READY.json")
    code = js(ROOT / "source/code-fingerprint.json")
    check("authorization_and_ready_binding", provenance["authorization"] == js(ROOT / "authorization.json")
          and provenance["authorization"]["prompt_two_confirmed"]
          and provenance["ready_sha256"] == provenance["authorization"]["ready_sha256"]
          == sha(ROOT / "preparation/READY.json"))
    check("training_code_fingerprint", code == provenance["code"] == ready["code"]
          and code["sha256"] == hashlib.sha256(json.dumps(code["files"], sort_keys=True).encode()).hexdigest())
    with tarfile.open(ROOT / "source/validated-training-source.tar.gz") as tar:
        source = {m.name: tar.extractfile(m).read() for m in tar.getmembers() if m.isfile()}
    check("training_source_coverage", set(source) == set(code["files"]))
    for name, data in source.items():
        check("training_source:" + name, hashlib.sha256(data).hexdigest() == code["files"][name])
    with tarfile.open(PRIOR / "source/validated-training-source.tar.gz") as tar:
        prior_source = {m.name: tar.extractfile(m).read() for m in tar.getmembers() if m.isfile()}
    model_files = [n for n in prior_source if n.startswith("mmseg/")]
    check("original_model_and_loss_source_unchanged", all(source[n] == prior_source[n] for n in model_files))

    data_dir = ROOT / "data-index/three-domain-manifests"
    audit = js(data_dir / "audit.json")
    manifests = {}
    for domain, train_n, val_n in (("A", 2975, 500), ("B", 400, 100), ("C", 400, 100)):
        for split, count in (("train", train_n), ("val", val_n)):
            name = domain + "_" + split
            records = jsonl(data_dir / (name + ".jsonl"))
            manifests[name] = records
            check("manifest:" + name, len(records) == count and len({v["id"] for v in records}) == count
                  and all(v["domain"] == domain and v["split"] == split for v in records)
                  and sha(data_dir / (name + ".jsonl")) == audit["manifest_sha256"][name + ".jsonl"])
            if domain in ("A", "B"):
                check("old_manifest_unchanged:" + name, sha(data_dir / (name + ".jsonl")) == sha(OLD_DATA / (name + ".jsonl")))
    check("C_recorded_data_audit", audit["status"] == "PASS" and audit["C_all_decoded"]
          and audit["C_trainIds_vs_labelIds_all_pixels_equal"]
          and not any(audit["overlaps_involving_C"].values()))
    check("C_archive_provenance_binding", sha(ROOT / "data-index/Rain-archive-provenance.json") == audit["archive_provenance_sha256"])
    histograms = {condition: [sum(v["label_histogram"].get(str(i), 0) for v in manifests[
        "C_val" if condition == "rain" else "B_val" if condition == "fog" else "A_val"])
        for i in range(19)] for condition in CONDITIONS}

    training = js(ROOT / "results/training-independent-check.json")["methods"]
    for method in METHODS:
        conv = js(ROOT / "preparation/conversion" / method / "conversion.json")
        rows = conv["keys"]
        check("parent_and_conversion:" + method, conv["parent_sha256"] == PARENTS[method]
              and conv["deployed_parent_tensors"] == 698
              and conv["target_tensors"] == len(rows) == (698 if method == "ft" else 1396)
              and not any(conv[k] for k in ("missing_keys", "unexpected_keys", "shape_mismatches"))
              and conv["all_values_exact"] and conv["strict_save_reload"]
              and conv["independent_parameter_and_buffer_storage"])
        if method != "ft":
            by_target = {v["target"]: v for v in rows}
            students = [v for v in rows if v["target"].startswith(("backbone_1.", "decode_head_1."))]
            check("student_promoted_with_all_buffers:" + method, len(students) == 698 and all(
                v["source"] == v["target"] and by_target[v["target"].replace("backbone_1.", "backbone.", 1)
                .replace("decode_head_1.", "decode_head.", 1)]["sha256"] == v["sha256"] for v in students))
        invocation = js(ROOT / "training" / method / "invocation.json")
        fresh = js(ROOT / "training" / method / "fresh-optimizer.json")
        cfg = config(ROOT / "training" / method / "resolved.py")
        check("C_fresh_training:" + method, invocation["train_domain"] == fresh["domain"] == "C"
              and invocation["seed"] == fresh["seed"] == cfg["randomness"]["seed"] == 0
              and not invocation["debug"] and not invocation["synthetic_fixture"]
              and invocation["initialization_sha256"] == conv["sha256"]
              and fresh["iteration"] == 0 and fresh["optimizer_state_empty"])
        check("training_config:" + method, cfg["train_dataloader"]["dataset"]["ann_file"].endswith("/C_train.jsonl")
              and cfg["val_dataloader"]["dataset"]["ann_file"].endswith("/C_val.jsonl")
              and cfg["train_dataloader"]["batch_size"] == 2 and cfg["train_cfg"]["max_iters"] == 4000
              and cfg["param_scheduler"][0]["end"] == 4000
              and cfg["optim_wrapper"]["optimizer"]["lr"] == 1e-5)
        check("completed_training_record:" + method, training[method]["iterations"] == 4000
              and training[method]["parent_sha256"] == PARENTS[method]
              and training[method]["losses_all_4000_finite"] and training[method]["parameter_policy_verified"]
              and not training[method]["formal_resume_used"])
    check("method_teacher_buffer_policies", len(training["gsmf"]["teacher_changed_buffers"]) == 342
          and training["lwf"]["teacher_changed_buffers"] == [])

    cells = js(ROOT / "results/42-cells.json")
    lookup = {(v["model"], v["condition"]): v for v in cells}
    check("seven_by_six_unique_cells", len(lookup) == len(cells) == 42 and
          {k[0] for k in lookup} == {"source"} | {m + "_" + s for m in METHODS for s in ("fog", "rain")})
    check("new_reused_image_counts", sum(v["provenance"] == "new" for v in cells) == 22
          and sum(v["provenance"] == "reused" for v in cells) == 20
          and sum(v["images"] for v in cells if v["provenance"] == "new") == 7000)
    protocol = js(ROOT / "results/protocol-independent-check.json")
    check("recorded_student_and_frozen_evaluation", protocol["status"] == "PASS" and len(protocol["cells"]) == 42
          and all(v["student_only"] and v["state_unchanged"] and v["GT_histogram_exact"] for v in protocol["cells"]))
    for cell in cells:
        name = cell["model"] + "-" + cell["condition"]
        matrix = js(ROOT / "results/matrices" / (name + ".json"))
        gt, pred, union, iou, mean = calculate(matrix["confusion_matrix"])
        check("matrix_and_metrics:" + name, matrix["confusion_matrix"] == cell["confusion_matrix"]
              and gt == matrix["GT_histogram"] == histograms[cell["condition"]]
              and pred == matrix["prediction_histogram"] and union == matrix["union"]
              and sum(gt) == matrix["valid_pixels"] == cell["valid_pixels"]
              and close(mean, matrix["mIoU"]) and close(mean, cell["mIoU"])
              and all((expected is None and matrix["IoU"][label] is None) or close(expected, matrix["IoU"][label])
                      for label, expected in zip(matrix["classes"], iou)))
        if cell["provenance"] == "reused":
            old_model = cell["model"].removesuffix("_fog")
            old_condition = "acdc" if cell["condition"] == "fog" else cell["condition"]
            old = js(PRIOR / "results/matrices" / (old_model + "_" + old_condition + ".json"))
            check("prior_matrix_identity:" + name, old["matrix"] == matrix["confusion_matrix"])
        else:
            proof = js(ROOT / "results/verification" / (name + ".json"))
            check("prediction_recheck_record:" + name, proof["status"] == "PASS"
                  and proof["metrics"]["confusion_matrix"] == matrix["confusion_matrix"]
                  and len(proof["predictions"]) == cell["images"] == (100 if cell["condition"] in ("rain", "fog") else 500))
    stages = js(ROOT / "results/real-domain-stages.json")
    deltas = js(ROOT / "results/stage-deltas.json")
    for method in METHODS:
        for stage_index, row in enumerate(stages[method]):
            scores = [lookup[(row["stage"], c)]["mIoU"] for c in ("clear", "fog", "rain")]
            check("seen_mean:" + method + ":" + str(stage_index),
                  all(close(row[k], value) for k, value in zip(("CS", "Fog", "Rain"), scores))
                  and close(row["seen_domain_equal_mean"], sum(scores[:stage_index + 1]) / (stage_index + 1)))
        before, after = stages[method][1:]
        check("stage_differences:" + method,
              close(deltas[method]["Fog_after_minus_Fog_stage"], after["Fog"] - before["Fog"])
              and close(deltas[method]["Rain_adaptation_after_minus_own_Fog"], after["Rain"] - before["Rain"])
              and close(deltas[method]["old_domain_forgetting_Fog"], before["Fog"] - after["Fog"]))
    samples = js(ROOT / "results/fixed-sample-selection-and-index.json")
    masks = list((ROOT / "results/fixed-samples").rglob("*.png")) + list((ROOT / "results/rain-fixed-samples").rglob("*.png"))
    mask_hashes = {sha(p) for p in masks}
    check("fixed_sample_predictions", len(masks) == len(samples["samples"]) == 114
          and samples["CS_new_raw_predictions"] == 72 and samples["Rain_unique_raw_predictions"] == 42
          and all(v["sha256"] in mask_hashes for v in samples["samples"]))
    with (ROOT / "results/42-cells.csv").open(encoding="utf-8", newline="") as handle:
        table = list(csv.DictReader(handle))
    check("summary_csv", len(table) == 42 and all(close(v["mIoU"], lookup[(v["model"], v["condition"])]["mIoU"]) for v in table))
    result = dict(status="PASS" if all(c["passed"] for c in CHECKS) else "FAIL",
                  verification_status="ANALYZED", model_rerun="CANNOT_VERIFY",
                  archive_sha256=sha(archive), payload_files=len(payload), sha_manifest_files=len(manifest),
                  training_source_files=len(source), unchanged_model_source_files=len(model_files),
                  checked=len(CHECKS), passed=sum(v["passed"] for v in CHECKS),
                  real_domain_stages=stages, stage_deltas=deltas, checks=CHECKS)
    output = HERE / ("REVIEW_" + RUN + "_checks.json")
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("status", "checked", "passed", "payload_files", "training_source_files")}))
    for item in CHECKS:
        if not item["passed"]:
            print("FAILED", item["name"])
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
