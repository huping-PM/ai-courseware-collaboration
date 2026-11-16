---
name: ppt-to-animated-video
description: |
  把「PPT + 配音稿」制作成逐帧动画解说视频（HTML/CSS 动效 + Edge headless 逐帧截图 + ffmpeg 合成），并保证画面元素与旁白严格对齐（音画同步）。

  当用户要求：把 PPT 做成动画视频/讲解视频/配音视频、把配音稿做成动画、给 PPT 加动效并导出 mp4、审查或修复「动画视频里配音读完了文字才出现」这类音画不同步问题、把某一页 PPT 按配音稿拆成两页并同步重排视频，都应触发本技能。

  触发词：动画视频、讲解视频、配音视频、逐帧、音画同步、不同步、配音读完画面才出现、PPT转视频、把配音稿做成动画。
license: internal
agent_created: true
---

# PPT → 动画解说视频 全流程

把一份 PPT（或 .slide 源码）与分段配音稿，做成 1920×1080 / 25fps 的逐帧动画解说视频。
核心难点不是"做出视频"，而是**画面元素必须在它对应的那句旁白读完之前就已经出现**。

## 0. 目录约定（以本项目为准，可迁移）

```
<项目>/
├── slides/NN.slide              # slidep 源码（页序即视频页序）
├── assets/*.png                 # 配图
├── video/
│   ├── audio/pages/page_NN.wav  # 每页一条整数页音频（总时长 = 视频总时长）
│   ├── audio/segs/pNN_s0M.mp3   # 分句音频（切分来源）
│   ├── timeline.json            # 每页每句的 [start, end]
│   ├── build_pages.py           # ★ 由 timeline 生成 HTML 页面（同步逻辑在这里）
│   ├── html/pages/pNN.html      # 生成的动效页面
│   ├── render.js                # Edge headless 逐帧截图 → html_frames2/pNN/f%05d.png
│   ├── build_video.py           # 页面帧 + 音频 → 每页 mp4 → 拼接 → 字幕
│   ├── verify_sync2.py          # ★ 双向音画同步校验（必跑）
│   └── audit.js                 # 图标/图片资源是否全部解析的静态审计
└── 非车险…（动画版）.mp4          # 最终交付
```

## 1. 阶段总览

| 阶段 | 脚本 | 产出 | 时长量级 |
|---|---|---|---|
| 1 音频 | edge-tts 合成 / 切分 | `audio/pages/page_NN.wav` | 分钟级 |
| 2 时间轴 | `prep_timeline*.py` | `timeline.json` | 秒级 |
| 3 页面 | `build_pages.py` | `html/pages/pNN.html` | 秒级 |
| 4 审计 | `audit.js` | 0 issue | 秒级 |
| 5 渲染 | `render.js` | `html_frames2/pNN/*.png` | **约 4 分钟/页** |
| 6 合成 | `build_video.py` | 每页 mp4 → 总 mp4 + 字幕 | 分钟级 |
| 7 校验 | `verify_sync2.py` | ALL SYNCED | 秒级 |

**先跑 3→4→7，再投入阶段 5 渲染。** 渲染最贵，同步逻辑没验证前不要开渲染。

## 2. 音画同步模型（本技能的核心）

### 2.1 时间轴结构

`timeline.json` 里每页形如：

```json
{"pages": {"1": {"total": 28.854, "segs": [{"start":0,"end":11.2,"text":"…"}, …]}}}
```

`total` **必须等于该页 wav 实测时长**（用 `wave` 读帧数/帧率，不要写估计值）。

### 2.2 根因：元素被铺到了"下一句"

页面里每个元素入场用一个 `block(t0, t_end, n)` 把 n 个元素**均分铺在 [t0, t_end]**。
若调用点习惯性把 `t_end` 传成「下一句起始」或「页尾」，则同一句的**最后一个元素**必然落到
本句语音读完之后 —— 这就是用户说的「配音已经读完，画面才出现对应文字」。

**实测证据（旧版 12 页）**：141 个入场节拍里 **50 个（35.5%）晚于本句语音结束**，
最大滞后 20.57s、平均 4.69s、中位 3.02s，12 页每页都有。

### 2.3 药方：句内锚定 + 硬上限

```python
LAG = 0.45          # 元素最晚必须在"句尾前 0.45s"出现

def sent_window(t, lag=LAG):
    """返回包含 t 的那一句的 [句首, max(句首, 句尾-lag)]；
       t 落在句间空隙时，归给刚读完的前一句。"""
    for s in segs:
        if s["start"] <= t <= s["end"]:
            return s["start"], max(s["start"], s["end"] - lag)
    # 落入空隙 → 取前一句
    prev = [s for s in segs if s["end"] < t]
    if prev:
        s = prev[-1]
        return s["start"], max(s["start"], s["end"] - lag)
    return t, t

def block(t0, t_end, n):
    st, en = sent_window(t0)
    t_end = min(t_end, en)      # ★ 收紧到本句安全句尾
    t0    = min(t0, t_end)      # ★ 避免窗口反转
    ...                          # 再在 [t0, t_end] 内均分
```

`finalize(page_n)` 里**逐 beat 再收一次**：`t = min(t, safe_end)`。
并且**删除**那类 `if ts[-1] > total - TAIL: ts[-1] = end` 的"页尾挤压"逻辑——
它会把元素**提前**，是反方向的错误。

### 2.4 内置源级自检

`build_pages.py` 的 `main()` 里累积 `LEDGER`，构建完打印：

```
[sync] checked 154 beats ... 0 over sentence end
```

**这个数字必须为 0，且 0 是"检查过 154 个"而不是"没检查"。** 若为 0 是因为 LEDGER 为空，说明埋点没生效。

### 2.5 双向校验（`verify_sync2.py`）

单向校验（只看"是否过早"）会漏掉滞后问题。必须双向：

- `maxEarly` ≤ `EARLY_OK=1.2s`（防提前）
- `maxLate` ≤ `LATE_OK=0.60s`（防滞后）—— **本次修复的目标指标**
- `endOver` < 0（动画结束不超出页长）

通过时输出：`RESULT: ALL SYNCED（无提前、无滞后、无超出页长）`

⚠️ **坑**：判定"元素起始时刻"必须取 `keyframes[0]["t"]`（第一个关键帧 = 元素开始出现），
**不能**取"第一个 op > 0 的关键帧"——pop/up 这类动画首帧 op=0，会把结束时刻误当成起始时刻，
从而虚报一批"超出页长"的假问题。

## 3. 按配音稿拆分 PPT 页（"第1页太长，拆成两页"）

### 3.1 切分点选在语义断点

在**句子边界**切，不要句中切。本项目原第 1 页 7 句、67.288s，在第 3 句起点
（=前 3 句累计 28.854s）切分：

- 0–2 句 = 现状问题（28.854s）→ 新第 1 页
- 3–6 句 = 治理演进（38.434s，**基准归零**）→ 新第 2 页

### 3.2 音频切分必须样本级

```python
import wave
w = wave.open(src); n = w.getnframes()
f = w.readframes(n)
# 逐页取帧区间，再 wave.open(dst,'wb') 写同参数
```

**不要用 `ffmpeg -c copy`**：实测有约 32ms 的取整误差（28.886 vs 28.854）。
切完务必校验时长精确到毫秒。

脚本要**幂等**：先备份原页到 `audio/pages_12bak/`，重复执行时从备份恢复再切，
否则会把已经切好的音频再切一次。

### 3.3 页号重排要脚本化

新增一页后，原 `page_02..page_12` 要整体后移成 `page_03..page_13`。
**不要手改**——写个 `shift_pages.py` 用正则批量替换函数名与引用：

- 函数定义 `def page_02(` → `def page_03(`
- 引用 `total_of(2)` / `seg(2,` / `TL["pages"]["2"]`

并用**降序**替换（12→13 先做），避免 02→03 又被后续 03→04 二次替换。
改完 grep 一遍确认没有残留旧引用。

别忘了：
- `PAGE_DEF / HDRS / GLOWS` 这类常量数组要补齐到新页数
- 页脚 `/ 12` 改成动态 `NPC`（= 页数）而不是硬编码 `13`
- `main()` 循环 `range(1, NPC + 1)`

## 4. 渲染与合成

### 4.1 逐帧渲染

`render.js`：Edge headless + puppeteer-core，对页面 `seek(t)` 后逐帧截图。
**约 4 分钟/页**，13 页约 50 分钟。**必须单进程串行**（并行会 OOM/抢占）。

### 4.2 帧数陷阱

重新构建时若新页**变短**，目录里会残留旧的长页帧（本项目 p01 旧 1690 帧、新 729 帧）。
`ffmpeg` 用 `f%05d.png` 会**继续读旧帧**，导致视频尾部出现错误画面。

**解法**：`build_video.py` 的 ffmpeg 命令加 `-frames:v <want>` 显式限帧。

### 4.3 单页与总长

```
单页视频长度 = 该页音频时长 + TAIL(0.30s)
视频总长     = Σ 各页音频时长
```

拼接后务必核对：总长 == 各页实测 wav 之和；每页视频 ≥ 该页音频约 0.30s。

### 4.4 字幕

由 `timeline.json` 生成 `subs.srt`（→ 转 `subs.ass` 便于烧录）。
两个交付版本：**含字幕**（`subtitles` 滤镜烧录）与**无字幕**。

## 5. 导出 PPT 预览图：优先本地方案

`slidep-export-images` 远端后端**不稳定**（实测报过 `retcode=50000 服务繁忙`、
`retcode=437005 PPT转PDF失败`、HTTP 504）。改用**本地 PowerPoint COM 导出**：

```powershell
$ppt  = New-Object -ComObject PowerPoint.Application
$pres = $ppt.Presentations.Open($src, $true, $false, $false)
$pres.Export($out, "PNG", 1600, 900)
$pres.Close(); $ppt.Quit()
```

导出的 PNG 文件名是中文「幻灯片N.PNG」，需重命名为 ASCII（`s01.png`…）再处理。

## 6. 环境约定（本项目实测）

- Node：`C:\Users\<u>\.workbuddy\binaries\node\versions\22.22.2-2\node.exe`
  （调用时须指向 `dist/index.js` 并带命令名；Windows 路径用正斜杠）
- Python：`C:\Users\<u>\.workbuddy\binaries\python\versions\3.13.12\python.exe`
- ffmpeg：`…\python\envs\default\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe`
  （**系统 PATH 里没有 ffmpeg/ffprobe**，脚本内写死绝对路径）
- 沙箱**禁用批量删除**：脚本一律**原地覆盖**，不要依赖清理旧目录。

## 7. 交付前检查清单

- [ ] `audit.js` → 0 issue，图标/图片全部解析
- [ ] `build_pages.py` 自检 → `checked N beats ... 0 over sentence end`
- [ ] `verify_sync2.py` → 全部页 OK，`lateN` 全 0
- [ ] 每页视频长度 ≥ 该页音频 + 0.3s
- [ ] 总长 == Σ 各页 wav 时长（精确到 0.01s）
- [ ] 含字幕 / 无字幕两版均已生成并 ffprobe 核对（1920×1080 / 25fps / h264 + aac）
- [ ] PPT 与视频页数一致、页脚一致

## 8. 常见问题速查

| 现象 | 根因 | 解法 |
|---|---|---|
| 配音读完文字才出现 | `t_end` 传成下一句起点/页尾 | `sent_window()` 句内锚定 + 硬上限 |
| 文字比配音早太多 | 页尾挤压逻辑把元素提前 | 删掉 `total-TAIL` 那段 clamp |
| 校验报"超出页长"假警 | 用"首个 op>0 帧"当起始时刻 | 改用 `keyframes[0]["t"]` |
| 视频尾部画面错乱 | 残留旧长页帧 | ffmpeg 加 `-frames:v` |
| 拆页后时长差几十毫秒 | ffmpeg `-c copy` 取整 | 改 `wave` 模块样本级切片 |
| 页脚还是 `/ 12` | 硬编码 | 改动态 `NPC` |
| 远端导出图 500/504 | 服务不稳 | 本地 PowerPoint COM 导出 |