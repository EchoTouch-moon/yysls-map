## 变更类型

- [ ] 功能（feat）
- [ ] 缺陷修复（fix）
- [ ] 数据集内容（feat(data)/fix(data)）
- [ ] 文档
- [ ] 工作流 / 配置

## 变更说明

<!-- 简述动机与实现方式 -->

## 验证声明

- [ ] `npm run verify` 通过
- [ ] `npm run test:api:db` 通过（涉及 API/数据时必填）
- [ ] `npm run test:e2e` 通过（涉及页面行为时必填）

## 数据集变更附加检查

- [ ] 已重跑 `python3 scripts/generate_signoff_checklist.py`
      （签字清单与 release-manifest.json 的 SHA-256 已更新）
- [ ] 新增结论有可定位来源；高风险条目不依赖单一社区转述
