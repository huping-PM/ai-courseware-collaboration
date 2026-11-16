---
name: course-manuscript-review
description: Review a complete Chinese insurance micro-course oral manuscript before storyboarding. Use for N05 content, source, spoken-script, and introduction-design review; do not create detailed storyboards.
---

# 课程文稿审核（试用）

负责 N05。审核对象必须是 N04 的完整口播稿和其 `artifact-manifest.json`，不是仅有目标、结论与知识点的课程大纲。先读取 `course-manuscript-validation` 的校验报告；存在 P0 时直接给出“修改后复审”，不以主观判断绕过硬校验。默认输出问题单和确认建议；除非用户明确要求，不直接重写文稿或生成分镜。

## 审核范围

按已确认的依据包、课程模板、课程生成规则和课程类型规则审核：

1. **事实边界与来源：** 关键结论可追溯；无承保、理赔、定责、金额或政策适用的越界承诺。
2. **口播完整性与可读性：** 场景、转场、每个知识判断点和小结均有连续、可朗读的口播；不能以标题、项目符号或“此处讲解”替代正文。
3. **教学结构：** 一个问题、至多 3 个知识点、目标/正文/小结/8 道题闭环；知识讲解中结论、条件、误区、服务动作和依据已被说清。
4. **情境导入设计：** 60–90 秒，只建立问题；人物、场地、叙事/旁白/对白、误解和冻结问题完整；导入不代替正文规则讲解。
5. **文稿表达：** 场景、知识讲解和小结职责不混淆；小结不回到开场人物；口播适合线上微课而非文件条文复述。
6. **分镜交接准备：** 已确认口播足以被 N06 映射，但不在 N05 审查镜头、机位、动画、布局或生成参数。

按 P0–P3 输出“位置 / 问题 / 依据 / 最小修改建议 / 回退节点”。同时输出机器可读字段：`status`（`APPROVED`、`BLOCKED`、`RETURNED`）、`blocking_issue_count`、`required_next_skill` 和 `locked_sections`。审核结论仅可为：通过进入 N06、修改后复审或退回上游；确认版不得被草稿覆盖。
