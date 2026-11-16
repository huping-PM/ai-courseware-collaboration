---
name: video-animation-build
description: Use when 用户要将页面内容与配音时间轴制作成逐项讲解动画，或修改讲解视频的页面视觉时。
---

# 讲解动画页面生成

## 输入与输出

- 输入：project.json、匹配该版本的timeline.json及图片/逐页音频。
- 输出：自包含HTML动画页、音频副本和pages-manifest.json。
- 适用范围：PPT知识讲解视频基础路线。基础讲解动效，不是通用PPT动画解析或视频编辑器；音画语义与观看体验需人工检查。

## 执行

1. 读取[数据契约](../video-workflow/references/data-contract.md)，运行[动画生成器](scripts/build_animation.py)，要求版本摘要、页序及语句映射一致。
2. 使用显式segment_id安排要点出场。一个句子绑定多个要点允许同时出现；需要逐项讲解时回到文案拆句，不机械套用原案例挤堆判据。
3. 所有层在旁白音频结束后统一淡出。window.seek(t)负责确定性画面，不依赖自动播放计时器。
4. 在浏览器检查静态布局及语句起点、页尾关键帧；图片内嵌，无外部动画/CSS文件依赖。PPT与动画内容同源，不能据此宣称像素完全一致。
5. 对过长内容返回明确容量问题；角色表演、复杂场景和自定义动效需另外实现与验证。

## 工具入口

在命令中将`<本技能>`替换为本SKILL.md所在目录，`<任务>`替换为用户指定输出目录；Python/Node使用当前环境实际可执行路径。路径含空格时保留引号。

```text
python "<本技能>/scripts/build_animation.py" --project "<任务>/project.json" --timeline "<任务>/voice-run-001/timeline.json" --output "<任务>/animation-run-001"
```

## 依赖与交接

本技能属于视频创作技能套件，须保留兄弟目录`video-workflow`，共用[数据契约](../video-workflow/references/data-contract.md)和[依赖说明](../video-workflow/references/dependencies.md)。复制单个节点时应同时带上该公共依赖，或由目标平台注册对应工具；不要只导入SKILL.md就声称脚本可执行。

## 失败与完成标准

- 缺输入、工具、账号权限或资源时，准确指出阻碍及可继续的工作，不伪造产物或检查结果。
- 工具报错先读原因，不循环盲重试；输出覆盖默认拒绝，保留已有人工成果。
- 完成时给出真实文件路径、执行过的检查、未检查项和下一节点。结构有效、文件生成、视觉通过、业务确认分别记录。
- 在用户授权范围内推进；本技能不自带外部发布、全局安装或后台监控授权。
