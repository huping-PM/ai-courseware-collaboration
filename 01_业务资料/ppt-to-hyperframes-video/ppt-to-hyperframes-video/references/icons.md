# 元素图标库（每页必加，淡蓝圆底 + 深蓝 SVG 线条）

## 规范

- 图标容器 `.ico`：`background:#D8E6F3; border-radius:50%; display:flex; align-items:center; justify-content:center;`
- SVG 线条 class `.iconline`：`fill:none; stroke:#1F4E79; stroke-width:2.6; stroke-linecap:round; stroke-linejoin:round;`
- 深蓝底药丸里的图标：改 `.tico`（`background:rgba(255,255,255,0.22)`）+ `.iconline{stroke:#FFFFFF}`。
- viewBox 统一 `0 0 32 32`，svg 尺寸按容器缩放（如容器 72px 配 svg 42px）。

## 现成图标（本项目用过的，直接复用 path 的 d 值）

| 语义 | SVG path |
|---|---|
| 文档/文件 | `<path d="M6 4h13l7 7v17H6z"/><path d="M19 4v7h7"/><path d="M11 18h10M11 23h6"/>` |
| 发票/报表 | `<path d="M6 8h20v16H6z"/><path d="M6 12h20M12 12v12"/><circle cx="21" cy="18" r="2.5"/>` |
| 齿轮/监管 | `<circle cx="16" cy="16" r="9"/><circle cx="16" cy="16" r="3.5"/><path d="M16 2v4M16 26v4M2 16h4M26 16h4"/>` |
| 靶心/问题导向 | `<circle cx="16" cy="16" r="10"/><circle cx="16" cy="16" r="4"/><circle cx="16" cy="16" r="1.2" fill="#1F4E79"/>` |
| 网格/分类 | `<rect x="3" y="3" width="11" height="11" rx="2"/><rect x="18" y="3" width="11" height="11" rx="2"/><rect x="3" y="18" width="11" height="11" rx="2"/><rect x="18" y="18" width="11" height="11" rx="2"/>` |
| 折线/趋势 | `<path d="M4 16h6l3-8 5 16 3-8h7"/>` |
| 台阶/稳步 | `<path d="M4 26h5l4-8h4l4 8h7"/><path d="M4 26h24"/>` |
| 数据库 | `<ellipse cx="16" cy="8" rx="8" ry="3.5"/><path d="M8 8v16c0 1.9 3.6 3.5 8 3.5s8-1.6 8-3.5V8"/><path d="M8 16c0 1.9 3.6 3.5 8 3.5s8-1.6 8-3.5"/>` |
| 列表/清单 | `<path d="M7 8h18M7 16h18M7 24h12"/><circle cx="23" cy="24" r="3.5"/>` |
| 盾牌/保障 | `<path d="M16 4l10 6v12l-10 6-10-6V10z"/><path d="M6 10l10 6 10-6M16 16v12"/>` |
| 人物/责任 | `<circle cx="12" cy="11" r="4"/><path d="M4 26c0-4.4 3.6-8 8-8s8 3.6 8 8"/><path d="M22 8a3 3 0 1 0 0 6M24 20c2 0 4 1.6 4 4"/>` |
| 地球/环境 | `<circle cx="16" cy="16" r="11"/><path d="M6 7c-1 2-1 4 0 6M26 7c1 2 1 4 0 6M11 15c2 1 3 2 5 2s3-1 5-2"/>` |
| 时钟/动态 | `<path d="M16 6a10 10 0 1 0 10 10"/><path d="M16 6v5l3.5 3.5"/><path d="M26 4l-1 1 1 1v-2z"/>` |
| 增长/上升 | `<path d="M5 24l7-9 6 5 9-12"/><path d="M20 8h7v7"/>` |
| 三角警示 | `<path d="M16 4l10 18H6z"/><path d="M16 13v5"/><circle cx="16" cy="22" r="1.5"/>` |
| 柱状图/数据 | `<path d="M5 6h22v20H5z"/><path d="M9 23V13M16 23V6M23 23v-7"/>` |
| 系统/电脑 | `<rect x="4" y="6" width="24" height="20" rx="2"/><line x1="16" y1="6" x2="16" y2="26"/><line x1="4" y1="12" x2="28" y2="12"/>` |
| 喇叭/业务 | `<path d="M5 14l5-4v12l-5-4z"/><path d="M10 10h12l5 4-5 4H10z"/>` |
| 邮箱/信封 | `<path d="M6 8h20v16H6z"/><path d="M6 8l10 8 10-8"/>` |

## 使用姿势

```html
<div class="ico" style="width:72px;height:72px;margin:0 auto;">
  <svg width="42" height="42" viewBox="0 0 32 32" fill="none">
    <path class="iconline" d="M6 4h13l7 7v17H6z"/>
    <path class="iconline" d="M19 4v7h7"/>
  </svg>
</div>
```

- 卡片内图标放顶部居中（`margin:0 auto`），或按「图标+序号」组合靠左（见 sync.md 布局技巧）。
- 深蓝药丸（tag）内用 `.tico` + `.iconline{stroke:#FFFFFF}` 白线条变体。