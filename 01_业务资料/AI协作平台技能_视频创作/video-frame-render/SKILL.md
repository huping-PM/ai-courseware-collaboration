---
name: video-frame-render
description: Use when 用户要将确定性HTML动画导出PNG帧序列、重渲染讲解页或检查视频画面缺帧时。
---

# 讲解动画逐帧渲染

## 输入与输出

- 输入：pages-manifest.json、完整本地HTML与音频；浏览器可执行文件。
- 输出：PNG帧序列、音频副本、frames-manifest.json。
- 适用范围：PPT知识讲解视频基础路线。渲染时间与页长相关；仅接收本套动画或通过同等契约验证的本地HTML。

## 执行

1. 读取[数据契约](../video-workflow/references/data-contract.md)与[依赖说明](../video-workflow/references/dependencies.md)。检查Node和一种浏览器控制库，不要求两套都装。
2. 运行[渲染工具](scripts/render_frames.js)，显式传浏览器路径。支持puppeteer-core或已有playwright，不依赖原作者用户名、固定端口或浏览器账号。
3. 工具等待字体/图片和seek就绪，阻止页面HTTP请求，按每页frame预算串行截图。缺页、加载错误或布局错误应失败；不要跳过后宣称完成。
4. 每次使用新目录，渲染过程中不修改project、timeline或HTML。失败保留诊断，修复后新建一次运行。
5. 核对每页从f00000.png开始连续且数量匹配，再交合成节点。

## 工具入口

在命令中将`<本技能>`替换为本SKILL.md所在目录，`<任务>`替换为用户指定输出目录；Python/Node使用当前环境实际可执行路径。路径含空格时保留引号。

```text
node "<本技能>/scripts/render_frames.js" --manifest "<任务>/animation-run-001/pages-manifest.json" --output "<任务>/frames-run-001" --browser "<浏览器exe>" --engine puppeteer
```

## 依赖与交接

本技能属于视频创作技能套件，须保留兄弟目录`video-workflow`，共用[数据契约](../video-workflow/references/data-contract.md)和[依赖说明](../video-workflow/references/dependencies.md)。复制单个节点时应同时带上该公共依赖，或由目标平台注册对应工具；不要只导入SKILL.md就声称脚本可执行。

## 失败与完成标准

- 缺输入、工具、账号权限或资源时，准确指出阻碍及可继续的工作，不伪造产物或检查结果。
- 工具报错先读原因，不循环盲重试；输出覆盖默认拒绝，保留已有人工成果。
- 完成时给出真实文件路径、执行过的检查、未检查项和下一节点。结构有效、文件生成、视觉通过、业务确认分别记录。
- 在用户授权范围内推进；本技能不自带外部发布、全局安装或后台监控授权。
