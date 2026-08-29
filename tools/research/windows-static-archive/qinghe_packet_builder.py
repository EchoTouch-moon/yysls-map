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
import subprocess
import sys

LUA_SIG = b"\x1bLua"
LUAC_DATA_STD = bytes([0x19, 0x93, 0x0D, 0x0A, 0x1A, 0x0A])
MAX_LOCATOR_BYTES = 64
PACKET_SCHEMA = "qinghe-evidence-packet-1"
MANIFEST_SCHEMA = "nex005-selection-manifest-1"
ENGINE_COMMIT = "204c97f0d1a6039860f49a9c4b9232c51ae8d8fa"
ARCHIVES = ["LT71", "LT51", "LT31"]
SELECT_N = 12
CLUSTER_OBS_CAP = 60
MAX_CLUSTER_ENTRIES = 5

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
    # An unsigned Lua varint must terminate with a byte carrying 0x80.
    # Reaching the width limit without that marker is malformed input.
    return None, None


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


def sub_split_key(record):
    """Deterministic sub-split key: cleaned source directory after
    'storyline_data/' (only [A-Za-z0-9_/.-], collapsed slashes)."""
    import re as _re
    loc = record["container"].get("source_locator") or ""
    marker = "storyline_data/"
    if marker in loc:
        rest = loc.split(marker, 1)[1]
        parts = rest.split("/")
        if len(parts) >= 2:
            key = "/".join(parts[:-1])
        else:
            key = parts[0]
    else:
        key = loc
    cleaned = _re.sub(r"[^A-Za-z0-9_/.-]", "", key)
    cleaned = _re.sub(r"/{2,}", "/", cleaned).strip("/")
    return cleaned or "unclassified"


def _chunk(members, base_id):
    """Deterministically split members into chunks of <= MAX_CLUSTER_ENTRIES."""
    if len(members) <= MAX_CLUSTER_ENTRIES:
        return [(base_id, members)]
    out = []
    for i in range(0, len(members), MAX_CLUSTER_ENTRIES):
        suffix = "" if i == 0 else f"#{i // MAX_CLUSTER_ENTRIES + 1}"
        out.append((f"{base_id}{suffix}", members[i:i + MAX_CLUSTER_ENTRIES]))
    return out


def cluster_entries(selected):
    """Priority assignment + §3a sub-split / fallback / merge rules.
    Every resulting cluster carries <= MAX_CLUSTER_ENTRIES entries."""
    clusters = {cid: [] for cid, _ in CLUSTER_ORDER}
    others = []
    for s, size, h, r, reasons in selected:
        placed = False
        for cid, pred in CLUSTER_ORDER:
            if pred(r):
                clusters[cid].append((r, reasons))
                placed = True
                break
        if not placed:
            others.append((r, reasons))
    # §3a.a: sub-split any cluster with >5 entries by source sub-path,
    # then chunk any group still over the cap (same sub-path can exceed it).
    final = {}
    for cid, members in clusters.items():
        if not members:
            continue
        groups = [(cid, members)]
        if len(members) > MAX_CLUSTER_ENTRIES:
            by_key = {}
            for m in members:
                key = sub_split_key(m[0]) or cid
                by_key.setdefault(key, []).append(m)
            groups = [(f"{cid}/{key}" if key != cid else cid, group)
                      for key, group in
                      sorted(by_key.items(), key=lambda kv: (-len(kv[1]), kv[0]))]
        for gid, group in groups:
            for cid2, chunk in _chunk(group, gid):
                final[cid2] = chunk
    # §3a.b: fallback OTHER (chunked too)
    if others:
        for cid, chunk in _chunk(others, "OTHER"):
            final[cid] = chunk
    # §3a.c: merge smallest into FAMILY_ST until <=8 clusters total;
    # re-chunk afterwards so the merged cluster also respects the cap.
    if len(final) > 8:
        fam_st = []
        for cid in [c for c in final
                    if c == "FAMILY_ST" or c.startswith("FAMILY_ST#")]:
            fam_st += final.pop(cid)
        while len(final) >= 8:
            smallest = min(final.items(), key=lambda kv: len(kv[1]))[0]
            fam_st += final.pop(smallest)
        for cid, chunk in _chunk(fam_st, "FAMILY_ST"):
            final[cid] = chunk
    over = {cid: len(m) for cid, m in final.items()
            if len(m) > MAX_CLUSTER_ENTRIES}
    if over:
        raise SystemExit(f"FAIL: cluster cap ({MAX_CLUSTER_ENTRIES}) "
                         f"violated: {over}")
    return final


def locator_bytes(value, cap=MAX_LOCATOR_BYTES):
    """UTF-8-safe byte cap (same contract as NEX-004A): encode -> cap at
    `cap` bytes -> trim incomplete trailing codepoint.  Returns (str, truncated)."""
    b = value.encode("utf-8")
    if len(b) <= cap:
        return value, False
    b = b[:cap]
    while b and (b[-1] & 0xC0) == 0x80:
        b = b[:-1]
    if b and b[-1] >= 0xC0:
        b = b[:-1]
    return b.decode("utf-8", errors="replace"), True


def verify_identity(selected, expected_engine):
    """H1/H2: verify builder-vs-extractor identity and per-record consistency.
    FAIL CLOSED unless: all selected records share one extractor_commit ==
    expected_engine and one extractor_source_sha256; per-entry metadata and
    block hash match the source record."""
    commits = {}
    srcs = {}
    for s, size, h, r, reasons in selected:
        c = r.get("extractor_commit")
        e = r.get("extractor_source_sha256")
        if not c or not e:
            raise SystemExit(f"FAIL: record {r['archive']}[{r['entry_index']}] "
                             "missing extractor identity")
        commits.setdefault(c, []).append(f"{r['archive']}[{r['entry_index']}]")
        srcs.setdefault(e, []).append(f"{r['archive']}[{r['entry_index']}]")
        # H2: per-entry block hash is taken from the record itself (no
        # aggregated trust); assert the archive/index fields are present.
        arch = r["archive"].replace(".mpk", "")
        if arch not in ("LT71", "LT51", "LT31"):
            raise SystemExit(f"FAIL: unexpected archive {r['archive']}")
        if not (0 <= r["entry_index"] < 100000):
            raise SystemExit("FAIL: entry_index out of range")
        if len(r.get("block_sha256", "")) != 64:
            raise SystemExit("FAIL: block_sha256 missing/malformed")
    if len(commits) != 1:
        raise SystemExit(f"FAIL: extractor_commit inconsistent across records: {commits}")
    engine_commit, _ = commits.popitem()
    if engine_commit != expected_engine:
        raise SystemExit(f"FAIL: extractor_commit {engine_commit} != {expected_engine}")
    if len(srcs) != 1:
        raise SystemExit(f"FAIL: extractor_source_sha256 inconsistent across records: {srcs}")
    engine_src, _ = srcs.popitem()
    return engine_commit, engine_src


def build(archive_dir, records_dirs, out_dir, engine_commit, builder_commit,
          game_version):
    verify_builder_identity(builder_commit)
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
    # H1: verify builder-vs-extractor identity (fail closed)
    verified_engine, verified_engine_src = verify_identity(selected, ENGINE_COMMIT)
    if verified_engine != engine_commit:
        raise SystemExit("FAIL: engine commit mismatch (record identity != arg)")
    # H2: substantive re-verification against the current archive state
    verify_provenance(selected, archive_dir, game_version)
    verify_extractor_blob(verified_engine, verified_engine_src)

    # clustering with §3a rules
    clusters = cluster_entries(selected)
    cluster_list = []
    for cid, members in clusters.items():
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
                short, trunc = locator_bytes(src["source_locator"])
                src_obs.append({"archive": r["archive"],
                                "entry_index": r["entry_index"],
                                "source_status": src.get("source_status"),
                                "source_locator": short,
                                "source_truncated": trunc,
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
                "builder_source_sha256": _src_sha(),
                "extractor_commit": verified_engine,
                "extractor_source_sha256": verified_engine_src,
                "game_version": game_version,
            },
            "warnings": sorted(warnings),
            "unresolved": unresolved,
        })
    if not 5 <= len(cluster_list) <= 8:
        counts = {c["cluster_id"]: len(c["entries"]) for c in cluster_list}
        raise SystemExit(f"FAIL: cluster count {len(cluster_list)} not in [5,8] "
                         f"(counts={counts})")

    manifest = {
        "schema_version": MANIFEST_SCHEMA,
        "builder_commit": builder_commit,
        "builder_source_sha256": _src_sha(),
        "extractor_commit": verified_engine,
        "extractor_source_sha256": verified_engine_src,
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
        "builder_source_sha256": _src_sha(),
        "extractor_commit": verified_engine,
        "extractor_source_sha256": verified_engine_src,
        "game_version": game_version,
        "selection_policy_ref": "docs/research/evidence/windows/wave-1.6/nex005-qinghe-packet/packet-policy.md",
        "clusters": cluster_list,
        "provenance": {
            "builder_commit": builder_commit,
            "builder_source_sha256": _src_sha(),
            "extractor_commit": verified_engine,
            "extractor_source_sha256": verified_engine_src,
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


def _git_file_sha(commit, abspath):
    """Return the SHA-256 of `abspath` as of `commit`, or fail closed."""
    rel = None
    try:
        root = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            check=True,
            text=True,
        ).stdout.strip()
        rel = os.path.relpath(abspath, root).replace(os.sep, "/")
        blob = subprocess.run(
            ["git", "show", f"{commit}:{rel}"],
            capture_output=True,
            check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        raise SystemExit(f"FAIL: source blob unavailable at {commit}:{rel}") from exc
    return hashlib.sha256(blob).hexdigest()


def _git_source_sha(commit):
    """Return the SHA-256 of this file at `commit`, or fail closed."""
    return _git_file_sha(commit, os.path.abspath(__file__))


def sha256_stream(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def verify_provenance(selected, archive_dir, game_version):
    """Substantive re-verification against archive_dir (fail closed).

    Every selected record must match the CURRENT archive state: game_version,
    mpkinfo/archive file digests, per-entry metadata (offset/size/flags) and
    the block SHA-256 recomputed from the archive.  Records generated before
    a baseline drift are rejected here, not repackaged."""
    digests = {}
    infos = {}
    for _s, _size, _h, r, _reasons in selected:
        arch = r["archive"].replace(".mpk", "")
        idx = r["entry_index"]
        tag = f"{arch}[{idx}]"
        if r.get("game_version") != game_version:
            raise SystemExit(
                f"FAIL: {tag} game_version {r.get('game_version')!r} != "
                f"current {game_version!r} (stale record; regenerate)")
        mpkinfo_path = os.path.join(archive_dir, arch + ".mpkinfo")
        archive_path = os.path.join(archive_dir, arch + ".mpk")
        if arch not in digests:
            if not (os.path.isfile(mpkinfo_path) and os.path.isfile(archive_path)):
                raise SystemExit(f"FAIL: archive files missing for {arch} in {archive_dir}")
            head = open(mpkinfo_path, "rb").read(8)
            if len(head) != 8:
                raise SystemExit(f"FAIL: mpkinfo truncated for {arch}")
            version, count = struct.unpack("<II", head)
            if version != 3 or os.path.getsize(mpkinfo_path) != 8 + count * 20 + 16:
                raise SystemExit(f"FAIL: mpkinfo invariant failed for {arch}")
            infos[arch] = (mpkinfo_path, count)
            digests[arch] = {"mpkinfo": sha256_stream(mpkinfo_path),
                             "archive": sha256_stream(archive_path)}
        if r.get("mpkinfo_sha256") != digests[arch]["mpkinfo"]:
            raise SystemExit(f"FAIL: {tag} mpkinfo_sha256 mismatch "
                             "(archive drifted; regenerate records)")
        if r.get("archive_sha256") != digests[arch]["archive"]:
            raise SystemExit(f"FAIL: {tag} archive_sha256 mismatch "
                             "(archive drifted; regenerate records)")
        mpkinfo_path, count = infos[arch]
        e = entry_metadata(mpkinfo_path, idx, count)
        if e is None:
            raise SystemExit(f"FAIL: {tag} entry metadata unavailable")
        if (e["offset"], e["size"], e["flags"]) != (
                r["entry_offset"], r["entry_stored_size"], r["flags_raw"]):
            raise SystemExit(f"FAIL: {tag} entry metadata mismatch "
                             "(index drifted; regenerate records)")
        blk = block_of(archive_path, e)
        if blk is None:
            raise SystemExit(f"FAIL: {tag} block read failed")
        if hashlib.sha256(blk).hexdigest() != r.get("block_sha256"):
            raise SystemExit(f"FAIL: {tag} block_sha256 mismatch")


def verify_extractor_blob(engine_commit, expected_sha):
    """Verify the extractor source blob at engine_commit hashes to the
    recorded extractor_source_sha256 (not merely 64 hex chars)."""
    engine_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "discovery_engine.py")
    if _git_file_sha(engine_commit, engine_path) != expected_sha:
        raise SystemExit(f"FAIL: extractor blob at {engine_commit} != "
                         "recorded extractor_source_sha256")


def verify_builder_identity(builder_commit):
    """Reject packets whose declared commit does not contain this source."""
    expected = _git_source_sha(builder_commit)
    actual = _src_sha()
    if expected != actual:
        raise SystemExit(
            "FAIL: builder source differs from declared commit "
            f"{builder_commit} (expected {expected}, current {actual})"
        )


def selftest():
    assert load_unsigned(bytes([1] * 8), 0) == (None, None)
    assert family_of("@hexm/client/storyline_data/x.lua") == "storyline_data"
    assert family_of("@hexm/client/storyline_data/wanfa/MSD_ST/ZDQ/dq_610900.lua") == "MSD_ST"
    assert qinghe_of("@hexm/client/storyline_data/guanqia/qinghe_end_task/_200443.lua")
    assert not qinghe_of("@hexm/client/ui/common.lua")
    # H3: UTF-8 byte cap
    v, t = locator_bytes("汉" * 40)
    assert t and len(v.encode("utf-8")) <= MAX_LOCATOR_BYTES and v == "汉" * 21
    v2, t2 = locator_bytes("@hexm/client/storyline_data/guanqia/qinghe_end_task/_200443.lua")
    assert not t2
    # H1: identity verification fail-closed on inconsistent commits
    recs_ok = [
        (0, 0, "", {"archive": "LT71", "entry_index": 1,
                    "extractor_commit": "204c97f0d1a6039860f49a9c4b9232c51ae8d8fa",
                    "extractor_source_sha256": "a" * 64, "block_sha256": "b" * 64}, []),
        (0, 0, "", {"archive": "LT71", "entry_index": 2,
                    "extractor_commit": "204c97f0d1a6039860f49a9c4b9232c51ae8d8fa",
                    "extractor_source_sha256": "a" * 64, "block_sha256": "c" * 64}, []),
    ]
    c, s = verify_identity(recs_ok, "204c97f0d1a6039860f49a9c4b9232c51ae8d8fa")
    assert c == "204c97f0d1a6039860f49a9c4b9232c51ae8d8fa" and s == "a" * 64
    recs_bad = [dict(r) for _, _, _, r, _ in recs_ok]
    recs_bad[1]["extractor_source_sha256"] = "d" * 64
    try:
        verify_identity([(0, 0, "", recs_bad[0], []), (0, 0, "", recs_bad[1], [])],
                        "204c97f0d1a6039860f49a9c4b9232c51ae8d8fa")
        raise AssertionError("expected SystemExit")
    except SystemExit:
        pass

    def qh_rec(i):
        return {"archive": "LT71", "entry_index": i, "entry_offset": 0,
                "entry_stored_size": 100, "flags_raw": 0,
                "container": {"source_locator":
                              "@hexm/client/storyline_data/wanfa/MSD_ST/ZDQ/dq_1.lua"},
                "observations": [{"pattern_kind": "REGION_REF_CANDIDATE",
                                  "raw_value": "EXPANSION_QINGHE",
                                  "byte_offset": 0}],
                "warnings": []}

    def plain_rec(i):
        return {"archive": "LT71", "entry_index": 100 + i, "entry_offset": 0,
                "entry_stored_size": 100, "flags_raw": 0,
                "container": {"source_locator": f"@hexm/client/ui/common_{i}.lua"},
                "observations": [], "warnings": []}

    # cluster cap: reviewer repro — 6 QH_EXPANSION sharing one sub-path
    # plus 4 singletons must NOT pass as [6,1,1,1,1].
    sel = [(0, 100, "", qh_rec(i), []) for i in range(6)] + \
          [(0, 100, "", plain_rec(i), []) for i in range(4)]
    got = cluster_entries(sel)
    sizes = sorted(len(v) for v in got.values())
    assert all(s <= MAX_CLUSTER_ENTRIES for s in sizes), sizes
    assert sum(sizes) == 10, sizes
    assert sizes == [1, 4, 5], sizes

    # verify_provenance on a synthetic archive dir
    import tempfile
    block = b"BLKDATA"
    mpkinfo_bytes = struct.pack("<II", 3, 1) + \
        struct.pack("<IIIII", 0xAA, 0xBB, 0, len(block), 7) + b"\x00" * 16
    mpk_bytes = block
    rec_ok = {"archive": "LT31.mpk", "entry_index": 0, "entry_offset": 0,
              "entry_stored_size": len(block), "flags_raw": 7,
              "block_sha256": hashlib.sha256(block).hexdigest(),
              "mpkinfo_sha256": hashlib.sha256(mpkinfo_bytes).hexdigest(),
              "archive_sha256": hashlib.sha256(mpk_bytes).hexdigest(),
              "game_version": "V1"}
    with tempfile.TemporaryDirectory() as td:
        open(os.path.join(td, "LT31.mpkinfo"), "wb").write(mpkinfo_bytes)
        open(os.path.join(td, "LT31.mpk"), "wb").write(mpk_bytes)
        verify_provenance([(0, 0, "", rec_ok, [])], td, "V1")
        for bad, gv in [(dict(rec_ok, block_sha256="0" * 64), "V1"),
                        (dict(rec_ok, entry_offset=1), "V1"),
                        (dict(rec_ok, mpkinfo_sha256="1" * 64), "V1"),
                        (dict(rec_ok), "V2")]:
            try:
                verify_provenance([(0, 0, "", bad, [])], td, gv)
                raise AssertionError("expected SystemExit")
            except SystemExit:
                pass
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
