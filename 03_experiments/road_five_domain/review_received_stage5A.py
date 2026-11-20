"""Offline audit of the received five-domain stage A (seed0 Rain->Snow->Night), without executing archived code.

Standard library only. Reads the extracted handoff package, the external receipts and the locally received
step-3 package; writes REVIEW_<run>_checks.json and CS_CONFUSION_SHIFT_stageA_2026-11-11.json beside this script.
Usage: python -I review_received_stage5A.py
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
RUN = "formal-A-plan-20261111-140000"
RECEIVED = HERE / RUN
ROOT = RECEIVED / RUN
S3 = HERE.parent / "road_clear_fog_rain/formal-seed0-plan-20261110-180543/formal-seed0-plan-20261110-180543"
S3_SHIFT = HERE.parent / "road_clear_fog_rain/CS_CONFUSION_SHIFT_2026-11-11.json"
REMOTE_PROJECT = "/home/ysheng4/research/GSMF-RS-DIL"
METHODS = ("ft", "gsmf", "lwf")
CONDITIONS = ("clear", "fog005", "fog010", "fog020", "fog", "rain", "snow", "night")
REAL = ("clear", "fog", "rain", "snow", "night")
IMAGES = dict(clear=500, fog005=500, fog010=500, fog020=500, fog=100, rain=100, snow=100, night=106)
VAL_OF = dict(clear="A_val", fog005="A_val", fog010="A_val", fog020="A_val", fog="B_val", rain="C_val",
              snow="D_val", night="E_val")
COUNTS = dict(A=(2975, 500), B=(400, 100), C=(400, 100), D=(400, 100), E=(400, 106))
TRACKED = ("terrain", "truck", "train", "sky", "building", "fence", "bicycle")
CHECKS = []


def js(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def sha(path):
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def check(name, condition, detail=None):
    item = {"name": name, "passed": bool(condition)}
    if detail is not None:
        item["detail"] = detail
    CHECKS.append(item)


def close(a, b, tol=1e-9):
    return a is not None and b is not None and math.isclose(float(a), float(b), rel_tol=0, abs_tol=tol)


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
        return {k.arg: literal(k.value) for k in node.keywords}
    raise ValueError("Unsupported resolved configuration syntax: " + ast.dump(node)[:80])


def config(path):
    result = {}
    for n in ast.parse(Path(path).read_text(encoding="utf-8")).body:
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


def local_manifest(remote_path):
    """Map a remote manifest path from the prepared directory to its copy inside the package."""
    marker = "/prepare-20261111-140000/"
    rel = remote_path.split(marker, 1)[1]
    if rel.startswith("data/"):
        return ROOT / "data-and-config-index" / rel
    if rel.startswith("eval-manifests/"):
        return ROOT / "data-and-config-index" / rel
    raise ValueError(remote_path)


def stage_names(method):
    return ["source", method + "_fog", method + "_rain", method + "-seed0-D", method + "-seed0-E"]


def archive_checks():
    archive = RECEIVED / (RUN + "-light.tar.gz")
    external = js(RECEIVED / "handoff-verification.json")
    completion = js(RECEIVED / "completion.json")
    final_status = js(RECEIVED / "remote-final-status.json")
    supervisor = js(RECEIVED / "remote-completion-status.json")
    digest = sha(archive)
    check("external_archive_sha", digest == external["archive_sha256"] == completion["handoff"]["archive_sha256"]
          == final_status["archive_sha256"]
          == (RECEIVED / (RUN + "-light.tar.gz.sha256")).read_text().split()[0])
    check("remote_complete", completion["status"] == final_status["state"] == supervisor["state"] == "complete"
          and final_status["exit_code"] == 0 and completion["handoff"]["status"] == external["status"] == "PASS"
          and (ROOT / "exit-code.txt").read_text().strip() == "0")
    check("remote_scope_B_not_started", "B deferred" in completion["next_phase"]
          and "B deferred" in final_status["next_phase"] and "C not authorized" in supervisor["next_phase"])
    with tarfile.open(archive) as tar:
        members = tar.getmembers()
        names = [str(PurePosixPath(m.name)).casefold() for m in members]
        check("safe_archive_members", len(names) == len(set(names)) and all(
            PurePosixPath(m.name).parts[0] == RUN and not PurePosixPath(m.name).is_absolute()
            and ".." not in PurePosixPath(m.name).parts and "\\" not in m.name
            and ":" not in m.name and (m.isfile() or m.isdir()) for m in members))
        archived = {m.name: hashlib.sha256(tar.extractfile(m).read()).hexdigest() for m in members if m.isfile()}
    on_disk = {p.relative_to(RECEIVED).as_posix() for p in ROOT.rglob("*") if p.is_file()}
    check("extracted_file_set_equals_archive", set(archived) == on_disk)
    check("extracted_files_match_archive", all(sha(RECEIVED / n) == d for n, d in archived.items()))
    files = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file()}
    manifest = {}
    bad = []
    for line in (ROOT / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines():
        d, name = line.split("  ", 1)
        if name in manifest or sha(ROOT / name) != d:
            bad.append(name)
        manifest[name] = d
    check("sha_manifest_all_match", not bad, bad[:5])
    payload = js(ROOT / "MANIFEST.json")["files"]
    check("sha_manifest_exact_coverage", set(manifest) == files - {"MANIFEST.sha256"})
    check("json_manifest_exact_coverage", set(payload) == files - {"MANIFEST.sha256", "MANIFEST.json"}
          and len(payload) == external["payload_files"] == completion["handoff"]["payload_files"] == 1519)
    check("json_manifest_hashes_and_sizes", all(sha(ROOT / n) == v["sha256"] and (ROOT / n).stat().st_size == v["bytes"]
                                                for n, v in payload.items()))
    return dict(archive_sha256=digest, archive_bytes=archive.stat().st_size, payload_files=len(payload),
                sha_manifest_files=len(manifest), archive_members=len(members))


def code_checks():
    provenance = js(ROOT / "provenance.json")
    ready_path = ROOT / "preparation/READY.json"
    ready = js(ready_path)
    auth = js(ROOT / "authorization-A.json")
    scope = js(ROOT / "preparation/authorization-scope-20261111.json")
    check("authorization_A_binding", auth == js(ROOT / "preparation/authorization-A.json") == provenance["authorization"]
          and auth["phase"] == "A" and auth["confirmed"]
          and auth["ready_sha256"] == provenance["ready_sha256"] == sha(ready_path))
    check("authorization_scope_A_only", scope["active_phases"] == ["A"] and set(scope["deferred_phases"]) == {"B", "C"}
          and scope["automatic_B_start"] is False)
    code = js(ROOT / "source/code-fingerprint.json")
    check("training_code_fingerprint", code == provenance["code"] == ready["code"]
          and code["sha256"] == hashlib.sha256(json.dumps(code["files"], sort_keys=True).encode()).hexdigest())
    with tarfile.open(ROOT / "source/formal-training-source.tar.gz") as tar:
        source = {m.name: tar.extractfile(m).read() for m in tar.getmembers() if m.isfile()}
    check("training_source_coverage", set(source) == set(code["files"]))
    mismatch = [n for n, data in source.items() if hashlib.sha256(data).hexdigest() != code["files"].get(n)]
    check("training_source_hashes", not mismatch, mismatch[:5])
    with tarfile.open(S3 / "source/validated-training-source.tar.gz") as tar:
        prior = {m.name: tar.extractfile(m).read() for m in tar.getmembers() if m.isfile()}
    model_files = sorted(n for n in prior if n.startswith("mmseg/"))
    check("original_model_and_loss_source_unchanged_vs_step3",
          bool(model_files) and all(source.get(n) == prior[n] for n in model_files))
    return dict(training_source_files=len(source), unchanged_model_source_files=len(model_files))


def data_checks():
    ddir = ROOT / "data-and-config-index/data"
    audit = js(ddir / "audit.json")
    manifests = {}
    for domain, (train_n, val_n) in COUNTS.items():
        for split, count in (("train", train_n), ("val", val_n)):
            name = domain + "_" + split
            records = jsonl(ddir / (name + ".jsonl"))
            manifests[name] = records
            check("manifest:" + name, len(records) == count and len({v["id"] for v in records}) == count
                  and all(v["domain"] == domain and v["split"] == split for v in records)
                  and sha(ddir / (name + ".jsonl")) == audit["manifest_sha256"][name + ".jsonl"])
            if domain in "ABC":
                check("ABC_manifest_identical_to_step3:" + name,
                      sha(ddir / (name + ".jsonl")) == sha(S3 / "data-index/three-domain-manifests" / (name + ".jsonl")))
    check("DE_recorded_data_audit", audit["status"] == "PASS" and audit["full_official_counts"]
          and audit["DE_all_decoded"] and audit["DE_trainIds_vs_labelIds_all_pixels_equal"]
          and not any(audit["overlaps_involving_DE"].values()))
    for domain in "DE":
        for split in ("train", "val"):
            g = audit["groups"][domain + "_" + split]
            hist = {str(i): sum(v["label_histogram"].get(str(i), 0) for v in manifests[domain + "_" + split]) for i in range(19)}
            check("DE_audit_group:" + domain + "_" + split, g["count"] == g["expected"] == len(manifests[domain + "_" + split])
                  and all(hist[str(i)] == g["histogram"].get(str(i), 0) for i in range(19)) and not g["orphan_labels"])
    # Local re-check of frame / byte / decoded-pixel overlaps involving D and E, across all ten groups.
    overlaps = {}
    for key in ("frame_id", "image_sha256", "rgb_pixels_sha256"):
        seen = {}
        dup = []
        for name, records in manifests.items():
            for v in records:
                if v.get(key) is None:
                    continue
                if v[key] in seen and (name[0] in "DE" or seen[v[key]][0] in "DE"):
                    dup.append((seen[v[key]], name, v[key]))
                seen.setdefault(v[key], name)
        overlaps[key] = dup
    check("local_DE_overlap_recheck", not any(overlaps.values()), {k: len(v) for k, v in overlaps.items()})
    pairs = {tuple(k.split(" vs ")): v for k, v in audit["shared_video_directories"].items()}
    de_pairs = {k: v for k, v in pairs.items() if k[0][0] in "DE" or k[1][0] in "DE"}
    check("DE_no_cross_domain_shared_sequences", bool(de_pairs) and not any(
        v for k, v in de_pairs.items() if k[0][0] != k[1][0]))
    disclosure = {" vs ".join(k): v for k, v in de_pairs.items() if v}
    histograms = {c: [sum(v["label_histogram"].get(str(i), 0) for v in manifests[VAL_OF[c]]) for i in range(19)]
                  for c in CONDITIONS}
    return manifests, histograms, dict(shared_video_directories_DE=disclosure,
                                       night_val_images=len(manifests["E_val"]), snow_val_images=len(manifests["D_val"]))


def training_checks(cells_by_model):
    s3_training = js(S3 / "results/training-independent-check.json")["methods"]
    rain_final = {m: s3_training[m]["checkpoint_sha256"] for m in METHODS}
    tic = js(ROOT / "results/training-independent-check.json")
    check("training_independent_check_pass", tic["status"] == "PASS" and len(tic["runs"]) == 6)
    remote_weights = {v["sha256"] for v in js(ROOT / "remote-index.json")["weights"].values()}
    summary = {}
    for method in METHODS:
        for domain in "DE":
            run = method + "-seed0-" + domain
            rec = tic["runs"][run]
            if domain == "D":
                parent_sha = rain_final[method]
                parent_path = "/road_clear_fog_rain/formal-seed0-plan-20261110-180543/" + method + "/iter_4000.pth"
            else:
                parent_sha = tic["runs"][method + "-seed0-D"]["final_checkpoint_sha256"]
                parent_path = "/road_five_domain/" + RUN + "/" + method + "-seed0-D/iter_4000.pth"
            conv = js(ROOT / "initializations" / run / "conversion.json")
            keys = conv["keys"]
            expected_targets = 698 if method == "ft" else 1396
            check("parent_and_conversion:" + run, conv["status"] == "PASS" and conv["method"] == method
                  and conv["parent_sha256"] == rec["parent_sha256"] == parent_sha
                  and conv["parent"].endswith(parent_path) and rec["parent"].endswith(parent_path)
                  and conv["deployed_parent_tensors"] == 698
                  and conv["target_tensors"] == len(keys) == expected_targets
                  and len({k["target"] for k in keys}) == expected_targets
                  and all(k["parent_checkpoint_sha256"] == parent_sha for k in keys)
                  and not any(conv[k] for k in ("missing_keys", "unexpected_keys", "shape_mismatches"))
                  and conv["all_values_exact"] and conv["strict_save_reload"]
                  and conv["independent_parameter_and_buffer_storage"])
            if method == "ft":
                check("ft_full_inheritance:" + run, all(k["source"] == k["target"] for k in keys))
            else:
                by_target = {k["target"]: k for k in keys}
                students = [k for k in keys if k["target"].startswith(("backbone_1.", "decode_head_1."))]
                check("student_promoted_to_teacher_and_student:" + run, len(students) == 698 and all(
                    k["source"] == k["target"]
                    and by_target[k["target"].replace("backbone_1.", "backbone.", 1).replace("decode_head_1.", "decode_head.", 1)]["sha256"] == k["sha256"]
                    and by_target[k["target"].replace("backbone_1.", "backbone.", 1).replace("decode_head_1.", "decode_head.", 1)]["source"] == k["target"]
                    for k in students))
            inv = js(ROOT / "training" / run / "invocation.json")
            fresh = js(ROOT / "training" / run / "fresh-optimizer.json")
            cfg = config(ROOT / "training" / run / "resolved.py")
            check("fresh_training_invocation:" + run, inv["train_domain"] == fresh["domain"] == rec["domain"] == domain
                  and inv["seed"] == fresh["seed"] == rec["seed"] == cfg["randomness"]["seed"] == 0
                  and inv["order"] == "ABCDE" and not inv["debug"] and not inv["synthetic_fixture"]
                  and inv["optimizer"] == "fresh" and inv["stage"] == method
                  and inv["initialization_sha256"] == conv["sha256"] == rec["initialization_sha256"]
                  and fresh["iteration"] == 0 and fresh["optimizer_state_empty"] and fresh["scheduler_end"] == 4000)
            check("training_config:" + run,
                  cfg["train_dataloader"]["dataset"]["ann_file"].endswith("/" + domain + "_train.jsonl")
                  and cfg["val_dataloader"]["dataset"]["ann_file"].endswith("/" + domain + "_val.jsonl")
                  and cfg["train_dataloader"]["batch_size"] == 2
                  and cfg["train_cfg"]["max_iters"] == 4000 and cfg["train_cfg"]["val_interval"] == 1000
                  and cfg["param_scheduler"][0]["end"] == 4000
                  and cfg["optim_wrapper"]["optimizer"]["type"] == "AdamW"
                  and cfg["optim_wrapper"]["optimizer"]["lr"] == 1e-5
                  and cfg["default_hooks"]["checkpoint"]["interval"] == 1000
                  and cfg["load_from"].endswith("/initialization/" + run + "/" + method + "_init.pth")
                  and cfg["road_checkpoint_meta"]["road_seed"] == 0
                  and cfg["road_checkpoint_meta"]["parent_checkpoint"].endswith(parent_path))
            audit = js(ROOT / "training" / run / "audit-end-4000.json")
            check("losses_4000_finite_local:" + run, len(audit["losses"]) == 4000
                  and all(math.isfinite(v) for v in audit["losses"]) and audit["finite_all_checked_gradients"])
            groups = rec["groups"]
            if method == "gsmf":
                policy = (groups["backbone"]["changed_parameters"] == 0 and groups["decode_head"]["changed_parameters"] == 0
                          and groups["backbone"]["trainable_elements"] == 0
                          and groups["backbone_1.stem"]["changed_parameters"] == 0
                          and groups["backbone_1.layer1"]["changed_parameters"] == 0
                          and groups["backbone_1.stem"]["trainable_elements"] == 0
                          and groups["backbone_1.layer1"]["trainable_elements"] == 0
                          and groups["backbone_1"]["trainable_elements"] > 0 and groups["decode_head_1"]["trainable_elements"] > 0
                          and len(rec["teacher_changed_buffers"]) == 342)
            elif method == "lwf":
                policy = (all(groups[g]["changed_parameters"] == 0 and groups[g]["changed_bn_buffers"] == 0
                              and groups[g]["trainable_elements"] == 0 for g in ("backbone", "decode_head"))
                          and groups["backbone_1"]["trainable_elements"] > 0 and rec["teacher_changed_buffers"] == [])
            else:
                policy = rec["teacher_changed_buffers"] == [] and all(g["trainable_elements"] > 0 for g in groups.values()
                                                                       if g["parameters"])
            check("method_parameter_policy:" + run, policy)
            final = rec["final_checkpoint_sha256"]
            check("completed_training_record:" + run, rec["iterations"] == 4000 and rec["fresh_optimizer"]
                  and rec["periodic_all_complete"] and rec["losses_all_finite"] and rec["resume_used"] is False
                  and cells_by_model[run] == {final} and final in remote_weights)
            summary[run] = dict(parent_sha256=parent_sha, initialization_sha256=conv["sha256"], final_sha256=final,
                                wall_minutes=rec["training_wall_seconds"] / 60,
                                peak_allocated_MiB=rec["peak_allocated_MiB"], teacher_changed_buffers=len(rec["teacher_changed_buffers"]))
    check("remote_index_weights_cover_13_checkpoints", remote_weights == set().union(*cells_by_model.values())
          and len(remote_weights) == 13)
    return summary


def cell_checks(histograms, manifests):
    cells = js(ROOT / "results/cells.json")
    lookup = {(c["model"], c["condition"]): c for c in cells}
    models = {m for m, _ in lookup}
    check("thirteen_by_eight_unique_cells", len(lookup) == len(cells) == 104 and len(models) == 13
          and all((m, c) in lookup for m in models for c in CONDITIONS))
    new = [c for c in cells if c["provenance"] == "new"]
    reused = [c for c in cells if c["provenance"] == "reused"]
    check("new_reused_counts", len(new) == 62 and len(reused) == 42
          and sum(c["images"] for c in new) == 15878 and all(c["images"] == IMAGES[c["condition"]] for c in cells))
    old_models = {"source"} | {m + s for m in METHODS for s in ("_fog", "_rain")}
    check("reuse_scope", {(c["model"], c["condition"]) for c in reused}
          == {(m, c) for m in old_models for c in ("clear", "fog005", "fog010", "fog020", "fog", "rain")})
    protocol = js(ROOT / "results/protocol-independent-check.json")
    pcells = {(c["model"], c["condition"]): c for c in protocol["cells"]}
    check("recorded_student_only_frozen_evaluation", protocol["status"] == "PASS" and len(pcells) == 104 and all(
        v["student_only"] and v["state_unchanged"] and v["GT_histogram_exact"] and v["exact_ID_paths_encoding"]
        for v in pcells.values()))
    check("protocol_GT_histograms_equal_manifests", all(protocol["GT_histograms"][c] == histograms[c] for c in CONDITIONS))
    s3_cells = {(c["model"], c["condition"]): c for c in js(S3 / "results/42-cells.json")}
    wide = {}
    with (ROOT / "results/class-iou-wide.csv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            wide[row["class_name"]] = row
    classes = list(wide)
    verification = js(ROOT / "results/verification.json")
    check("verification_summary", verification["status"] == "PASS" and verification["new_cells"] == 62
          and verification["independent_reread_images"] == 15878)
    for cell in cells:
        name = cell["model"] + "-" + cell["condition"]
        matrix = cell["confusion_matrix"]
        gt, pred, union, iou, mean = calculate(matrix)
        p = pcells[(cell["model"], cell["condition"])]
        man = local_manifest(p["manifest"])
        col = cell["model"] + "/" + cell["condition"]
        check("matrix_and_metrics:" + name, gt == histograms[cell["condition"]] and sum(gt) == cell["valid_pixels"]
              and close(mean, cell["mIoU"]) and p["checkpoint_sha256"] == cell["checkpoint_sha256"]
              and sha(man) == p["manifest_sha256"]
              and all((iou[i] is None and wide[k][col] in ("", "None", "null", "nan"))
                      or (iou[i] is not None and close(iou[i], wide[k][col], 1e-7)) for i, k in enumerate(classes)))
        if cell["provenance"] == "reused":
            old = s3_cells[(cell["model"], cell["condition"])]
            check("reused_matrix_identical_to_step3:" + name, old["confusion_matrix"] == matrix
                  and old["checkpoint_sha256"] == cell["checkpoint_sha256"] and close(old["mIoU"], cell["mIoU"]))
        else:
            proof = js(ROOT / "results/verification" / (name + ".json"))
            ids = [v["id"] for v in proof["predictions"]]
            manifest_ids = {v["id"] for v in jsonl(man)} if man.suffix == ".jsonl" else None
            check("new_cell_reread_record:" + name, proof["status"] == "PASS"
                  and proof["metrics"]["confusion_matrix"] == matrix and close(proof["metrics"]["mIoU"], mean)
                  and proof["metrics"]["gt_histogram"] == gt and len(ids) == len(set(ids)) == cell["images"]
                  and (manifest_ids is None or set(ids) == manifest_ids))
    return cells, lookup, classes


def stage_checks(lookup):
    stages = js(ROOT / "results/stage-matrices.json")
    deltas = js(ROOT / "results/signed-deltas-and-forgetting.json")
    out = {}
    for method in METHODS:
        key = method + "-seed0-ABCDE"
        names = stage_names(method)
        R = [{c: lookup[(n, c)]["mIoU"] for c in REAL} for n in names]
        rows = stages[key]
        check("stage_matrix:" + method, [r["stage"] for r in rows] == names and all(
            all(close(rows[t]["values"][c], R[t][c]) for c in REAL)
            and rows[t]["seen_domains"] == list(REAL[:t + 1])
            and close(rows[t]["seen_domain_equal_mean"], sum(R[t][c] for c in REAL[:t + 1]) / (t + 1)) for t in range(5)))
        d = deltas[key]
        ok = len(d["stage_changes"]) == 4
        for t in range(1, 5):
            s = d["stage_changes"][t - 1]
            ok = ok and s["stage"] == names[t] and s["new_domain"] == REAL[t] and all(
                close(s["after_minus_before"][c], R[t][c] - R[t - 1][c])
                and close(s["cumulative_after_minus_Source"][c], R[t][c] - R[0][c]) for c in REAL) \
                and close(s["new_domain_adaptation_gain"], R[t][REAL[t]] - R[t - 1][REAL[t]])
        check("signed_stage_changes:" + method, ok)
        forgetting = {}
        for j, c in enumerate(REAL[:4]):
            best_t = max(range(j, 4), key=lambda t: R[t][c])
            forgetting[c] = dict(reference_stage=names[best_t], signed_forgetting=R[best_t][c] - R[4][c])
        check("old_domain_forgetting:" + method, all(
            d["old_domain_forgetting"][c]["reference_stage"] == forgetting[c]["reference_stage"]
            and close(d["old_domain_forgetting"][c]["signed_forgetting"], forgetting[c]["signed_forgetting"]) for c in forgetting)
            and close(d["old_domain_mean_forgetting"], sum(v["signed_forgetting"] for v in forgetting.values()) / 4)
            and close(d["final_five_real_domain_mean"], sum(R[4].values()) / 5))
        out[method] = dict(stages=dict(zip(names, R)), seen_mean=[sum(R[t][c] for c in REAL[:t + 1]) / (t + 1) for t in range(5)],
                           forgetting=forgetting, mean_forgetting=sum(v["signed_forgetting"] for v in forgetting.values()) / 4,
                           final_five_mean=sum(R[4].values()) / 5)
    text = (ROOT / "SUMMARY.md").read_text(encoding="utf-8")
    check("summary_headline_numbers", all(("%.4f" % out[m][k]) in text for m in METHODS for k in ("final_five_mean", "mean_forgetting")))
    return out


def confusion_checks(lookup, classes):
    tracking = js(ROOT / "results/confusion-tracking.json")
    names = ["source"] + [n for m in METHODS for n in stage_names(m)[1:]]
    road = classes.index("road")
    ok = True
    for n in names:
        M = lookup[(n, "clear")]["confusion_matrix"]
        row = M[road]
        top = sorted(range(19), key=lambda j: -row[j])[:5]
        rec = tracking[n + "-clear"]["road_destinations_top5"]
        ok = ok and [r["class_name"] for r in rec] == [classes[j] for j in top] and all(
            r["pixels"] == row[j] and close(r["fraction"], row[j] / sum(row)) for r, j in zip(rec, top))
    check("road_destinations_top5_clear", ok)
    with (ROOT / "results/road-destinations-all-classes.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    ok = bool(rows)
    for r in rows:
        M = lookup[(r["stage"], r["condition"])]["confusion_matrix"]
        row = M[road]
        ok = ok and int(r["road_GT_pixels"]) == sum(row) and all(
            close(r["road_to_" + classes[j]], row[j] / sum(row), 1e-12) for j in range(19))
    check("road_destinations_csv_all_rows", ok, len(rows))
    # Same calculation as road_clear_fog_rain/analyze_cs_confusion_shift.py, extended to 13 checkpoints.
    src = lookup[("source", "clear")]
    src_iou = calculate(src["confusion_matrix"])[3]
    result = dict(scope="Cityscapes val500 clear; seed0 stage A; descriptive only, no significance test",
                  method_note="same formulas as road_clear_fog_rain/analyze_cs_confusion_shift.py", clear={})
    for n in names:
        M = lookup[(n, "clear")]["confusion_matrix"]
        iou = calculate(M)[3]
        road_row = M[road]
        tracked = {}
        for c in TRACKED:
            j = classes.index(c)
            colv = [M[i][j] for i in range(19)]
            p, g = sum(colv), sum(M[j])
            tracked[c] = dict(IoU=float(iou[j]), pred_over_gt_area=p / g, recall_percent=100 * M[j][j] / g,
                              false_positive_sources_percent={classes[i]: 100 * colv[i] / p
                                                              for i in sorted(range(19), key=lambda i: -colv[i])[:3]})
        drop = {classes[i]: float(src_iou[i] - iou[i]) / 19 for i in range(19)}
        result["clear"][n] = dict(mIoU=lookup[(n, "clear")]["mIoU"],
                                  road_gt_predicted_as_percent={classes[j]: 100 * road_row[j] / sum(road_row)
                                                                for j in sorted(range(19), key=lambda j: -road_row[j])[:5]},
                                  tracked=tracked, miou_drop_vs_source_pp=sum(drop.values()),
                                  per_class_drop_contribution_pp=dict(sorted(drop.items(), key=lambda kv: -kv[1])))
    for stage in ("_fog", "_rain", "-seed0-D", "-seed0-E"):
        g = calculate(lookup[("gsmf" + stage, "clear")]["confusion_matrix"])[3]
        f = calculate(lookup[("ft" + stage, "clear")]["confusion_matrix"])[3]
        contrib = {classes[i]: float(g[i] - f[i]) / 19 for i in range(19)}
        result["gsmf_minus_ft" + stage.replace("-seed0-", "_") + "_contribution_pp"] = dict(
            total=sum(contrib.values()), per_class=dict(sorted(contrib.items(), key=lambda kv: kv[1])))
    old = js(S3_SHIFT)["clear"]
    check("confusion_shift_old_checkpoints_match_step3_analysis", all(
        all(close(old[m]["road_gt_predicted_as_percent"][k], v) for k, v in result["clear"][m]["road_gt_predicted_as_percent"].items())
        and close(old[m]["miou_drop_vs_source_pp"], result["clear"][m]["miou_drop_vs_source_pp"])
        for m in old))
    out = HERE / "CS_CONFUSION_SHIFT_stageA_2026-11-11.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return result


def sample_checks():
    index = js(ROOT / "results/fixed-sample-selection-and-index.json")
    masks = list((ROOT / "results/fixed-samples").rglob("*.png"))
    local = {sha(p) for p in masks}
    indexed = {v["sha256"] for v in index["samples"]}
    aligned = [p for p in (ROOT / "results/figures").glob("*.png")
               if p.name.split("-", 1)[0] in ("clear", "snow", "night")]
    check("fixed_sample_predictions", index["status"] == "PASS" and index["selected_before_inference"]
          and len(masks) == index["total_raw_masks"] == 192 and index["new_raw_CS_masks"] == 36
          and index["all_DE_raw_masks"] == 156 and local <= indexed and len(index["samples"]) == 234
          and len(aligned) == index["aligned_figures"] == 18)


def main():
    info = archive_checks()
    info.update(code_checks())
    manifests, histograms, data_info = data_checks()
    cells, lookup, classes = cell_checks(histograms, manifests)
    by_model = {}
    for c in cells:
        by_model.setdefault(c["model"], set()).add(c["checkpoint_sha256"])
    training = training_checks(by_model)
    stages = stage_checks(lookup)
    shift = confusion_checks(lookup, classes)
    sample_checks()
    result = dict(status="PASS" if all(c["passed"] for c in CHECKS) else "FAIL",
                  verification_status="ANALYZED", model_rerun="CANNOT_VERIFY",
                  checked=len(CHECKS), passed=sum(c["passed"] for c in CHECKS), **info, data=data_info,
                  training=training, real_domain_results=stages,
                  confusion_summary={n: v["road_gt_predicted_as_percent"] for n, v in shift["clear"].items()},
                  checks=CHECKS)
    output = HERE / ("REVIEW_" + RUN + "_checks.json")
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("status", "checked", "passed", "payload_files", "training_source_files")}))
    for item in CHECKS:
        if not item["passed"]:
            print("FAILED", item["name"], item.get("detail", ""))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
