# NEX-004C — Holdout Selection: Frozen Policy

> Task: NEX-004C Narrative-Relevant Holdout Validation
> 本政策随 `narrative_holdout_selector.py` 在 **C0** 冻结，之后不得修改并仍称同一轮 holdout validation。
> Frozen discovery engine：`204c97f`（R1-R5 与 observation caps 不得修改）。

## 1. 允许的采样先验（source family ONLY）

```text
source family == storyline_data
source family == MSD_ST
```

- family 判定仅观察 **bounded Lua source region**（`0x21` 起，varint 定长）中的子串 `storyline_data` / `MSD_ST`。
- 判定顺序：含 `MSD_ST` → family=MSD_ST；否则含 `storyline_data` → family=storyline_data。

## 2. 禁止的采样信号（selector 从不使用）

```text
dq_*
EXPANSION_*
numeric refs（[0-9]{4,10} 等）
CJK payload
framed payload strings
已知目标值（NodeGraphData / TextByNo / 70276 / 江晏 / dq_610900 等）
```

- selector 代码中不出现上述任何模式；只检查两个 family 子串。

## 3. Holdout 结构

```text
12 unique entries
  6 x (storyline_data AND NOT MSD_ST)
  6 x (MSD_ST)
```

## 4. 排除集（所有历史 pilot/evidence/blind entries）

```text
LT71 : {1768, 1631}          pilots
     + {534, 2766, 1490, 165} blind
LT51 : {1178}                pilot
     + {861, 873}            blind
LT31 : {874}                 pilot
     + {552, 2876}           blind
```

## 5. 确定性选择

```text
selection_score = int(sha256("{arch}:{idx}:{offset}:{size}:{flags}")[:8], 16)
每个 family 取 score 最低的 6 个。
任一 family 候选 < 6 -> 非零退出，不产出 manifest（fail closed）。
```

## 6. Manifest（C1，不泄露完整 source path）

```text
每条：archive, entry_index, entry_offset, stored_size, flags_raw,
      source_family, source_locator_sha256（path 的 SHA-256，不回显路径）, selection_score
```

## 7. Gate coverage（仅统计 R1/R2/R3/R5）

```text
>=2 个 distinct specific rule families 在 unseen holdout 出现 -> NARRATIVE_GENERALIZATION_PASS
0-1                                                    -> GENERALIZATION_PARTIAL
R4 IDENTIFIER 不计入 coverage。
```
