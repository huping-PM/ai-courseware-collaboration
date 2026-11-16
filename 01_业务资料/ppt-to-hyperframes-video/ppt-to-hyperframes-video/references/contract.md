# HyperFrames 工程契约（本项目验证过的关键点）

底层完整契约以 `hyperframes-core` / `hyperframes-animation` 技能为准；本文档沉淀本路线
**实际踩过并验证**的要点，写 sceneNN.html 前先读。

## 1. 子合成（sub-composition）结构

每个场景是一个 `<template>` 包裹的 HTML 文件（sceneNN.html），由 index.html 的
`data-composition-src="compositions/sceneNN.html"` 挂载。

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"></head>
<body>
<template>
  <style>…所有样式…</style>
  <div id="root" data-composition-id="scene05" data-width="1920" data-height="1080">
    …内容…
  </div>
  <script>
    window.__timelines = window.__timelines || {};
    const tl = gsap.timeline({ paused: true });
    // … fromTo() 动效 …
    window.__timelines["scene05"] = tl;   // key 必须 = data-composition-id
  </script>
</template>
</body>
</html>
```

三条硬规则（不遵守会静默坏掉）：

1. **`<style>` 和 `<script>` 必须放在 `<template>` 内** —— 运行时只 clone template 内容，外面的全丢弃。
2. **三个 id 必须完全一致**：host slot 的 `data-composition-id` = 模板根 `data-composition-id` = `window.__timelines["<id>"]` 的 key。不要加 `-mount`/`-slot`/`-host` 后缀。
3. **子合成根必须用 `<template>` 包裹**；索引页（index.html）根本身是 standalone，不包裹。

## 2. index.html（编排层）

```html
<div id="root" data-composition-id="main" data-start="0"
     data-width="1920" data-height="1080" data-duration="526.608" data-fps="30">
  <div id="scene01" data-composition-id="scene01"
       data-composition-src="compositions/scene01.html"
       data-start="0" data-duration="26.328" data-track-index="1"
       data-width="1920" data-height="1080"></div>
  <!-- …每场一个，data-start 累加 = 前场 start+duration … -->
  <audio id="narr" src="narr_full.mp3" data-start="0"
         data-duration="526.608" data-track-index="20" data-volume="1"></audio>
</div>
<script>
  window.__timelines = window.__timelines || {};
  window.__timelines["main"] = gsap.timeline({ paused: true });
</script>
```

要点：
- 每场的 `data-start` = 前一场的 `start + duration`（从 timeline-full.json 的每场 total 累加得到）。
- 全片 `data-duration` = 所有场 total 之和（= narr_full.mp3 实测时长）。
- `<audio>` 必须是 host root 的**直接子元素**（绝不放子合成 template 内）。
- 每场 `data-duration` = 该场 total（配音时长），动效要在场内安排完。

## 3. 动效运行时（GSAP paused timeline）

- 每场建**恰好一个** `gsap.timeline({ paused: true })`，同步构建。
- 用 `tl.fromTo(el, {y:26, opacity:0}, {y:0, opacity:1, duration:0.6, ease:"power3.out"}, at)` 做入场。
- `at` 是「场景内相对秒数」，就是音画同步要对齐的核心参数。
- SVG 线稿绘制用 `getTotalLength()` 设 `strokeDasharray`/`strokeDashoffset`，再 `tl.to` 把 offset 归 0。

```js
function prep(id) {
  const p = document.getElementById(id);
  if (!p) return;
  const len = p.getTotalLength();
  p.style.strokeDasharray = len;
  p.style.strokeDashoffset = len;
}
["belt","link"].forEach(prep);
tl.to("#belt", { strokeDashoffset: 0, duration: 0.7, ease: "power2.out" }, 3.6);
```

## 4. 确定性规则（会静默坏、要主动避开）

- 不用 `<br>` 写正文换行（用块级 div 分行）。
- 只 tween 视觉属性允许列表（transform/opacity/strokeDashoffset 等），不 tween `display`/`visibility`。
- 不写 `repeat: -1` 无限循环；不用 `Math.random` / 时钟 / 网络。
- 被 transform 的元素必须是 block 级且有尺寸。
- 每个 `id` 全局唯一；子合成内部 id 建议加场景前缀（但本项目用短 id，靠「每场独立 template + getElementById 作用域」也未冲突——稳妥起见仍建议唯一）。

## 5. 常见 check 输出释义

`npx hyperframes check .` 输出分 Lint / Runtime / Layout / Motion / Contrast 五组。

- `container_overflow` / `text_box_overflow`（info/error）→ 文字或内容超出卡片，要加高卡片或缩小字号。
- `content_overlap`（error）→ 两个文本块基线重叠（如标题 y 与副标题 y 差 < 字号），拉开 y 或加大 margin。
- `connector_orphan`（info，非阻塞）→ 连线在两端点都未上场时就可见；属提示，可忽略或把 line 的显示绑到端点入场之后。

## 6. 审核图（snapshot）

```bash
npx hyperframes@0.8.58 snapshot . -o snapshots/review-v3 --at 23,45,69,100,150,200,228,270,330,410,470,515
```

- `--at` 是**全片绝对秒数**（不是场景内秒数），要根据 index.html 里每场的 data-start 选点。
- 出 PNG 关键帧 + contact-sheet.jpg（网格大图）。
- 用 `--no-end` 只截指定时刻，不加末尾帧。

## 7. 渲染（render）

```bash
export PATH="$(pwd)/../.fftools:$PATH"   # 注入本地 ffmpeg/ffprobe
npx hyperframes@0.8.58 render . -o 非车险新规解读-完整版-v4.mp4 -q delivery
```

- 8 分钟量级、约 15800 帧（30fps × 526s）、硬件 GPU（drawelement capture）。
- 交付后 ffprobe 核对：1920×1080、h264 + aac、时长 = 配音总长。