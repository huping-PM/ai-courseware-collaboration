# 视频创作数据契约 v1

本契约用于本套10个技能。运行成果存入用户选定的任务目录，不能写回技能源码目录。路径为相应JSON文件所在目录的相对路径；仅允许本地相对路径，拒绝绝对路径、URL和越出目录的路径。

## project.json

UTF-8 JSON，schema_version=1。必需字段：title（非空字符串）、pages（非空数组）。

```json
{
  "schema_version": 1,
  "title": "课程名称",
  "language": "zh-CN",
  "canvas": {"width": 1280, "height": 720, "fps": 25},
  "style": {"font": "Microsoft YaHei", "background": "#F7FBF8", "foreground": "#0F3D2E", "accent": "#34C77B"},
  "audio": {"sample_rate": 24000, "pause": 0.25, "tail": 0.30},
  "pages": [{
    "id": "p01", "title": "一个核心观点",
    "bullets": [{"id": "b01", "text": "画面文字", "segment_id": "s01"}],
    "segments": [{"id": "s01", "text": "这句话解释画面中的核心观点。", "audio": "audio/p01-s01.wav"}],
    "source_refs": ["source.md#第一节"]
  }]
}
```

page.id在课程内唯一，bullet.id与segment.id在页内唯一；ID符合`[A-Za-z][A-Za-z0-9_-]*`。bullets和segments非空；bullet.segment_id必须指向本页语句。一个句子可对应多个要点，按映射同时显示，不用模糊文字匹配猜测。可选page.image为本地图片路径；可选segment.audio为已合成单句音频。没有音频不能伪造真实TTS成果。source_refs为来源文字索引，不用于脚本访问网络。

本版基础模板固定16:9，1280×720逻辑画布，fps允许1—60整数；style字段为配置，不是业务标准。基础模板最多5条要点，标题建议不超过30个全角字符，要点建议不超过60字；超长应拆页或调整模板并实测，不宣称固定字数能保证不溢出。不支持自动还原任意上传PPT、复杂图表或角色动画。

## timeline.json

由真实音频生成，禁止按字数估时。project_sha256为project.json原始字节SHA256；项目文件变化后重新生成。

```json
{
  "schema_version": 1, "project_sha256": "实际摘要", "fps": 25, "sample_rate": 24000, "tail": 0.3,
  "pages": [{
    "id": "p01", "audio": "audio/p01.wav",
    "segments": [{"id": "s01", "text": "实际口播", "start": 0.0, "end": 2.0}],
    "narration_end": 2.0, "audio_duration": 2.0,
    "duration": 2.32, "frames": 58
  }]
}
```

单句音频转为相同采样率、单声道16bit PCM，以实际样本数计算时长；句间插入pause，最后一句后不插pause。音频可能自带静音，narration_end定义为最后一段音频样本结束，不等于已做声学检测的最后发声时刻；精细去静音应另行实现并记录。

frames=`ceil((audio_duration+tail)*fps)`；duration=frames/fps。禁止分别四舍五入导致音频截断。fade只用于本版动画，所有层在[narration_end,duration]统一淡出。最后一个采样帧t=(frames-1)/fps，不要求它数值等于duration或绝对纯背景；验收按实际采样点计算预期不透明度。

## 页面与帧清单

动画工具输出pages-manifest.json：schema_version、project_sha256、timeline_sha256、fps、width、height、pages数组。每页包含id、html（相对该清单）、frames、duration、audio（该清单相对路径）。为了独立搬运，生成器应把逐页音频复制入输出目录audio/。html应自包含样式/脚本，图片可内嵌，提供`window.seek(t)`和`window.__videoReady`。canvas使用实际像素1280×720。

渲染器输出frames-manifest.json：上述摘要、fps、width、height及pages；每页id、directory（清单相对路径）、frames、duration、audio（复制入渲染输出的audio/）。帧名f00000.png起严格连续。禁止存在旧结果时静默混用；默认拒绝非空输出目录，重新运行使用新目录。

合成器读取frames-manifest.json，逐页显式限帧，生成MP4和composition.json（schema_version、输入摘要、fps、width、height、frame_count、output路径、页数、检查边界）。生产检查需FFprobe或等效媒体探测；未探测或未播放不能声称成片全面验收。

## 状态与确认

技能成功只表示该节点产物已生成/检查。文案确认、画面确认、配音试听、业务审核是不同状态。不能由脚本退出0自动宣称业务通过。总入口记录用户已有授权，复用已确认输入；改文案/音色重做配音及视频，改纯样式可复用音频但须重新绑定project摘要并检查语句未变。
