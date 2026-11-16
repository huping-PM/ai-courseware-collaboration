---
name: video-voice-timeline
description: Use when 用户要给逐页口播配音、换音色、合并分句音频或生成真实时长的视频时间轴时。
---

# 课件配音与时间轴

## 输入与输出

- 输入：project.json；每句对应的真实音频，或可用且获授权的TTS能力。
- 输出：逐页PCM WAV、timeline.json、试听和音色记录。
- 适用范围：PPT知识讲解视频基础路线。同采样率单声道PCM16 WAV可走标准库；其他音频需FFmpeg。内置不含本地TTS大模型及声音克隆。

## 执行

1. 读取[数据契约](../video-workflow/references/data-contract.md)。先确认音色、语言、特殊术语，复用已有授权；需要时先生成短试听。
2. 可使用已授权宿主TTS、本地引擎或edge-tts。无账号不等同于无服务：edge-tts路径不要求本技能保存账号，但依赖联网与实际音色可用性。没有可用引擎则明确阻碍，不生成静音假配音。
3. 将每句真实音频路径写入segment.audio。独立的[edge-tts桥接脚本](scripts/synthesize_edge.py)按显式音色合成，运行会联网；不在普通结构测试时调用。
4. 用[时间轴工具](scripts/build_timeline.py)统一采样率、声道和格式，以实际样本数建立逐页音频和时间轴；禁止按字数估时。
5. 页面末尾音频可能含静音，当前narration_end指最后音频样本，不宣称精确识别最后发声点。需要去静音时先处理音频再建时间轴。
6. 改口播或音色后输出到新目录，重建时间轴及下游动画/视频。试听检查错音、断句和音量，记录未复核项。

## 工具入口

在命令中将`<本技能>`替换为本SKILL.md所在目录，`<任务>`替换为用户指定输出目录；Python/Node使用当前环境实际可执行路径。路径含空格时保留引号。

```text
python "<本技能>/scripts/build_timeline.py" --project "<任务>/project.json" --output "<任务>/voice-run-001" --ffmpeg "<FFmpeg路径>"
```

## 依赖与交接

本技能属于视频创作技能套件，须保留兄弟目录`video-workflow`，共用[数据契约](../video-workflow/references/data-contract.md)和[依赖说明](../video-workflow/references/dependencies.md)。复制单个节点时应同时带上该公共依赖，或由目标平台注册对应工具；不要只导入SKILL.md就声称脚本可执行。

## 失败与完成标准

- 缺输入、工具、账号权限或资源时，准确指出阻碍及可继续的工作，不伪造产物或检查结果。
- 工具报错先读原因，不循环盲重试；输出覆盖默认拒绝，保留已有人工成果。
- 完成时给出真实文件路径、执行过的检查、未检查项和下一节点。结构有效、文件生成、视觉通过、业务确认分别记录。
- 在用户授权范围内推进；本技能不自带外部发布、全局安装或后台监控授权。
