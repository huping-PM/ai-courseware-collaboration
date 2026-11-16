---
name: ppt-to-hyperframes-video
description: |
  用 HyperFrames 引擎把「PPT/讲稿/配音稿」制作成逐页动画解说视频（1920×1080 mp4），并保证画面元素与旁白严格音画同步。

  当用户要求：把 PPT/文档/讲稿做成动画视频、政策解读视频、知识科普视频、给 PPT 加动效导出 mp4、
  基于配音稿制作逐帧动画、按「先出审核图再渲染」的流程做动画视频、修复「配音念到某板块但画面卡片迟迟不出现 /
  卡片提前弹出 / 文字没居中 / 图标和文字没对齐」等排版与音画不同步问题时，触发本技能。

  与兄弟技能的边界：
  - `hyperframes-core` / `hyperframes-animation` 是 HyperFrames 引擎的底层技术契约（composition 结构、data-* 属性、GSAP 运行时），本技能调用它们。
  - `ppt-to-animated-video` 走的是「slidep + Edge headless 逐帧截图 + ffmpeg」路线，本技能走「HyperFrames 引擎直接 render」路线，二者互斥，按用户环境选择。
  - 本技能沉淀的是一套可移植的完整 SOP：配音合成 → 时间轴 → 分场景动效 HTML → 审核图 → 校验 → 渲染交付，换电脑装好依赖即可套用。

  触发词：动画视频、政策解读视频、知识讲解视频、配音视频、HyperFrames、音画同步、不同步、
  先出审核图、元素图标、配色改淡蓝、报行合一、治理政策、逐页动效、mp4 导出。
license: internal
agent_created: true
---

# PPT → HyperFrames 动画解说视频 · 全流程

把一份 PPT 或讲稿，加上逐句配音稿，用 **HyperFrames 引擎**（HTML 声明式动效 + GSAP 时间轴 + 引擎统一 render）做成 1920×1080 / 30fps 的逐页动画解说视频。本技能沉淀的是经过完整交付验证的端到端流程（以「非车险综合治理政策解读」项目为蓝本，共 12 场景、8 分 46 秒成片）。

## 0. 目录约定（可直接迁移）

```
<项目>/非车险新规解读-动画视频/
├── 分镜.md                      # 分镜脚本：每页标题+要点+配图规划
├── 视频规格书.md                # 画幅/帧率/配色/字体约定
├── synth_full.py                # ★ 逐句配音合成（edge-tts）→ 输出每句时长
├── timeline-full.json           # ★ 每场每句的 {text,dur} + 每场 total（时间轴唯一真相）
├── 字幕.srt                     # 由 timeline 生成的逐句字幕
├── audio_full/                  # 逐句 mp3 + concat.txt + narr_full.mp3（拼接成品）
├── .fftools/                    # ★ ffmpeg.exe + ffprobe.exe（从静态包复制，见 §环境）
└── hf-full/                     # ★ HyperFrames 工程（render 的根目录）
    ├── index.html               # 编排：12 场景 + narr_full.mp3（主时间轴）
    ├── gsap.min.js              # GSAP 运行时
    ├── narr_full.mp3            # 全片配音
    ├── compositions/sceneNN.html # 每场一个子合成（<template> 包裹）
    ├── assets/*.png              # 配图
    └── snapshots/review-*/       # 审核图输出
```

## 1. 阶段总览（8 步，先审后渲）

| 阶段 | 动作 | 产出 | 关键点 |
|---|---|---|---|
| 1 配音 | 写逐句稿 → `synth_full.py` 合成 | `audio_full/*.mp3` + `timeline-full.json` | 每句独立 mp3，时长实测写入 json |
| 2 拼接 | concat 逐句 → `narr_full.mp3` | 全片配音 | 连续紧排，不留静音 |
| 3 分镜 | 写 `分镜.md`（每页标题/要点/配图） | 分镜脚本 | 决定每页动效节奏 |
| 4 工程 | 搭 `hf-full/`：index.html + sceneNN.html | HyperFrames 工程 | 契约见 references |
| 5 确认 | **先做 1 页**（配色+图标），出审核图 | 单页快照 | 用户认可再铺开 |
| 6 铺开 | 全部场景加元素图标 + 放大字体 | 12 场景草稿 | 图标每页必加，配图按需 |
| 7 审核 | `check` 校验 + `snapshot` 出全页审核图 | review 图集 | 用户逐帧审核 |
| 8 交付 | 修排版/音画同步 → `render` 出 mp4 | 最终 mp4 | 同步算法见 references/sync |

**先跑 7 的 check+snapshot，用户确认后再跑 8 的 render（渲染约 8 分钟，最贵）。**

## 2. 音画同步模型（本技能核心，血的教训）

**不要"拍脑袋"写每张卡片的入场时刻。** 正确做法是：读 `timeline-full.json`，算出每场每句旁白的「场景内相对起始时刻」，把每个卡片/板块的入场动画对齐到它对应那句旁白「刚开始念」的时刻（±0.2s）。

- **滞后**（配音念完了卡片才出现）= 元素入场时刻 > 本句播放区间
- **提前**（配音没念到画面先切换）= 元素入场时刻 < 本句起点
- **多卡片场景最易错**：三个板块分别对应三句旁白，必须各自对齐，不能只排一个开场

算法与坑详见 `references/sync.md`，已有现成脚本 `scripts/calc_seg_times.py`。

## 3. 配色与元素图标规范（用户明确偏好，直接照抄）

用户要求的配色 token（政策解读类视频通用，已验证美观）：

| 用途 | 色值 |
|---|---|
| 背景 | `#EAF2F8` 淡蓝 |
| 卡片 | `#FFFFFF` 白 |
| 标题/强调/图标线条 | `#1F4E79` 深蓝 |
| 正文 | `#161B22` 近黑 |
| 次要文字 | `#4A5F76` 灰蓝 |
| 图标圆底 | `#D8E6F3` 淡蓝 |
| 分割线/描边 | `#DCE7F1` |
| 深蓝药丸内图标线条 | `#FFFFFF` 白 |

元素图标：**每页必加**（淡蓝圆底 + 具象 SVG），配图按需（仅关键页）。字体：标题 62~72px、卡片标题 38~44px、正文 25~34px，卡片尺寸同步调大填满空白，底部留字幕区（y≈820~920）。

图标 SVG 规范与现成图标库见 `references/icons.md`。

## 4. 通用提示词（每页构图提示，可直接喂给生成/手写）

见 `references/prompts.md`，含：每场景的构图提示词模板、配图生成提示词（ImageGen）、配音稿润色提示词（edge-tts）。

## 5. 换电脑套用清单

见 `references/setup.md`，含：Node/Python/ffmpeg 依赖、`.fftools` 提取、edge-tts 安装、HyperFrames CLI、路径硬编码排查清单。

## 6. 校验与交付检查清单

- [ ] `npx hyperframes check .` → 0 errors, 0 warnings（lint+runtime+layout+motion+contrast）
- [ ] 每个子合成的 `data-composition-id` = 模板根 `data-composition-id` = `window.__timelines` 的 key
- [ ] `<style>`/`<script>` 都在 `<template>` 内；`#root` 有明确尺寸
- [ ] 音画同步：每卡片入场时刻 = 对应旁白分句起点（脚本可验）
- [ ] 快照审核图每页肉眼过一遍
- [ ] `render -q delivery` 出 mp4 后 ffprobe 核对（1920×1080 / h264+aac / 时长≈配音总长）

详见各 references 文档。开始前先读 `references/setup.md` 确认环境，再读 `references/contract.md` 掌握 HyperFrames 契约。