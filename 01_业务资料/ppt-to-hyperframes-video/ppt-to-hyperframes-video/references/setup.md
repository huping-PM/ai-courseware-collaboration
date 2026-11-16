# 换电脑套用清单（环境与依赖）

## 1. 依赖一览

| 依赖 | 用途 | 安装/获取 |
|---|---|---|
| Node 22.x | 跑 HyperFrames CLI | WorkBuddy 托管 `binaries/node/versions/22.x` 或系统 node |
| Python 3.13 | 配音合成、时间轴计算 | 同上托管或系统 python |
| edge-tts | 逐句配音合成（晓晓语音） | `pip install edge-tts`（装进隔离 venv，别污染全局） |
| HyperFrames CLI | check/render/snapshot | 无需全局安装，`npx hyperframes@0.8.58` 按需拉取 |
| ffmpeg + ffprobe | render 内部必调 | **系统 PATH 常没有**，需自取（见下） |

## 2. ffmpeg / ffprobe（关键坑）

`npx hyperframes render` 报 `FFmpeg/FFprobe not found` 时：

1. 从 node_modules 的静态包复制 exe 到项目 `.fftools/`：
   ```bash
   mkdir -p .fftools
   cp node_modules/ffmpeg-static/ffmpeg.exe .fftools/
   cp node_modules/ffprobe-static/ffprobe.exe .fftools/   # 包名以实际为准
   ```
2. 每次 render/check 前注入 PATH：
   ```bash
   export PATH="$(pwd)/../.fftools:$PATH"
   ```
   注意 `.fftools` 放在工程父目录（hf-full 的上级），所以相对路径是 `../.fftools`。

## 3. 路径硬编码排查清单（换电脑必查）

以下脚本里可能写着绝对路径，换电脑/换账号要改：

- `synth_full.py`：`FFPROBE = "D:/…/tools/ffmpeg/…/ffprobe.exe"` → 改为 `.fftools/ffprobe.exe` 或环境变量。
- `concat.txt`：`file 'D:/…/audio_full/s01_s00.mp3'` → 全量换成新机器绝对路径（或脚本生成）。
- Windows 路径统一用正斜杠 `/`（Git Bash 兼容）。

## 4. 隔离环境约定（WorkBuddy 托管运行时）

- Python 装包用隔离 venv，别跑全局 `pip install`：
  - 创建：`<python> -m venv <isolated>/envs/default`
  - 装包：`<venv>/bin/pip install edge-tts`
- Node 包尽量用 `npx` 按需拉取，不全局安装。

## 5. 从零到交付的最小启动顺序

```bash
# 1) 本地 FFmpeg
mkdir -p .fftools && cp <ffmpeg-static>/ffmpeg.exe .fftools/ && cp <ffprobe-static>/ffprobe.exe .fftools/

# 2) 合成配音（生成 audio_full/ + timeline-full.json）
python synth_full.py

# 3) 拼接全片配音
ffmpeg -f concat -safe 0 -i audio_full/concat.txt -c copy hf-full/narr_full.mp3

# 4) 校验工程
cd hf-full && export PATH="$(pwd)/../.fftools:$PATH"
npx hyperframes@0.8.58 check .

# 5) 出审核图
npx hyperframes@0.8.58 snapshot . -o snapshots/review-v1 --at <各场中点秒数>

# 6) 用户确认后渲染
npx hyperframes@0.8.58 render . -o 成品.mp4 -q delivery
```

## 6. 常见报错速查

| 报错 | 原因 | 解法 |
|---|---|---|
| FFmpeg/FFprobe not found | PATH 无 ffmpeg | 复制到 .fftools 并注入 PATH |
| GSAP target not found | DOM id 写错 / 模板外 | 修 id；确认在 template 内 |
| content_overlap | 文本基线重叠 | 拉开 y / margin |
| text_box_overflow | 文字超卡片 | 加高卡片或缩小字号 |
| 渲染帧全黑 | 全屏色块放 root 上了 | 色块改放 full-bleed 子元素 |