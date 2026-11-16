---
name: course-manuscript-validation
description: Validate a Chinese insurance micro-course draft against its task card before review or storyboarding. Use after manuscript generation; do not write, approve, or storyboard the manuscript.
---

# 课程文稿硬校验

负责 N04.5。读取 `task-spec.json`、课程草稿和 `artifact-manifest.json`，输出 `validation-report.json`。本技能只报告问题，不修改正文、不补充事实、不批准进入 N06。

## 阻断规则

以下任一问题必须标为 P0，状态为 `BLOCKED`：

- 正文出现未在任务卡 `entities` 中声明的命名角色；
- 角色名称、身份或称谓自相矛盾；
- 缺少要求栏目、知识点超过 3 个或练习题不是 8 道；
- 练习题缺答案、解析或来源；
- 出现未关闭的占位符、批注或模板残留；
- 关键结论缺少证据 ID，或 manifest 没有对应来源记录。

使用 `scripts/validate_course_manuscript.py` 执行确定性检查，再补充必要的人工/模型语义检查。报告应列出：`status`、每项问题的 `severity`、`location`、`rule_id`、`evidence` 和 `repair_hint`。仅在 P0 数量为 0 时输出 `PASS`。
