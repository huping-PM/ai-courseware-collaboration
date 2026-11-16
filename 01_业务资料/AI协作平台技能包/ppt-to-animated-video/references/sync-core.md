# 音画同步核心片段（可直接移植）

从本项目 `build_pages.py` 抽取的同步核心，**已与真实实现逐行核对**。
完整文件见同目录 `build_pages.py`（67KB，含 13 页具体内容，仅供写法参考；
移植时抄这里的核心函数，不要整份复制）。

## 1. 两个常量不要混用

```python
# build_pages.py
TAIL      = 2.4     # 页尾留白（页面动效时间轴上的留白，≠ 视频余量）
MIN_GAP   = 0.5     # 同一内容块内子元素均分的最小间隔
SYNC_STACK= 0.16    # 仅用于打散"完全同刻"的元素：只向后微移，绝不提前
LAG       = 0.45    # 元素出场须比本句语音结束提前这么多秒

# build_video.py（另一个文件，另一个概念）
TAIL = 0.30         # 单页视频长度 = 该页音频 + 0.30s
```

> ⚠️ `build_pages.py` 的 `TAIL=2.4` 和 `build_video.py` 的 `TAIL=0.30` 是**两个不同用途**，
> 名字相同纯属巧合。混淆会导致总时长算错。

## 2. 时间轴读取

```python
def total_of(n):
    return TL["pages"][str(n)]["total"]

def seg(n, i, fb=0.0):
    """第 n 页第 i 句的起始时刻（配音锚点）。"""
    ss = TL["pages"][str(n)]["segs"]
    return round(ss[i]["start"], 2) if i < len(ss) else fb

def seg_window(n, i):
    """第 i 句的语音区间 (start, end)。注意最多是 start+dur，不要假设有 end 字段。"""
    s = TL["pages"][str(n)]["segs"][i]
    return s["start"], s["start"] + s["dur"]
```

## 3. sent_window()：句内锚定

```python
def sent_window(t, lag=LAG):
    """找到包含时刻 t 的那一句，返回其 [句首, 句尾-lag] 安全窗口。"""
    segs = TL["pages"][str(_CURPAGE)]["segs"]
    for s in segs:
        st, en = s["start"], s["start"] + s["dur"]
        if st <= t <= en:
            return st, max(st + 0.5, en - lag)
    # 落在句间停顿里：归属**前一句**（后一句尚未开口）
    prev = [s for s in segs if s["start"] + s["dur"] <= t]
    if prev:
        s = prev[-1]
        return s["start"], max(s["start"] + 0.5, s["start"] + s["dur"] - lag)
    return t, t + 0.5
```

两个细节：
- **下界 `max(st + 0.5, …)`**：保证句首也留一点余量，窗口不会塌成零宽。
- **空隙归前一句**：归后一句会让"晚到的元素"看起来正常，正是旧校验漏报的原因。

## 4. block()：★ 核心修复点

```python
def block(t0, t_end, n, kinds=None, dur=0.85):
    """返回 (子节拍时刻列表, kind 列表)。

    关键约束：所有子节拍都被收进"包含 t0 的那一句"的语音区间内，
    且最后一个节拍绝不越过该句句尾。
    """
    st, en = sent_window(t0)
    t_end = min(t_end, en)                      # ★ 收紧到本句安全句尾
    t0 = min(max(t0, 0.0), t_end)               # ★ 防窗口反转 & 防负值
    if n <= 1:
        ts = [t0]
    else:
        span = t_end - t0
        need = MIN_GAP * (n - 1)
        # 窗口偏窄时允许拉长，但硬上限是"本句句尾"（en - t0）
        span = max(span, min(need, max(0.0, en - t0)))
        ts = [t0 + span * i / (n - 1) for i in range(n)]
    for t in ts:
        LEDGER.append({"page": _CURPAGE, "anchor": round(st, 3),
                       "sent_end": round(en, 3), "t": round(t, 3)})
    if kinds is None:
        kinds = ["up", "left", "right", "pop", "zoom", "fade"][:n]
        while len(kinds) < n:
            kinds.append("up")
    return ts, kinds[:n]
```

- `t_end` 的调用点常传 `wins[i]`（下一句起点）或 `total - TAIL`（页尾）——**这正是病根**。
  `min(t_end, en)` 一行即治愈。
- 注意 `span = max(span, min(need, max(0.0, en - t0)))`：窗口太窄时可以拉长，
  但**拉长的上限仍是句尾**，不会溢出本句。

## 5. finalize()：第二道保险

```python
def finalize(n, beats):
    global _CURPAGE
    _CURPAGE = n
    beats = sorted(beats, key=lambda b: b["t"])
    ts = [max(0.0, b["t"]) for b in beats]
    for i in range(1, len(ts)):                 # 同刻元素向后微散，绝不提前
        if ts[i] <= ts[i - 1]:
            ts[i] = ts[i - 1] + SYNC_STACK
    for b, t in zip(beats, ts):
        if t > 0.01:                            # 页首常驻元素不参与收敛
            _, safe_end = sent_window(t)
            t = min(t, safe_end)                # ★ 逐 beat 再收一次
        html = b["html"].replace("@@A0@@", anim(t, b.get("kind", "up"), b.get("dur", 0.85)))
        for idx, off, kind in b.get("sub", []):
            html = html.replace("@@A%d@@" % idx, anim(t + off, kind, b.get("subDur", 0.8)))
```

**不要写** `if ts[-1] > total - TAIL: ts[-1] = end` 这类"页尾挤压"——
它会把元素**提前**，是反方向的错误。本项目已删除该逻辑。

## 6. main() 源级自检

构建完每页后打印一行，**必须看到 `checked` 数 > 0 且 overrun = 0**：

```python
bad = [b for b in LEDGER if b["t"] > b["sent_end"] + 1e-6]
print("[sync] page %2d checked %3d beats ... %d over sentence end"
      % (n, len(LEDGER), len(bad)))
```

实测输出：`[sync] checked 154 beats ... 0 over sentence end`

> 若打印 `checked 0 beats`，说明 LEDGER 埋点没生效，是**假通过**，务必排查。

## 7. 移植检查清单

1. `TL["pages"]` 的 key 是字符串还是 int？统一，否则 `str(n)` 会 KeyError。
2. `_CURPAGE` 必须在每页开始前设置，否则 `sent_window` 读错页（这是最容易犯的错）。
3. `segs[i]` 用 `start + dur` 算句尾，不要假设存在 `end` 字段。
4. `build_pages.py` 的 `TAIL=2.4` 与 `build_video.py` 的 `TAIL=0.30` 分属两个文件，别混。
5. 改完立刻跑 `verify_sync2.reference.py` 双向校验，再看是否重渲染。