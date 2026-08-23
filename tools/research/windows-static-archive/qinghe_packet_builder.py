#!/usr/bin/env python3
"""
qinghe_packet_builder.py — NEX-005: Qinghe Structural Evidence Packet builder.

Builds a bounded, provenance-complete Qinghe native structural evidence packet
for NEX-006 Mac reconciliation, using the frozen observation engine (204c97f).

Frozen policy: see docs/.../nex005-qinghe-packet/packet-policy.md (P0).
  * candidate pool: 4 pilots + 12 holdout records + Qinghe-source scan
    (source contains qinghe/QINGHE/清河) + large family (>=8000B, top 4).
  * priority scoring and clustering per the frozen policy.
  * NOT a blind benchmark: Qinghe/narrative candidate signals are allowed as
    priority ONLY — never interpreted as canonical facts.
  * copyright: MAX_LOCATOR_BYTES=64, bounded observations, no dialogue/prose,
    no scripts/assets committed.

Usage:
    python qinghe_packet_builder.py --selftest
    python qinghe_packet_builder.py <archive_dir> --records-dir <dir> --out <dir>
                                    --commit <engine_commit> --builder-commit <p0sha>
"""
import argparse
import hashlib
import json
import os
import struct
import sys

LUA_SIG = b"\x1bLua"
LUAC_DATA_STD = bytes([0x19, 0x93, 0x0D, 0x0A, 0x1A, 0x0A])
MAX_LOCATOR_BYTES = 64
PACKET_SCHEMA = "qinghe-evidence-packet-1"
MANIFEST_SCHEMA = "nex005-selection-manifest-1"
ENGINE_COMMIT = "204c97f0d1a6039860f49a9c4b9232c51ae8d8fa"
ARCHIVES = ["LT71", "LT51", "LT31"]
SELECT_N = 16
CLUSTER_OBS_CAP = 60

KNOWN = {
    "LT71": [1768, 1631],
    "LT51": [1178],
    "LT31": [874],
}
HOLDOUT = [
    ("LT31", 1087), ("LT51", 1280), ("LT51", 1272), ("LT71", 2471),
    ("LT71", 2415), ("LT71", 886), ("LT31", 1702), ("LT31", 2382),
    ("LT31", 1583), ("LT71", 1068), ("LT31", 659), ("LT71", 824),
]

QINGHE_SUBSTRINGS = ("qinghe", "QINGHE", "清河")
CLUSTER_ORDER = [
    ("QH_EXPANSION", lambda r: any(o["pattern_kind"] == "REGION_REF_CANDIDATE" and "EXPANSION" in o["raw_value"] for o in r["observations"])),
    ("QH_SOURCE", lambda r: any(s in (r["container"].get("source_locator") or "") for s in QINGHE_SUBSTRINGS)),
    ("TASK_DQ", lambda r: any(o["pattern_kind"] == "TASK_REF_CANDIDATE" for o in r["observations"])),
    ("NODE_GRAPH", lambda r: any(o["raw_value"] == "NodeGraphData" for o in r["observations"])),
    ("CJK_TERM", lambda r: any(o["pattern_kind"] == "SHORT_CJK_TERM_CANDIDATE" for o in r["observations"])),
    ("NUM_REF", lambda r: any(o["pattern_kind"] == "TEXT_REF_CANDIDATE" for o in r["observations"])),
    ("FAMILY_MSD", lambda r: "MSD_ST" in (r["container"].get("source_locator") or "")),
    ("FAMILY_ST", lambda r: "storyline_data" in (r["container"].get("source_locator") or "")),
]


def load_unsigned(data, off):
    x = 0
    i = 0
    while i < 8:
        if off + i >= len(data):
            return None, None
        b = data[off + i]
        x = (x << 7) | (b & 0x7F)
        i += 1
        if b & 0x80:
            return x, i
    return x, i


def source_of(blk):
    L, n = load_unsigned(blk, 0x20)
    if L is None or L < 2:
        return None
    slen = L - 1
    src = blk[0x21:0x21 + slen]
    if len(src) != slen:
        return None
    return src.decode("utf-8", errors="replace")


def family_of(src):
    if not src:
        return None
    if "MSD_ST" in src:
        return "MSD_ST"
    if "storyline_data" in src:
        return "storyline_data"
    return None


def qinghe_of(src):
    return any(s in src for s in QINGHE_SUBSTRINGS) if src else False


def entry_metadata(mpkinfo_path, index, count):
    if not (0 <= index < count):
        return None
    with open(mpkinfo_path, "rb") as f:
        f.seek(8 + index * 20)
        raw = f.read(20)
    if len(raw) != 20:
        return None
    f0, f1, off, size, flags = struct.unpack("<IIIII", raw)
    return {"offset": off, "size": size, "flags": flags}


def block_of(archive_path, e):
    if e["offset"] + e["size"] > os.path.getsize(archive_path):
        return None
    with open(archive_path, "rb") as f:
        f.seek(e["offset"])
        blk = f.read(e["size"])
    return blk if len(blk) == e["size"] else None


def load_existing(records_dirs):
    """Load processed records from one or more records dirs
    (each may contain regression/ and/or holdout-json/ subdirs)."""
    recs = []
    for rd in records_dirs:
        for sub in ("regression", "holdout-json"):
            d = os.path.join(rd, sub)
            if not os.path.isdir(d):
                continue
            for f in sorted(os.listdir(d)):
                if f.endswith(".json"):
                    recs.append(json.load(open(os.path.join(d, f), encoding="utf-8")))
    return recs


def discover_new(archive_dir, engine_commit, builder_commit, game_version):
    """Find + run the frozen engine on new candidates (qinghe-source + large family)."""
    import discovery_engine as de
    new = []
    scanned_keys = set()
    for arch in ARCHIVES:
        mpkinfo_path = os.path.join(archive_dir, arch + ".mpkinfo")
        archive_path = os.path.join(archive_dir, arch + ".mpk")
        head = open(mpkinfo_path, "rb").read(8)
        version, count = struct.unpack("<II", head)
        if version != 3:
            continue
        for idx in range(count):
            if (arch, idx) in scanned_keys:
                continue
            e = entry_metadata(mpkinfo_path, idx, count)
            if e is None:
                continue
            blk = block_of(archive_path, e)
            if blk is None:
                continue
            sig = blk.find(LUA_SIG)
            if sig < 0 or blk[sig + 4] != 0x54:
                continue
            src = source_of(blk)
            fam = family_of(src)
            if fam is None:
                continue
            scanned_keys.add((arch, idx))
            qh = qinghe_of(src)
            if qh or e["size"] >= 8000:
                new.append({"archive": arch, "index": idx, "size": e["size"],
                            "offset": e["offset"], "flags": e["flags"],
                            "family": fam, "qinghe": qh})
    # frozen policy: pool = all Qinghe-source + TOP 4 large-family (size desc,
    # sha256 tie-break)
    qh_all = [c for c in new if c["qinghe"]]
    large_only = [c for c in new if not c["qinghe"]]
    large_only.sort(key=lambda x: (-x["size"],
                                   hashlib.sha256(f"{x['archive']}:{x['index']}".encode()).hexdigest()))
    to_run = qh_all + large_only[:4]
    # run engine on new candidates
    recs = []
    for c in sorted(to_run, key=lambda x: (-x["size"], x["archive"], x["index"])):
        r = de.discover(archive_dir, c["archive"] + ".mpk",
                        c["archive"] + ".mpkinfo", c["index"], game_version,
                        engine_commit, None)
        recs.append(r)
    return recs


def score_record(r):
    src = r["container"].get("source_locator") or ""
    obs = r.get("observations", [])
    s = 0
    reasons = []
    if qinghe_of(src) or any(o["pattern_kind"] == "REGION_REF_CANDIDATE" and "EXPANSION" in o["raw_value"] for o in obs):
        s += 4
        reasons.append("Qinghe signal (source/EXPANSION)")
    dq = [o["raw_value"] for o in obs if o["pattern_kind"] == "TASK_REF_CANDIDATE"]
    if dq:
        s += 3
        reasons.append(f"dq_ TASK_REF ({','.join(dq[:3])})")
    if any(o["raw_value"] == "NodeGraphData" for o in obs):
        s += 2
        reasons.append("NodeGraphData observation")
    cjk = [o["raw_value"] for o in obs if o["pattern_kind"] == "SHORT_CJK_TERM_CANDIDATE"]
    if cjk:
        s += 2
        reasons.append(f"SHORT_CJK ({','.join(cjk[:3])})")
    if any(o["pattern_kind"] == "TEXT_REF_CANDIDATE" for o in obs):
        s += 1
        reasons.append("numeric TEXT_REF")
    if "MSD_ST" in src:
        s += 1
        reasons.append("family MSD_ST")
    if r["entry_stored_size"] >= 8000:
        s += 1
        reasons.append("stored_size >= 8KB")
    return s, reasons


def build(archive_dir, records_dirs, out_dir, engine_commit, builder_commit,
          game_version):
    existing = load_existing(records_dirs)
    new = discover_new(archive_dir, engine_commit, builder_commit, game_version)
    all_recs = existing + new
    scored = []
    for r in all_recs:
        s, reasons = score_record(r)
        key = f"{r['archive']}:{r['entry_index']}"
        h = hashlib.sha256(key.encode()).hexdigest()
        scored.append((s, r["entry_stored_size"], h, r, reasons))
    scored.sort(key=lambda x: (-x[0], -x[1], x[2]))
    selected = scored[:SELECT_N]
    if len(selected) < 12:
        raise SystemExit(f"FAIL: only {len(selected)} candidates (need >= 12)")

    # clustering
    clusters = {cid: [] for cid, _ in CLUSTER_ORDER}
    for s, size, h, r, reasons in selected:
        for cid, pred in CLUSTER_ORDER:
            if pred(r):
                clusters[cid].append((r, reasons))
                break
    cluster_list = []
    for cid, members in clusters.items():
        if not members:
            continue
        entries = []
        obs_all = []
        src_obs = []
        families = set()
        warnings = set()
        for r, reasons in members:
            entries.append({
                "archive": r["archive"], "entry_index": r["entry_index"],
                "entry_offset": r["entry_offset"],
                "stored_size": r["entry_stored_size"],
                "block_sha256": r["block_sha256"],
            })
            src = r["container"]
            if src.get("source_locator"):
                short = src["source_locator"][:MAX_LOCATOR_BYTES]
                src_obs.append({"archive": r["archive"],
                                "entry_index": r["entry_index"],
                                "source_status": src.get("source_status"),
                                "source_locator": short,
                                "source_reconstruction": src.get("source_reconstruction")})
            for o in r.get("observations", []):
                obs_all.append(o)
            fam = "MSD_ST" if "MSD_ST" in (src.get("source_locator") or "") else ("storyline_data" if "storyline_data" in (src.get("source_locator") or "") else None)
            if fam:
                families.add(fam)
            warnings.update(r.get("warnings", []))
        obs_all.sort(key=lambda o: (o["byte_offset"], o["raw_value"]))
        obs_all = obs_all[:CLUSTER_OBS_CAP]
        unresolved = [
            "SEMANTIC_ROLE_UNVERIFIED: all structural observations are candidates, not canonical facts",
            "CONSTANT_OWNERSHIP_UNKNOWN: framing_tag_raw is a raw byte, not a Lua constant tag",
            "PROTO_OWNERSHIP_UNKNOWN: no owning proto / constant index assigned",
        ]
        cluster_list.append({
            "cluster_id": cid,
            "selection_reasons": sorted({rr for _, rrs in members for rr in rrs}),
            "source_families": sorted(families),
            "entries": entries,
            "source_observations": src_obs,
            "structural_observations": obs_all,
            "provenance": {
                "builder_commit": builder_commit,
                "extractor_commit": engine_commit,
                "game_version": game_version,
                "extractor_source_sha256": _src_sha(),
            },
            "warnings": sorted(warnings),
            "unresolved": unresolved,
        })
    if not 5 <= len(cluster_list) <= 8:
        raise SystemExit(f"FAIL: cluster count {len(cluster_list)} not in [5,8]")

    manifest = {
        "schema_version": MANIFEST_SCHEMA,
        "builder_commit": builder_commit,
        "extractor_commit": engine_commit,
        "game_version": game_version,
        "selection_count": len(selected),
        "entries": [{
            "archive": r["archive"], "entry_index": r["entry_index"],
            "entry_offset": r["entry_offset"], "stored_size": r["entry_stored_size"],
            "flags_raw": r["flags_raw"], "score": s,
            "selection_reasons": reasons,
        } for s, size, h, r, reasons in selected],
    }
    packet = {
        "schema_version": PACKET_SCHEMA,
        "builder_commit": builder_commit,
        "extractor_commit": engine_commit,
        "game_version": game_version,
        "selection_policy_ref": "docs/research/evidence/windows/wave-1.6/nex005-qinghe-packet/packet-policy.md",
        "clusters": cluster_list,
        "provenance": {
            "builder_commit": builder_commit,
            "extractor_commit": engine_commit,
            "game_version": game_version,
        },
        "warnings": [
            "INSTRUCTION_SERIALIZATION_VARIANT",
            "SEMANTIC_ROLE_UNVERIFIED",
            "CANONICAL: NONE — packet is structural evidence only",
        ],
        "unresolved": [
            "No canonical mapping, confirmed character identity, or quest title assignment",
            "Qinghe/narrative signals are candidates (priority), not truths",
        ],
    }
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "selection-manifest.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        f.write("\n")
    with open(os.path.join(out_dir, "qinghe-evidence-packet.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(packet, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return manifest, packet


def _src_sha():
    with open(os.path.abspath(__file__), "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def selftest():
    assert family_of("@hexm/client/storyline_data/x.lua") == "storyline_data"
    assert family_of("@hexm/client/storyline_data/wanfa/MSD_ST/ZDQ/dq_610900.lua") == "MSD_ST"
    assert qinghe_of("@hexm/client/storyline_data/guanqia/qinghe_end_task/_200443.lua")
    assert not qinghe_of("@hexm/client/ui/common.lua")
    return True


def main(argv=None):
    ap = argparse.ArgumentParser(description="NEX-005 Qinghe evidence packet builder")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--records-dir", action="append", default=[], required=False)
    ap.add_argument("--out", required=False)
    ap.add_argument("--commit", default=ENGINE_COMMIT)
    ap.add_argument("--builder-commit", default=None)
    ap.add_argument("archive_dir", nargs="?")
    args = ap.parse_args(argv)
    if args.selftest:
        selftest()
        print("selftest PASS")
        return 0
    if not (args.archive_dir and args.records_dir and args.out):
        ap.error("archive_dir --records-dir --out required (or --selftest)")
    game_version = None
    vf = os.path.join(args.archive_dir, "patching_version.txt")
    try:
        game_version = open(vf, encoding="utf-8").read().strip()
    except OSError:
        pass
    if not game_version or game_version == "UNKNOWN":
        raise SystemExit("FAIL: game_version unavailable")
    builder_commit = args.builder_commit
    if builder_commit is None:
        import subprocess
        try:
            builder_commit = subprocess.run(["git", "rev-parse", "HEAD"],
                                            capture_output=True, text=True,
                                            check=True).stdout.strip()
        except Exception:
            builder_commit = None
    if not builder_commit:
        raise SystemExit("FAIL: builder commit unavailable")
    manifest, packet = build(args.archive_dir, args.records_dir, args.out,
                             args.commit, builder_commit, game_version)
    print(f"manifest: {len(manifest['entries'])} entries; "
          f"packet: {len(packet['clusters'])} clusters")
    return 0


if __name__ == "__main__":
    sys.exit(main())
