#!/usr/bin/env python3
"""H-NEX-006R read-only baseline census of the Windows install.

Census scope (frozen by the H-NEX-006R contract):
  * Core toolchain inputs get SHA-256 + size + mtime:
      Patch/patching_version.txt
      Patch/LT31.mpk, LT31.mpkinfo, LT51.mpk, LT51.mpkinfo, LT71.mpk, LT71.mpkinfo
  * Every other file directly under the Patch dir gets path/size/mtime
    (no hashing -- many are multi-GB patch blobs the frozen engine never reads).

Deterministic: entries sorted by relative path; manifest_sha256 hashes the
canonical JSON (exclude_keys=["census_id","timestamp"]) so two censuses of an
unchanged tree produce the identical manifest hash.

Read-only: opens files in "rb" mode only; never writes to the game install.
"""

import argparse
import datetime as _dt
import hashlib
import json
import os
import sys

CORE_FILES = [
    "patching_version.txt",
    "LT31.mpk",
    "LT31.mpkinfo",
    "LT51.mpk",
    "LT51.mpkinfo",
    "LT71.mpk",
    "LT71.mpkinfo",
]


def sha256_stream(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("patch_dir")
    ap.add_argument("--out", required=True, help="census JSON output path")
    ap.add_argument("--census-id", required=True)
    args = ap.parse_args()

    root = os.path.abspath(args.patch_dir)
    entries = []
    for name in sorted(os.listdir(root)):
        p = os.path.join(root, name)
        if not os.path.isfile(p):
            continue
        st = os.stat(p)
        rec = {
            "path": f"Patch/{name}",
            "size": st.st_size,
            "mtime_utc": _dt.datetime.fromtimestamp(
                st.st_mtime, tz=_dt.timezone.utc
            ).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        if name in CORE_FILES:
            rec["sha256"] = sha256_stream(p)
            rec["role"] = "core-input"
        else:
            rec["role"] = "metadata-only"
        entries.append(rec)

    pv_path = os.path.join(root, "patching_version.txt")
    with open(pv_path, "rb") as f:
        version_raw = f.read()

    manifest = {
        "census_id": args.census_id,
        "timestamp_utc": _dt.datetime.now(_dt.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
        "patch_dir": root,
        "patching_version": version_raw.decode("utf-8").strip(),
        "patching_version_sha256": hashlib.sha256(version_raw).hexdigest(),
        "files": entries,
    }
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    stable = {k: v for k, v in manifest.items() if k not in ("census_id", "timestamp_utc")}
    stable_json = json.dumps(stable, sort_keys=True, separators=(",", ":")).encode()
    manifest["manifest_sha256"] = hashlib.sha256(stable_json).hexdigest()
    manifest["core_sha256_set"] = {
        e["path"]: e["sha256"] for e in entries if e["role"] == "core-input"
    }

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
        f.write("\n")

    sys.stdout.buffer.write(
        (
            f"census_id={args.census_id}\n"
            f"manifest_sha256={manifest['manifest_sha256']}\n"
            f"patching_version={manifest['patching_version']}\n"
            f"files={len(entries)} core={len(manifest['core_sha256_set'])}\n"
        ).encode("utf-8")
    )
    for p in sorted(manifest["core_sha256_set"]):
        sys.stdout.buffer.write(f"  {p} {manifest['core_sha256_set'][p]}\n".encode())
    sys.stdout.buffer.write(
        f"full_sha256={hashlib.sha256(canonical).hexdigest()}\n".encode("utf-8")
    )


if __name__ == "__main__":
    main()
