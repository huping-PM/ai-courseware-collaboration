# 数据结构

入口是 UTF-8 JSON 对象：`title`、`subtitle`、`groups`。可选 `rootTitle`（地图中央简短名，默认产品方案）、`date`（展示文本，不自动编造日期）。所有说明为纯文本；支持正文里的 `[名称](https://...)` 链接，不接受任意 HTML。

每个 group：`title`（无需手写序号）、`subtitle`、非空 `sections`。

每个 section：`title`、`structure`（`comparison`、`modules`、`conditional`）、非空 `topics`。

每个 topic：

- `title`、`items`（字符串数组，常用前缀“业务问题：”“方案方向：”“产品形态：”“优点：”“劣势：”“选择理由：”）。
- `recommended`：可选布尔值，模板渲染独立“推荐”标签，标题不用再加【推荐】。
- `priority`：可选数字 1/2/3。只对需要优先级的模块设置。
- `modules`：可选数组，各项 `{title, items:[用途说明]}`。仅在右侧和全文中呈现，不成为导图节点。
- `images`：可选数组，各项 `{src, title}`，src 是相对输入 JSON 的本地图片路径（PNG/JPG/WebP/SVG）。同一节点的多图视作一组比较；无需业务专用的图片索引或裁切常量。

比较型节点默认核心问题在首、推荐结论在末；推荐内容由编写者判断，脚本不替你制造结论。条件型与模块型无需推荐结论。示例中的优先级与方案只是演示，不应用到新业务。

运行：

```text
node <技能目录>/scripts/build.cjs <方案.json> <输出目录>
```

使用模板需要 Node.js；输出 HTML 本身不依赖 Node 或网络。默认不覆盖已有输出，确认是本次要更新的方案时可加 `--force`。输出 `方案数据.json` 中图片路径已指向交付目录内资源，后续可以直接以它为输入更新。
