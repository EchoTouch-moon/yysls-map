#!/usr/bin/env python3
"""H-NEX-006R drift matrix: old snapshot artifacts vs new snapshot rebuild.

Old artifacts are DIFF INPUTS ONLY — never new evidence, never expected
results.  The matrix records, per comparable item, whether the new snapshot
reproduces the old observation byte-for-byte (block_sha256) or diverges.

Read-only: reads old committed artifacts + the new run dir; writes one JSON.
"""

import argparse
import hashlib
import json
import os
import sys

OLD_BASE = "docs/research/evidence/windows/wave-1.6"


def load_records(dirs):
    """Load engine records from one or more dirs; key = (archive, index)."""
    recs = {}
    for d in dirs:
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if not f.endswith(".json"):
                continue
            r = json.load(open(os.path.join(d, f), encoding="utf-8"))
            recs[(r["archive"], r["entry_index"])] = r
    return recs


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(1 << 20)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--new-run-dir", required=True,
                    help="dir containing records/ and packet/ of the new run")
    ap.add_argument("--old-base", default=OLD_BASE)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    old_records = load_records([
        os.path.join(args.old_base, "nex004b-structural-discovery", "regression"),
        os.path.join(args.old_base, "nex004b-structural-discovery", "blind"),
        os.path.join(args.old_base, "nex004c-holdout", "holdout-json"),
    ])
    new_records = load_records([
        os.path.join(args.new_run_dir, "records", "regression"),
        os.path.join(args.new_run_dir, "records", "holdout-json"),
        os.path.join(args.new_run_dir, "records", "blind"),
    ])

    old_manifest = json.load(open(os.path.join(
        args.old_base, "nex005-qinghe-packet", "out",
        "selection-manifest.json"), encoding="utf-8"))
    new_manifest = json.load(open(os.path.join(
        args.new_run_dir, "packet", "selection-manifest.json"), encoding="utf-8"))
    old_packet = json.load(open(os.path.join(
        args.old_base, "nex005-qinghe-packet", "out",
        "qinghe-evidence-packet.json"), encoding="utf-8"))
    new_packet = json.load(open(os.path.join(
        args.new_run_dir, "packet", "qinghe-evidence-packet.json"), encoding="utf-8"))

    entry_rows = []
    for key in sorted(set(old_records) | set(new_records)):
        o = old_records.get(key)
        n = new_records.get(key)
        row = {
            "archive": key[0], "entry_index": key[1],
            "in_old": o is not None, "in_new": n is not None,
        }
        if o and n:
            row["block_sha256_equal"] = o.get("block_sha256") == n.get("block_sha256")
            row["old_game_version"] = o.get("game_version")
            row["new_game_version"] = n.get("game_version")
            row["observation_count_old"] = len(o.get("observations", []))
            row["observation_count_new"] = len(n.get("observations", []))
        entry_rows.append(row)

    old_sel = [(e["archive"], e["entry_index"]) for e in old_manifest["entries"]]
    new_sel = [(e["archive"], e["entry_index"]) for e in new_manifest["entries"]]
    old_scores = {(e["archive"], e["entry_index"]): e["score"]
                  for e in old_manifest["entries"]}
    new_scores = {(e["archive"], e["entry_index"]): e["score"]
                  for e in new_manifest["entries"]}
    selection_rows = []
    for pos in range(max(len(old_sel), len(new_sel))):
        o = old_sel[pos] if pos < len(old_sel) else None
        n = new_sel[pos] if pos < len(new_sel) else None
        selection_rows.append({
            "rank": pos,
            "old": (f"{o[0]}[{o[1]}]" if o else None),
            "new": (f"{n[0]}[{n[1]}]" if n else None),
            "same_entry": o == n,
            "old_score": old_scores.get(o) if o else None,
            "new_score": new_scores.get(n) if n else None,
        })

    old_clusters = {c["cluster_id"]: sorted(
        f"{e['archive']}[{e['entry_index']}]" for e in c["entries"])
        for c in old_packet["clusters"]}
    new_clusters = {c["cluster_id"]: sorted(
        f"{e['archive']}[{e['entry_index']}]" for e in c["entries"])
        for c in new_packet["clusters"]}
    cluster_rows = []
    for cid in sorted(set(old_clusters) | set(new_clusters)):
        cluster_rows.append({
            "cluster_id": cid,
            "old_entries": old_clusters.get(cid),
            "new_entries": new_clusters.get(cid),
            "identical": old_clusters.get(cid) == new_clusters.get(cid),
        })

    both = [r for r in entry_rows if r["in_old"] and r["in_new"]]
    matrix = {
        "schema": "hnex006r-drift-matrix-1",
        "policy": ("old artifacts are diff inputs only; no old locator, "
                   "record, or manifest was used as new evidence or as an "
                   "expected result by the rebuild pipeline"),
        "old_snapshot": {
            "game_version": old_manifest["game_version"],
            "packet_sha256": sha256_file(os.path.join(
                args.old_base, "nex005-qinghe-packet", "out",
                "qinghe-evidence-packet.json")),
            "manifest_sha256": sha256_file(os.path.join(
                args.old_base, "nex005-qinghe-packet", "out",
                "selection-manifest.json")),
            "record_count": len(old_records),
        },
        "new_snapshot": {
            "game_version": new_manifest["game_version"],
            "packet_sha256": sha256_file(os.path.join(
                args.new_run_dir, "packet", "qinghe-evidence-packet.json")),
            "manifest_sha256": sha256_file(os.path.join(
                args.new_run_dir, "packet", "selection-manifest.json")),
            "record_count": len(new_records),
        },
        "summary": {
            "game_version_changed":
                old_manifest["game_version"] != new_manifest["game_version"],
            "selection_membership_equal": set(old_sel) == set(new_sel),
            "selection_order_equal": old_sel == new_sel,
            "selection_scores_equal":
                all(old_scores[k] == new_scores[k] for k in old_sel
                    if k in new_scores) and set(old_sel) == set(new_sel),
            "cluster_layout_identical":
                all(r["identical"] for r in cluster_rows)
                and set(old_clusters) == set(new_clusters),
            "records_compared": len(both),
            "records_block_identical":
                sum(1 for r in both if r["block_sha256_equal"]),
            "records_block_diverged":
                sum(1 for r in both if not r["block_sha256_equal"]),
            "records_old_only":
                sum(1 for r in entry_rows if r["in_old"] and not r["in_new"]),
            "records_new_only":
                sum(1 for r in entry_rows if r["in_new"] and not r["in_old"]),
        },
        "selection_ranks": selection_rows,
        "clusters": cluster_rows,
        "entries": entry_rows,
    }
    canonical = json.dumps(matrix, sort_keys=True, separators=(",", ":"))
    matrix["matrix_sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(matrix, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
    s = matrix["summary"]
    sys.stdout.buffer.write((
        f"records compared={s['records_compared']} "
        f"block_identical={s['records_block_identical']} "
        f"diverged={s['records_block_diverged']} "
        f"old_only={s['records_old_only']} new_only={s['records_new_only']}\n"
        f"selection order equal={s['selection_order_equal']} "
        f"scores equal={s['selection_scores_equal']} "
        f"clusters identical={s['cluster_layout_identical']}\n"
        f"game_version {matrix['old_snapshot']['game_version']} -> "
        f"{matrix['new_snapshot']['game_version']}\n"
        f"matrix_sha256={matrix['matrix_sha256']}\n"
    ).encode("utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
