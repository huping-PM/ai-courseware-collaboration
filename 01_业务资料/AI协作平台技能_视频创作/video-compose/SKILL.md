---
name: video-compose
description: Use when 用户要把课件帧序列与逐页配音合成MP4、重建视频片段或输出无字幕讲解成片时。
---

# 讲解视频合成

## 输入与输出

- 输入：frames-manifest.json、连续帧及逐页WAV；FFmpeg。
- 输出：逐页MP4、无字幕final.mp4和composition.json。
- 适用范围：PPT知识讲解视频基础路线。首版不处理字幕烧录、BGM混音、转场剪辑或复杂音效。需要时另扩展，不应声称当前已经支持。

## 执行

1. 读取[数据契约](../video-workflow/references/data-contract.md)，使用[合成工具](scripts/compose_video.py)读取当前帧清单。
2. 工具检查完整序列及参数、逐页显式限帧并强制生成到新目录；缺资源返回失败，不复用已有旧MP4。
3. 帧序列与音频按统一fps/帧数合成，统一编码再拼接。仅生成无字幕版，不擅自增加字幕或其他交付版本。
4. 交给质量检查技能实际探测成片；查看拼接边界与试听。不能用容器时长的小差异代替视频帧数检查，也不能只凭进程成功判成片通过。

## 工具入口

在命令中将`<本技能>`替换为本SKILL.md所在目录，`<任务>`替换为用户指定输出目录；Python/Node使用当前环境实际可执行路径。路径含空格时保留引号。

```text
python "<本技能>/scripts/compose_video.py" --manifest "<任务>/frames-run-001/frames-manifest.json" --output "<任务>/video-run-001" --ffmpeg "<FFmpeg路径>"
```

## 依赖与交接

本技能属于视频创作技能套件，须保留兄弟目录`video-workflow`，共用[数据契约](../video-workflow/references/data-contract.md)和[依赖说明](../video-workflow/references/dependencies.md)。复制单个节点时应同时带上该公共依赖，或由目标平台注册对应工具；不要只导入SKILL.md就声称脚本可执行。

## 失败与完成标准

- 缺输入、工具、账号权限或资源时，准确指出阻碍及可继续的工作，不伪造产物或检查结果。
- 工具报错先读原因，不循环盲重试；输出覆盖默认拒绝，保留已有人工成果。
- 完成时给出真实文件路径、执行过的检查、未检查项和下一节点。结构有效、文件生成、视觉通过、业务确认分别记录。
- 在用户授权范围内推进；本技能不自带外部发布、全局安装或后台监控授权。
