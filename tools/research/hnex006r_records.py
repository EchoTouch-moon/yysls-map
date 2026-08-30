#!/usr/bin/env python3
"""H-NEX-006R Phase B driver: record-set rebuild on the new snapshot.

Materializes the three record categories the frozen packet builder consumes,
using ONLY frozen code (loaded byte-for-byte from git blobs) and the current
archive snapshot.  No old locators, old records, or old manifests are read;
the frozen selector's EXCLUDED constant is the sole disjunction mechanism.

  regression/   : frozen engine re-run on the builder's KNOWN entries.
  holdout-json/ : frozen engine re-run on a FRESH selection produced by the
                  frozen narrative_holdout_selector (schema v2).
  blind/        : byte-stable mirror of the records the frozen builder's own
                  discover_new() will produce inside build() for the same
                  records dir (same engine blob, same existing_keys).

Each record is written as <ARCH>-entry<N>-discovery.json (engine dict,
ensure_ascii=False, indent=2, trailing newline).  A deterministic
records-manifest.json hashes every file.  Read-only w.r.t. the game install.
"""

import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile

ENGINE_COMMIT = "204c97f0d1a6039860f49a9c4b9232c51ae8d8fa"
BUILDER_COMMIT = "6c47256be6f42b33826341bf217469be03d4c7ab"
ENGINE_REL = "tools/research/windows-static-archive/discovery_engine.py"
BUILDER_REL = "tools/research/windows-static-archive/qinghe_packet_builder.py"
SELECTOR_REL = "tools/research/windows-static-archive/narrative_holdout_selector.py"


def git_blob(commit, rel):
    return subprocess.run(
        ["git", "show", f"{commit}:{rel}"], capture_output=True, check=True
    ).stdout


def load_module_from_blob(commit, rel, name):
    blob = git_blob(commit, rel)
    fd, path = tempfile.mkstemp(suffix=".py")
    with os.fdopen(fd, "wb") as f:
        f.write(blob)
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod, hashlib.sha256(blob).hexdigest()


def dump_record(rec, out_dir, files):
    arch = rec["archive"].replace(".mpk", "")
    name = f"{arch}-entry{rec['entry_index']}-discovery.json"
    text = json.dumps(rec, ensure_ascii=False, indent=2) + "\n"
    with open(os.path.join(out_dir, name), "w", encoding="utf-8",
              newline="\n") as f:
        f.write(text)
    files[name] = hashlib.sha256(text.encode("utf-8")).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("archive_dir")
    ap.add_argument("--out", required=True)
    ap.add_argument("--engine-commit", default=ENGINE_COMMIT)
    ap.add_argument("--builder-commit", default=BUILDER_COMMIT)
    args = ap.parse_args()

    engine, engine_blob_sha = load_module_from_blob(
        args.engine_commit, ENGINE_REL, "frozen_engine_b")
    builder, builder_blob_sha = load_module_from_blob(
        args.builder_commit, BUILDER_REL, "frozen_builder_b")
    selector, selector_blob_sha = load_module_from_blob(
        args.builder_commit, SELECTOR_REL, "frozen_selector_b")
    if builder.ENGINE_COMMIT != args.engine_commit:
        raise SystemExit("FAIL: builder blob ENGINE_COMMIT != declared engine commit")

    game_version = open(
        os.path.join(args.archive_dir, "patching_version.txt"),
        encoding="utf-8").read().strip()
    if not game_version or game_version == "UNKNOWN":
        raise SystemExit("FAIL: game_version unavailable (fail closed)")

    for sub in ("regression", "holdout-json", "blind"):
        os.makedirs(os.path.join(args.out, sub), exist_ok=True)
    files = {}
    failures = []

    def run_engine(arch, idx, check_sha):
        if check_sha:
            try:
                r = engine.discover(args.archive_dir, arch + ".mpk",
                                    arch + ".mpkinfo", idx, game_version,
                                    args.engine_commit, None)
            except SystemExit as exc:
                return None, str(exc)
        else:
            r = engine.discover(args.archive_dir, arch + ".mpk",
                                arch + ".mpkinfo", idx, game_version,
                                args.engine_commit, None)
        got = r.get("extractor_source_sha256")
        if got != engine_blob_sha:
            raise SystemExit(
                f"FAIL: engine source sha mismatch on {arch}[{idx}] "
                f"({got} != {engine_blob_sha})")
        return r, None

    # 1. regression records: frozen KNOWN entries re-run on the new snapshot.
    known = sorted(
        [(a, i) for a, idxs in builder.KNOWN.items() for i in idxs])
    for arch, idx in known:
        rec, err = run_engine(arch, idx, check_sha=True)
        if rec is None:
            failures.append({"category": "regression", "archive": arch,
                             "entry_index": idx, "error": err})
            continue
        dump_record(rec, os.path.join(args.out, "regression"), files)

    # 2. fresh holdout selection via the frozen selector, then engine records.
    holdout_manifest_path = os.path.join(args.out, "holdout-manifest.json")
    hm = selector.select(args.archive_dir, holdout_manifest_path)
    hm_bytes = open(holdout_manifest_path, "rb").read()
    files["holdout-manifest.json"] = hashlib.sha256(hm_bytes).hexdigest()
    holdout_keys = []
    for pool in ("holdout_a", "holdout_b"):
        for c in hm[pool]:
            holdout_keys.append((c["archive"], c["entry_index"]))
    for arch, idx in sorted(holdout_keys):
        rec, err = run_engine(arch, idx, check_sha=True)
        if rec is None:
            failures.append({"category": "holdout", "archive": arch,
                             "entry_index": idx, "error": err})
            continue
        dump_record(rec, os.path.join(args.out, "holdout-json"), files)

    # 3. blind mirror: discover_new with exactly the existing_keys build()
    #    will compute from this records dir (regression + holdout records).
    existing_keys = set(known) | set(holdout_keys)
    new_recs = builder.discover_new(
        args.archive_dir, args.engine_commit, args.builder_commit,
        game_version, existing_keys)
    for rec in new_recs:
        dump_record(rec, os.path.join(args.out, "blind"), files)

    manifest = {
        "schema": "hnex006r-records-manifest-1",
        "engine_commit": args.engine_commit,
        "engine_blob_sha256": engine_blob_sha,
        "builder_commit": args.builder_commit,
        "builder_blob_sha256": builder_blob_sha,
        "selector_commit": args.builder_commit,
        "selector_blob_sha256": selector_blob_sha,
        "selector_manifest_schema": hm["schema_version"],
        "game_version": game_version,
        "archive_dir": os.path.abspath(args.archive_dir),
        "regression_entries": [
            {"archive": a, "entry_index": i} for a, i in known],
        "holdout_entries": [
            {"archive": a, "entry_index": i} for a, i in sorted(holdout_keys)],
        "blind_count": len(new_recs),
        "failures": failures,
        "files": dict(sorted(files.items())),
    }
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"))
    manifest["manifest_sha256"] = hashlib.sha256(
        canonical.encode("utf-8")).hexdigest()
    with open(os.path.join(args.out, "records-manifest.json"), "w",
              encoding="utf-8", newline="\n") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")

    out = (
        f"regression={len(known) - len([x for x in failures if x['category'] == 'regression'])}/{len(known)} "
        f"holdout={len(holdout_keys) - len([x for x in failures if x['category'] == 'holdout'])}/{len(holdout_keys)} "
        f"blind={len(new_recs)} failures={len(failures)}\n"
        f"records_manifest_sha256={manifest['manifest_sha256']}\n"
    )
    sys.stdout.buffer.write(out.encode("utf-8"))
    for x in failures:
        sys.stdout.buffer.write(
            f"  FAILURE {x['category']} {x['archive']}[{x['entry_index']}]: "
            f"{x['error']}\n".encode("utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
