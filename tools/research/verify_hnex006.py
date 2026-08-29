#!/usr/bin/env python3
"""Replay the Mac-side deterministic checks for H-NEX-006.

This verifier intentionally uses only repository state. Public-page content is
audited separately because live responses are not stable inputs, and Windows
native-owned evidence remains outside the Mac trust boundary.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any


BASE_COMMIT = "3c99afe530c277a72243c1bf89cf913719faffb9"
MAC_COMMIT = "cd50bd24779fd47b808bc270a12c617cd9977be9"
BUILDER_COMMIT = "6c47256be6f42b33826341bf217469be03d4c7ab"
EXTRACTOR_COMMIT = "204c97f0d1a6039860f49a9c4b9232c51ae8d8fa"
CANONICAL_SHA256 = "4b1919f0b8d86ffac66b77d0e2f02c9e1a824e02ecd9a87e170889c134ece1ec"
PACKET_SHA256 = "8c1e4b5ae6d05ef52ccdc3cb6412bb50007e1532f1bfe2aad174d3c7100ef9a7"
MANIFEST_SHA256 = "4d5a1397786be70c71b5ba81ea2282bfe4cf246d24ed3e01adc00ff3c5c80f9c"

MAC_FILES = (
    "docs/research/narrative/qinghe/README.md",
    "docs/research/narrative/qinghe/source-ledger.md",
    "docs/research/narrative/qinghe/main-story-inventory.md",
    "docs/research/narrative/qinghe/hidden-story-inventory.md",
    "docs/research/narrative/qinghe/unresolved-questions.md",
    "docs/research/narrative/qinghe/character-aliases.md",
    "docs/research/narrative/qinghe/interpretation/part-1-you-jian-xin-lai-yan.md",
)

EXACT_MAC_FILES = MAC_FILES[1:3] + MAC_FILES[4:]

CANONICAL_EXPECTED = {
    "wwm:qinghe:chapter-1:part-1": ("又见新来燕", "wwm:qinghe:chapter-1", 1),
    "wwm:qinghe:chapter-1:part-1:awaken": ("竹林旧居线索", "wwm:qinghe:chapter-1:part-1", 1),
    "wwm:qinghe:chapter-1:part-1:bridge": ("断桥", "wwm:qinghe:chapter-1:part-1", 2),
    "wwm:qinghe:chapter-1:part-1:archery": ("北竹林学射", "wwm:qinghe:chapter-1:part-1", 3),
    "wwm:qinghe:chapter-1:part-1:wilderness": ("百草野遇天涯客", "wwm:qinghe:chapter-1:part-1", 4),
    "wwm:qinghe:chapter-1:part-1:arena": ("将军祠擂台", "wwm:qinghe:chapter-1:part-1", 5),
}

EXPECTED_CLUSTERS = {
    "QH_SOURCE/guanqia/qinghe_end_task",
    "QH_SOURCE/guanqia/qinghe_end_task#2",
    "QH_SOURCE/guanqia/qinghe_end_boss_fight",
    "QH_SOURCE/guanqia/qinghe_end_boss_fight/bxx",
    "QH_SOURCE/task",
    "QH_SOURCE/task/lizehao",
    "NODE_GRAPH",
}

REPRESENTATIVE_OBSERVATIONS = (
    ("LT71.mpk", 502, "NodeGraphData", 941),
    ("LT51.mpk", 2597, "NodeGraphData", 526),
    ("LT71.mpk", 318, "NodeGraphData", 412),
    ("LT51.mpk", 86, "NodeGraphData", 337),
    ("LT51.mpk", 322, "NodeGraphData", 315),
    ("LT51.mpk", 322, "nodeID", 495),
    ("LT31.mpk", 2415, "NodeGraphData", 370),
    ("LT71.mpk", 1919, "NodeGraphData", 501),
    ("LT51.mpk", 2232, "NodeGraphData", 541),
    ("LT51.mpk", 2232, "autoStartList", 643),
    ("LT51.mpk", 1943, "NodeGraphData", 538),
    ("LT51.mpk", 1943, "nodeID", 808),
    ("LT31.mpk", 972, "NodeGraphData", 346),
    ("LT31.mpk", 972, "nodeID", 496),
    ("LT31.mpk", 972, "is_only_once", 574),
    ("LT71.mpk", 1248, "小稞", 1794),
    ("LT31.mpk", 566, "13610", 93),
    ("LT31.mpk", 566, "传送配置", 641),
)

NATIVE_TERMS = (
    "又见新来燕",
    "又见新燕来",
    "红线",
    "江叔",
    "冯继升",
    "冯继生",
    "天涯客",
    "方旭",
    "老金",
    "寻心",
    "寒姨",
    "寒香寻",
    "少东家",
    "明潮",
    "暗涌",
    "燕北盟",
    "王清",
    "河东八骏",
    "换脸",
    "妙善",
    "田英",
)


class VerificationError(RuntimeError):
    """Raised when a deterministic H-NEX-006 invariant fails."""


class Verifier:
    def __init__(self) -> None:
        self.passed = 0

    def check(self, condition: bool, label: str) -> None:
        if not condition:
            raise VerificationError(label)
        self.passed += 1
        print(f"PASS {label}")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def git(root: Path, *args: str) -> bytes:
    return subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True
    ).stdout


def git_show(root: Path, revision: str, path: str) -> bytes:
    return git(root, "show", f"{revision}:{path}")


def normalized_trailing_space(data: bytes) -> list[bytes]:
    return [line.rstrip() for line in data.splitlines()]


def is_subsequence(needle: list[bytes], haystack: list[bytes]) -> bool:
    iterator = iter(haystack)
    return all(any(candidate == item for candidate in iterator) for item in needle)


def json_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise VerificationError(f"expected JSON object: {path}")
    return value


def local_markdown_links(paths: list[Path]) -> tuple[int, list[str]]:
    pattern = re.compile(r"(?<!!)\[[^]]*\]\(([^)]+)\)")
    count = 0
    missing: list[str] = []
    for path in paths:
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for raw_target in pattern.findall(line):
                if raw_target.startswith(("http://", "https://", "#")):
                    continue
                target = raw_target.split("#", 1)[0]
                if not target:
                    continue
                count += 1
                if not (path.parent / target).resolve().exists():
                    missing.append(f"{path}:{line_number} -> {raw_target}")
    return count, missing


def verify() -> int:
    root = Path(__file__).resolve().parents[2]
    v = Verifier()

    evidence_dir = root / "docs/research/narrative/qinghe/reconciliation"
    evidence_map_path = evidence_dir / "qinghe-part1-evidence-map.md"
    followup_path = evidence_dir / "windows-followup-evidence-list.md"
    index_path = evidence_dir / "README.md"
    packet_path = root / "docs/research/evidence/windows/wave-1.6/nex005-qinghe-packet/out/qinghe-evidence-packet.json"
    manifest_path = root / "docs/research/evidence/windows/wave-1.6/nex005-qinghe-packet/out/selection-manifest.json"
    canonical_path = root / "content/yysls-qinghe-canonical-v0.1.json"

    v.check(
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", BASE_COMMIT, "HEAD"], cwd=root
        ).returncode
        == 0,
        "base commit is an ancestor of HEAD",
    )
    protected = ("content", "schemas", "apps", "packages", "public")
    v.check(
        subprocess.run(
            ["git", "diff", "--quiet", BASE_COMMIT, "--", *protected], cwd=root
        ).returncode
        == 0,
        "canonical/schema/product/asset surfaces are unchanged from base",
    )

    original_lines = 0
    original_hashes: dict[str, str] = {}
    for relative in MAC_FILES:
        blob = git_show(root, MAC_COMMIT, relative)
        original_lines += len(blob.splitlines())
        original_hashes[relative] = sha256_bytes(blob)
    v.check(original_lines == 532, "Mac input contains the declared 532 lines")
    for relative in EXACT_MAC_FILES:
        v.check(
            (root / relative).read_bytes() == git_show(root, MAC_COMMIT, relative),
            f"Mac input remains byte-identical: {relative}",
        )
    hidden_path = "docs/research/narrative/qinghe/hidden-story-inventory.md"
    v.check(
        normalized_trailing_space((root / hidden_path).read_bytes())
        == normalized_trailing_space(git_show(root, MAC_COMMIT, hidden_path)),
        "hidden-story input differs only by trailing whitespace",
    )
    readme_path = "docs/research/narrative/qinghe/README.md"
    v.check(
        is_subsequence(
            git_show(root, MAC_COMMIT, readme_path).splitlines(),
            (root / readme_path).read_bytes().splitlines(),
        ),
        "Mac README content is preserved with additive reconciliation entries",
    )
    index_text = index_path.read_text(encoding="utf-8")
    v.check(
        all(digest in index_text for digest in original_hashes.values()),
        "reconciliation index records every original Mac input SHA-256",
    )

    v.check(sha256_file(packet_path) == PACKET_SHA256, "Windows packet SHA-256 is frozen")
    v.check(sha256_file(manifest_path) == MANIFEST_SHA256, "Windows manifest SHA-256 is frozen")
    v.check(sha256_file(canonical_path) == CANONICAL_SHA256, "canonical SHA-256 is frozen")

    packet = json_object(packet_path)
    v.check(packet.get("builder_commit") == BUILDER_COMMIT, "packet builder provenance matches")
    v.check(packet.get("extractor_commit") == EXTRACTOR_COMMIT, "packet extractor provenance matches")

    tracked_json = git(root, "ls-files", "*.json").decode().splitlines()
    for relative in tracked_json:
        json.loads((root / relative).read_text(encoding="utf-8"))
    v.check(len(tracked_json) == 47, "all 47 tracked JSON files parse")

    changed_markdown = [
        root / relative
        for relative in git(
            root, "diff", "--name-only", f"{BASE_COMMIT}..HEAD", "--", "*.md"
        ).decode().splitlines()
    ]
    link_count, missing_links = local_markdown_links(changed_markdown)
    v.check(link_count >= 33 and not missing_links, "all changed local Markdown links resolve")

    canonical = json_object(canonical_path)
    nodes = {node["canonical_key"]: node for node in canonical["nodes"]}
    for key, expected in CANONICAL_EXPECTED.items():
        node = nodes.get(key)
        v.check(node is not None, f"canonical key resolves: {key}")
        assert node is not None
        actual = (node["title"], node["parent_key"], node["sort_order"])
        v.check(actual == expected, f"canonical title/parent/order match: {key}")

    evidence_text = evidence_map_path.read_text(encoding="utf-8")
    claim_ids = re.findall(r"^### (NEX006-[A-Z0-9-]+)$", evidence_text, re.MULTILINE)
    statuses = Counter(
        re.findall(r"\*\*reconciliation_status\*\*：`([A-Z_]+)`", evidence_text)
    )
    v.check(len(claim_ids) == 10 and len(set(claim_ids)) == 10, "10 atomic claim IDs are unique")
    v.check(
        statuses
        == Counter(
            {"PARTIALLY_SUPPORTED": 5, "CONFLICT": 1, "UNRESOLVED": 4}
        ),
        "claim status distribution matches 0/5/1/4",
    )

    clusters = packet.get("clusters")
    if not isinstance(clusters, list):
        raise VerificationError("packet clusters must be a list")
    cluster_ids = {cluster["cluster_id"] for cluster in clusters}
    v.check(cluster_ids == EXPECTED_CLUSTERS, "all seven packet clusters match the evidence map")
    packet_entries = {
        (entry["archive"], entry["entry_index"])
        for cluster in clusters
        for entry in cluster["entries"]
    }
    v.check(len(packet_entries) == 12, "all 12 packet entries are unique and accounted for")
    for archive, entry_index in packet_entries:
        token = f"{archive.removesuffix('.mpk')}[{entry_index}]"
        v.check(token in evidence_text, f"packet entry is cited: {token}")

    observations = {
        (
            observation["provenance"]["archive"],
            observation["provenance"]["entry_index"],
            observation["raw_value"],
            observation["byte_offset"],
        )
        for cluster in clusters
        for observation in cluster["structural_observations"]
    }
    v.check(
        all(item in observations for item in REPRESENTATIVE_OBSERVATIONS),
        "all 18 representative observation locators resolve in the packet",
    )
    v.check(
        all(term not in packet_path.read_text(encoding="utf-8") for term in NATIVE_TERMS),
        "native target terms remain absent from the frozen packet",
    )

    followup_text = followup_path.read_text(encoding="utf-8")
    tasks = re.split(r"^## (P[01]-\d+ — .+)$", followup_text, flags=re.MULTILINE)
    headings = tasks[1::2]
    bodies = tasks[2::2]
    if len(headings) != len(bodies):
        raise VerificationError("Windows follow-up headings and bodies are unbalanced")
    task_sections = list(zip(headings, bodies))
    required_fields = (
        "**target claim**",
        "**required evidence type**",
        "**candidate archive / entry / cluster**",
        "**static procedure**",
        "**success criterion**",
        "**failure criterion**",
        "**manual fallback**",
    )
    v.check(len(task_sections) == 7, "seven Windows follow-up tasks are defined")
    v.check(
        all(all(field in body for field in required_fields) for _, body in task_sections),
        "every Windows follow-up task contains the full execution schema",
    )

    print(f"H-NEX-006 deterministic Mac verification PASS ({v.passed} checks)")
    return 0


def main() -> int:
    try:
        return verify()
    except (OSError, subprocess.CalledProcessError, VerificationError, AssertionError) as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
