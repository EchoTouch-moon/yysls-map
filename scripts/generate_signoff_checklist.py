#!/usr/bin/env python3
"""Generate the Phase-B editorial sign-off checklist for a content dataset.

Extracts every high-risk item per PROJECT_ROADMAP.md stage B:
spoiler levels 2/3, relationship confidence below 0.9, hidden relations,
identity interpretations, and conclusions backed only by community
analysis. Also writes a release manifest with the dataset SHA-256 so the
reviewed bytes can be frozen and reproduced.

Usage:
    python3 scripts/generate_signoff_checklist.py [path/to/dataset.json]
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEFAULT_DATASET = REPO / "content" / "yysls-qinghe-v4.json"
CHECKLIST_PATH = REPO / "docs" / "editorial-signoff-qinghe.md"
MANIFEST_PATH = REPO / "content" / "release-manifest.json"

DECISION_OPTIONS = "通过 / 降级 / 改写 / 暂不发布"


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    dataset_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DATASET
    data = json.loads(dataset_path.read_text())
    digest = sha256_of(dataset_path)
    now = time.strftime("%Y-%m-%d %H:%M")

    sources_by_id = {s["id"]: s for s in data["sources"]}
    chars_by_id = {c["id"]: c["name"] for c in data["characters"]}

    def source_types(ids: list[str]) -> list[str]:
        return [sources_by_id[i]["source_type"] for i in ids if i in sources_by_id]

    def only_community(ids: list[str]) -> bool:
        types = source_types(ids)
        return bool(types) and set(types) == {"community_analysis"}

    lines = [
        "# 清河编辑签字清单",
        "",
        f"> 数据集：`{data['dataset']['id']}` · SHA-256 `{digest[:16]}…{digest[-8:]}`",
        f"> 生成时间：{now} · 审阅对象为上述哈希对应的文件字节",
        "",
        "每条给出明确审阅决定（**通过 / 降级 / 改写 / 暂不发布**）并签名。",
        "决定「通过」即确认：措辞、剧透等级与来源支撑均达到公开标准。",
        "",
    ]

    # A. spoiler 2/3 entities
    lines += ["## A. 剧透等级 2/3 的公开实体", ""]
    count_a = 0
    for kind, items, name_key in (
        ("人物", data["characters"], "name"),
        ("事件", data["events"], "title"),
    ):
        for item in items:
            if item["spoiler_level"] >= 2:
                count_a += 1
                flag = " ⚠️仅社区来源" if only_community(item.get("source_ids", [])) else ""
                lines.append(
                    f"- [ ] `{item['id']}` [{kind}] {item[name_key]}"
                    f"（spoiler {item['spoiler_level']}）{flag}"
                )
    lines.append("")

    # B. low-confidence relationships
    lines += ["## B. 置信度低于 0.9 的关系", ""]
    count_b = 0
    for rel in data["relationships"]:
        if rel.get("confidence", 1) < 0.9:
            count_b += 1
            src = chars_by_id.get(rel["source_character_id"], rel["source_character_id"])
            dst = chars_by_id.get(rel["target_character_id"], rel["target_character_id"])
            flag = " ⚠️仅社区来源" if only_community(rel.get("source_ids", [])) else ""
            lines.append(
                f"- [ ] `{rel['id']}` {src} —[{rel['relation_type']}]→ {dst}"
                f"（confidence {rel['confidence']}，spoiler {rel['spoiler_level']}）{flag}"
            )
    lines.append("")

    # C. hidden relations
    lines += ["## C. 隐藏关系（relation_type = hidden）", ""]
    count_c = 0
    for rel in data["relationships"]:
        if rel["relation_type"] == "hidden":
            count_c += 1
            src = chars_by_id.get(rel["source_character_id"], rel["source_character_id"])
            dst = chars_by_id.get(rel["target_character_id"], rel["target_character_id"])
            lines.append(
                f"- [ ] `{rel['id']}` {src} → {dst}"
                f"（spoiler {rel['spoiler_level']}，confidence {rel.get('confidence')}）"
            )
    lines.append("")

    # D. identity interpretations
    lines += ["## D. 含身份解释的人物卷宗（spoiler ≥2 且有 interpretation）", ""]
    count_d = 0
    for c in data["characters"]:
        if c["spoiler_level"] >= 2 and c.get("interpretation"):
            count_d += 1
            lines.append(f"- [ ] `{c['id']}` {c['name']}（spoiler {c['spoiler_level']}）")
    lines.append("")

    # E. single-community-source high risk
    lines += ["## E. 高风险且仅社区来源（需补官方材料、任务定位或玩家亲历）", ""]
    count_e = 0
    seen = set()
    for kind, items, name_key in (
        ("人物", data["characters"], "name"),
        ("事件", data["events"], "title"),
        ("关系", data["relationships"], "label"),
    ):
        for item in items:
            risky = item.get("spoiler_level", 0) >= 2 or item.get("confidence", 1) < 0.9
            if risky and only_community(item.get("source_ids", [])):
                count_e += 1
                seen.add(item["id"])
                lines.append(f"- [ ] `{item['id']}` [{kind}] {item[name_key]}")
    lines.append("")

    # F. story guide verbatim review
    arc = data["story_arcs"][0]
    lines += [
        "## F. 主线导读逐字审阅（桥接与下一问）",
        "",
        f"弧线：{arc['title']} · {len(arc['beats'])} 节",
        "",
    ]
    for beat in arc["beats"]:
        lines.append(f"- [ ] `{beat['id']}` 第{beat['sort_order']}节 bridge：「{beat['bridge'][:40]}…」")
    lines.append("")

    # summary + signature
    total = count_a + count_b + count_c + count_d + count_e
    lines += [
        "## 汇总",
        "",
        f"- A 剧透 2/3 实体：{count_a}",
        f"- B 低置信关系：{count_b}",
        f"- C 隐藏关系：{count_c}",
        f"- D 身份解释：{count_d}",
        f"- E 高风险仅社区来源：{count_e}",
        f"- F 导读逐字审阅：{len(arc['beats'])} 节",
        f"- **待决条目合计：{total + len(arc['beats'])}**",
        "",
        "## 签字",
        "",
        "| 条目范围 | 审阅人 | 日期 | 备注 |",
        "|---------|--------|------|------|",
        "| A–E 全部 | | | |",
        "| F 导读 | | | |",
        "",
    ]

    CHECKLIST_PATH.write_text("\n".join(lines), encoding="utf-8")

    manifest = {
        "dataset_id": data["dataset"]["id"],
        "dataset_file": dataset_path.name,
        "sha256": digest,
        "schema_version": data["schema_version"],
        "frozen_at": now,
        "counts": {
            "chapters": len(data["chapters"]),
            "factions": len(data["factions"]),
            "characters": len(data["characters"]),
            "events": len(data["events"]),
            "relationships": len(data["relationships"]),
            "sources": len(data["sources"]),
            "historical_references": len(data["historical_references"]),
            "historical_contexts": len(data["historical_contexts"]),
            "event_historical_links": len(data["event_historical_links"]),
        },
        "signoff_checklist": str(CHECKLIST_PATH.relative_to(REPO)),
        "pending_decisions": total + len(arc["beats"]),
    }
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(f"checklist: {CHECKLIST_PATH}")
    print(f"manifest:  {MANIFEST_PATH}")
    print(f"sha256:    {digest}")
    print(f"pending decisions: {total + len(arc['beats'])}")


if __name__ == "__main__":
    main()
