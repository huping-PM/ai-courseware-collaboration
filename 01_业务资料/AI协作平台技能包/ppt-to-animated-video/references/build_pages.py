# -*- coding: utf-8 -*-
"""build_pages.py — 把 12 页 .slide 版式还原为 1920×1080 的 HTML 动画页。

动画模型（每个"内容块"在它的配音窗口内渐进展开）：
- 一个块 = 一个静态容器 + N 个带 data-anim 的内部元素；
- 容器里用 @@A0@@ @@A1@@ … 占位，由节拍表分别赋予各自的入场时刻；
- 每个块的子节拍铺满 [块起点, 下一块起点]，从而
  (1) 不会整页一起出现；(2) 相邻两次入场间隔受控，画面全程有推进；
- 另加「进度脊线」+ 光斑漂移，任何一帧都还有连续微动。
"""
import json
import math
import os

BASE = os.path.dirname(os.path.abspath(__file__))
PAGES_DIR = os.path.join(BASE, "html", "pages")
TL = json.load(open(os.path.join(BASE, "timeline.json"), encoding="utf-8"))
os.makedirs(PAGES_DIR, exist_ok=True)

S = 1.5
GL = "#34C77B"
DEEP = "#0F3D2E"
MIST = "#E8F7EF"
NEU = "#5B6B63"

TAIL = 2.4          # 页尾留白
MIN_GAP = 0.5       # 同一内容块内、子元素的均分最小间隔（spread 用）
SYNC_STACK = 0.16   # 仅用于打散"完全同刻"的元素：只向后微移，绝不提前
LAG = 0.45          # 元素出场须比本句语音结束提前这么多秒（留出看清的时间）

# ===== 音画同步核心 =====
# 病症：block(t0, t_end, n) 原先一律按调用方给的 t_end 铺开，而多数调用点把
#       t_end 传成"下一句的起始时刻"（wins[i]）或"页尾"（total-TAIL）。
#       于是同一句里的最后一个元素被推到**本句语音读完之后**才出现——
#       也就是"配音已经读完，画面才出现对应文字"。
# 药方：把窗口末端强制收进 "包含 t0 的那一句" 的语音区间内（末端再留 LAG 秒余量）。
#       这样元素只会在本句被念到的时间里出现，既不会提前，也不会拖到下一句。
_CURPAGE = 1        # 由 main() 在调用每页函数前设置
LEDGER = []         # 记录每个由 block() 产出的入场时刻，供同步自检


def px(v):
    return round(v * S, 2)


def total_of(n):
    return TL["pages"][str(n)]["total"]


def seg(n, i, fb=0.0):
    ss = TL["pages"][str(n)]["segs"]
    return round(ss[i]["start"], 2) if i < len(ss) else fb


def seg_window(n, i):
    """第 i 句的语音区间 (start, end)。"""
    s = TL["pages"][str(n)]["segs"][i]
    return s["start"], s["start"] + s["dur"]


def sent_window(t, lag=LAG):
    """找到包含时刻 t 的那一句，返回其 [句首, 句尾-lag] 安全窗口。"""
    segs = TL["pages"][str(_CURPAGE)]["segs"]
    for s in segs:
        st, en = s["start"], s["start"] + s["dur"]
        if st <= t <= en:
            return st, max(st + 0.5, en - lag)
    # 落在句间停顿里：归属前一句（后一句尚未开口）
    prev = [s for s in segs if s["start"] + s["dur"] <= t]
    if prev:
        s = prev[-1]
        return s["start"], max(s["start"] + 0.5, s["start"] + s["dur"] - lag)
    return t, t + 0.5


def spread(t0, t_end, n, min_gap=MIN_GAP):
    """把 n 个子节拍均匀铺在 [t0, t_end]。"""
    if n <= 1:
        return [t0]
    span = max(t_end - t0, min_gap * (n - 1))
    return [t0 + span * i / (n - 1) for i in range(n)]


def anim(t, kind="up", dur=0.85, ease="outCubic"):
    k0 = {"up": {"op": 0, "y": 39}, "down": {"op": 0, "y": -39},
          "left": {"op": 0, "x": -58}, "right": {"op": 0, "x": 58},
          "zoom": {"op": 0, "s": 0.9}, "clip": {"op": 1, "clip": 0},
          "pop": {"op": 0, "y": 24, "s": 0.94}, "pulse": {"op": 0.25, "s": 0.75},
          "grow": {"op": 0.2, "x": -40}, "fade": {"op": 0}}.get(kind, {"op": 0, "y": 39})
    k0 = dict(k0)
    k0["t"] = round(t, 3)
    k1 = {"t": round(t + dur, 3), "ease": ease}
    for k in k0:
        if k != "t":
            k1[k] = {"op": 1, "y": 0, "x": 0, "s": 1, "clip": 100}[k]
    return "data-anim='" + json.dumps([k0, k1], ensure_ascii=False) + "'"


def block(t0, t_end, n, kinds=None, dur=0.85):
    """返回 (子节拍时刻列表, 对应 kind 列表)。

    关键约束：所有子节拍都被**收进包含 t0 的那一句的语音区间**，
    且最后一个节拍绝不越过该句句尾。这样元素只会在本句被念到的
    时间里出现——既不会提前（画面先动、语音后到），也不会滞后
    （配音读完、画面才出现）。
    """
    st, en = sent_window(t0)
    t_end = min(t_end, en)
    t0 = min(max(t0, 0.0), t_end)
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


# ---------------- 通用组件 ----------------
def ico(name, size, color, extra=""):
    return (f'<i class="fa-solid fa-{name}" style="font-size:{px(size)}px;color:{color};'
            f'line-height:1;{extra}"></i>')


def icobox(name, box, isz, bg, fg, radius=12, extra=""):
    return (f'<div class="icobox" style="width:{px(box)}px;height:{px(box)}px;'
            f'border-radius:{px(radius)}px;background:{bg};{extra}">{ico(name, isz, fg)}</div>')


def tag(text, fg="#1F9D5F", bg=MIST, size=12):
    return (f'<div style="display:inline-flex;align-items:center;padding:0 {px(10)}px;'
            f'height:{px(size + 12)}px;border-radius:9999px;background:{bg};'
            f'font-size:{px(size)}px;font-weight:600;color:{fg};white-space:nowrap">{text}</div>')


def hdr(title, chip, solid=False):
    cb = GL if solid else MIST
    cf = "#FFFFFF" if solid else DEEP
    bd = "" if solid else "border:1px solid rgba(52,199,123,0.45);"
    return f'''<div style="position:absolute;left:{px(64)}px;top:{px(24)}px;width:{px(1152)}px;height:{px(88)}px;display:flex;align-items:center;gap:{px(14)}px;z-index:6">
<div style="width:{px(5)}px;height:{px(38)}px;border-radius:{px(3)}px;background:{GL};flex:none"></div>
<div style="font-size:{px(34)}px;font-weight:700;color:{DEEP};line-height:1.4">{title}</div>
<div style="margin-left:auto;display:flex;align-items:center;padding:0 {px(16)}px;height:{px(30)}px;border-radius:9999px;background:{cb};{bd}font-size:{px(13)}px;font-weight:600;color:{cf};letter-spacing:{px(0.5)}px">{chip}</div>
</div>'''


NPC = len(TL["pages"])   # 总页数（13）


def footer(n):
    return (f'<div style="position:absolute;left:{px(64)}px;top:{px(640)}px;width:{px(1152)}px;'
            f'height:{px(56)}px;display:flex;align-items:center;justify-content:space-between;'
            f'border-top:1px solid rgba(52,199,123,0.18);z-index:6;font-size:{px(14)}px;color:{NEU}">'
            f'<span>非车险综合治理政策解读</span><span>{n:02d} / {NPC}</span></div>')


def spine(total):
    return (f'<div {anim(0.8, "clip", max(3.0, total - 3.0), "linear")} '
            f'style="position:absolute;left:{px(64)}px;top:{px(638)}px;width:{px(1152)}px;'
            f'height:{px(4)}px;border-radius:{px(2)}px;z-index:7;'
            f'background:linear-gradient(90deg,#34C77B 0%,#1F9D5F 100%)"></div>')


def marker(total):
    """页脚游标：沿进度轨全程匀速移动，保证任何一帧都有连续可见位移。"""
    d = json.dumps([{"t": 0.8, "x": 0, "op": 0},
                    {"t": 1.4, "x": 0, "op": 1, "ease": "outCubic"},
                    {"t": round(total - 2.6, 1), "x": px(1128), "op": 1, "ease": "linear"}])
    return (f'<div data-anim=\'{d}\' style="position:absolute;left:{px(64)}px;top:{px(632)}px;'
            f'width:{px(22)}px;height:{px(16)}px;z-index:8">'
            f'<div style="width:{px(16)}px;height:{px(16)}px;border-radius:9999px;background:{GL};'
            f'box-shadow:0 0 {px(10)}px rgba(52,199,123,0.85)"></div></div>')


def bloom(total, top, side, val, size, alpha, ax=140, ay=90, phase=0.0):
    """大面积漂移光晕：以固定周期循环呼吸，覆盖广、位移大，是"无长静止"的主力。"""
    x = f"right:{px(val)}px" if side == "right" else f"left:{px(val)}px"
    cycle = 8.6
    n = max(1, int(max(total, cycle) / cycle))
    ks = [{"t": 0, "x": 0, "y": 0, "s": 1.0}]
    for c in range(n):
        b = c * cycle
        ks.append({"t": round(b + cycle * 0.25, 2), "x": round(ax * 0.95, 1),
                   "y": round(ay * 0.95, 1), "s": 1.14, "ease": "inOutCubic"})
        ks.append({"t": round(b + cycle * 0.50, 2), "x": round(-ax * 0.85, 1),
                   "y": round(-ay * 0.85, 1), "s": 0.94, "ease": "inOutCubic"})
        ks.append({"t": round(b + cycle * 0.75, 2), "x": round(ax * 0.55, 1),
                   "y": round(-ay * 0.45, 1), "s": 1.06, "ease": "inOutCubic"})
        ks.append({"t": round(b + cycle, 2), "x": 0, "y": 0, "s": 1.0, "ease": "inOutCubic"})
    d = json.dumps(ks)
    return (f'<div data-anim=\'{d}\' style="position:absolute;top:{px(top)}px;{x};'
            f'width:{px(size)}px;height:{px(size)}px;border-radius:9999px;'
            f'background:radial-gradient(circle,rgba(52,199,123,{alpha}) 0%,rgba(52,199,123,0) 68%)"></div>')


def kenburns_attr(total):
    """缓慢推镜（分段往复，幅度更大）：大面积连续变化。"""
    ks = [{"t": 0, "s": 1.0, "x": 0, "y": 0}]
    span = max(total, 6.0)
    n = 3
    for i in range(1, n + 1):
        s = 1.0 + 0.045 * (i if i <= 2 else 2)
        ks.append({"t": round(span * i / n, 1),
                   "s": round(s, 4),
                   "x": round(-38 * (1 if i % 2 else -0.5), 1),
                   "y": round(-26 * (1 if i % 2 else -0.6), 1),
                   "ease": "inOutCubic"})
    return "data-anim='" + json.dumps(ks) + "'"


def scan(total, width=700, cycle=6.0, alpha=0.13, z=5):
    """扫描光带：按固定周期循环横穿画面（两端均在画面外，折返不可见）。
    这是最可靠的"永远在动"的运动源，保证任意时刻都有大面积线性位移。"""
    span_in = 1920 + width * 2
    K = int(total / cycle) + 2
    ks = []
    for k in range(K):
        t0 = k * cycle
        ks.append({"t": round(t0, 2), "x": -width - 20})
        ks.append({"t": round(t0 + cycle * 0.88, 2), "x": round(-width - 20 + span_in, 1),
                   "ease": "linear"})
    d = json.dumps(ks)
    return (f'<div data-anim=\'{d}\' data-decor="1" style="position:absolute;left:0;top:0;width:{px(width)}px;'
            f'height:100%;z-index:{z};pointer-events:none;'
            f'background:linear-gradient(90deg,rgba(52,199,123,0) 0%,'
            f'rgba(52,199,123,{alpha * 0.35:.3f}) 30%,rgba(52,199,123,{alpha:.3f}) 50%,'
            f'rgba(52,199,123,{alpha * 0.35:.3f}) 70%,rgba(52,199,123,0) 100%)"></div>')


def sub(txt, size, color, weight=0, lh=1.7):
    w = f"font-weight:{weight};" if weight else ""
    return f'<span style="font-size:{px(size)}px;color:{color};{w}line-height:{lh}">{txt}</span>'


def check(txt, color, size=14, ic=GL):
    return (f'<div style="display:flex;gap:{px(9)}px;align-items:flex-start">'
            f'{ico("check", size * 0.86, ic, f"margin-top:{px(3)}px;flex:none")}'
            f'<span style="font-size:{px(size)}px;color:{color};line-height:1.65;flex:1">{txt}</span></div>')


# ========== 装配 ==========
def finalize(n, beats):
    global _CURPAGE
    _CURPAGE = n
    total = total_of(n)
    g = GLOWS[n]
    title, chip, solid = HDRS[n]
    parts = []
    # 底色
    parts.append(f'<div style="position:absolute;inset:0;background:#F7FBF8"></div>')
    # 大面积漂移光晕（两层，相位错开）
    parts.append(bloom(total, g[0], g[1], g[2], g[3], g[4],
                       ax=185, ay=125, phase=0.0))
    side2 = "left" if g[1] == "right" else "right"
    parts.append(bloom(total, -80, side2, -160, 620, g[4] * 0.75, ax=155, ay=-140, phase=0.5))
    parts.append(bloom(total, 340, g[1], -260, 540, g[4] * 0.6, ax=-165, ay=110, phase=0.25))
    # 头部
    parts.append(f'<div {anim(0.3, "down", 0.8)} style="position:absolute;left:0;top:0;width:100%;z-index:6">'
                 + hdr(title, chip, solid) + '</div>')
    # 内容组：元素出场时刻一律采用各页标注的旁白锚点（seg(n,i)），保证与语音同步。
    # 三重约束：
    #   ① 绝不提前——提前会出现"画面先动、语音后到"；
    #   ② 完全同刻的块内子元素按 SYNC_STACK 向后微散；
    #   ③ 再统一收进"该元素所属那一句"的语音区间内（减去 LAG 余量），
    #      避免堆叠后越过句尾，造成"配音读完画面才出现"。
    beats = sorted(beats, key=lambda b: b["t"])
    ts = [max(0.0, b["t"]) for b in beats]
    for i in range(1, len(ts)):
        if ts[i] <= ts[i - 1]:
            ts[i] = ts[i - 1] + SYNC_STACK
    inner = []
    for b, t in zip(beats, ts):
        if t > 0.01:                       # 页首常驻元素不参与收敛
            _, safe_end = sent_window(t)
            t = min(t, safe_end)
        html = b["html"]
        html = html.replace("@@A0@@", anim(t, b.get("kind", "up"), b.get("dur", 0.85)))
        for idx, off, kind in b.get("sub", []):
            html = html.replace("@@A%d@@" % idx, anim(t + off, kind, b.get("subDur", 0.8)))
        for i in range(8):
            html = html.replace("@@A%d@@" % i, anim(t + 0.02 * i, "fade", 0.4))
        inner.append(html)
    parts.append(f'<div style="position:absolute;inset:0;z-index:3">'
                 + "".join(inner) + '</div>')
    parts.append(spine(total))
    parts.append(footer(n))
    # 注：原先为「消除长静止」而加的两条循环扫描光带与页脚游标已移除——
    # 它们与配音无关，属于"为动而动"的干扰层。
    return '<div class="stage">' + "".join(parts) + "</div>"


def B(t, kind, html, sub=None, dur=0.85):
    return {"t": t, "kind": kind, "html": html, "sub": sub or [], "dur": dur}


# ================= 各页 =================
def page_01():
    """新第 1 页 · 背景：无序竞争与经营质量失衡（对应原第 1 页 seg0..seg2）。"""
    total = total_of(1)
    b = []
    # ① 主视觉（页首常驻，配 seg0「这些问题并不是个例」）
    b.append(B(1.0, "clip", f'''<div @@A0@@ style="position:absolute;left:{px(64)}px;top:{px(112)}px;width:{px(1152)}px;height:{px(288)}px;border-radius:{px(16)}px;overflow:hidden;background:{MIST};box-shadow:0 {px(6)}px {px(24)}px rgba(15,61,46,0.06);z-index:3">
<img src="../assets/risk_scene.png" style="width:100%;height:100%;object-fit:cover;display:block"></div>''', dur=1.0))
    b.append(B(1.0, "fade", f'<div @@A0@@ style="position:absolute;left:{px(64)}px;top:{px(112)}px;width:{px(1152)}px;height:{px(288)}px;border-radius:{px(16)}px;background:linear-gradient(180deg,rgba(15,61,46,0) 42%,rgba(15,61,46,0.84) 100%);z-index:4"></div>', dur=1.2))
    # 图上的标语 + 三行注解：锚在 seg1（"近年来……问题逐渐显现"，6.346~13.138s）
    s1 = seg(1, 1)
    b.append(B(s1 + 0.35, "left", f'<div @@A0@@ style="position:absolute;left:{px(90)}px;top:{px(300)}px;width:{px(520)}px;font-size:{px(21)}px;font-weight:700;color:#FFF;line-height:1.35;z-index:5">{sub("规模在涨，经营质量没有跟上", 21, "#FFF", 700, 1.35)}</div>'))
    w1 = seg_window(1, 1)
    ts, ks = block(s1 + 1.6, w1[1], 3, ["right", "right", "fade"])
    for i, (txt, c) in enumerate([("不计成本降低费率、放宽条款", "rgba(255,255,255,0.90)"),
                                  ("依靠高额手续费吸引客户", "rgba(255,255,255,0.90)"),
                                  ("→ 无序竞争、费用率虚高、应收保费较高", "#C9F5DC")]):
        b.append(B(ts[i], ks[i], f'<div @@A0@@ style="position:absolute;left:{px(620)}px;top:{px(346 + i * 30)}px;width:{px(566)}px;text-align:right;font-size:{px(14)}px;color:{c};z-index:5">{sub(txt, 14, c, lh=1.6)}</div>'))
    # ② 三张问题卡：每张落在 seg2（"部分机构为争夺业务……"，13.388~28.604s）窗口内的不同时段
    s2 = seg(1, 2)
    w2 = seg_window(1, 2)
    cards = [("scale-unbalanced", "无序竞争", "不计成本降低费率、放宽条款，把价格当作争夺业务的唯一手段，费率纪律被不断突破。", s2 + 0.4, False),
             ("arrow-trend-up", "费用率虚高", "依靠高额手续费吸引客户，费用支出持续走高、层层加码，挤压正常经营与风险管理投入。", s2 + 5.0, False),
             ("file-invoice", "应收保费较高", "保费尚未实际到账即行承保，承保与收费脱节，账面增长与现金流入相互背离。", s2 + 9.6, True)]
    for i, (ic, ti, de, t0, hl) in enumerate(cards):
        cls = "card-hl" if hl else "card"
        ibg = "rgba(255,255,255,0.22)" if hl else MIST
        ts, ks = block(t0, w2[1], 4, ["fade", "left", "up", "pop"])
        html = f'''<div @@A0@@ class="{cls}" style="position:absolute;left:{px(64 + i * 393)}px;top:{px(416)}px;width:{px(366)}px;height:{px(224)}px;padding:{px(18)}px {px(20)}px;display:flex;flex-direction:column;gap:{px(10)}px;z-index:3">
<div @@A1@@ style="display:flex;align-items:center;gap:{px(10)}px">{icobox(ic, 34, 17, ibg, "#FFFFFF" if hl else GL, 10)}
<div style="font-size:{px(17)}px;font-weight:700;color:{"#FFFFFF" if hl else DEEP}">{ti}</div></div>
<div @@A2@@ style="font-size:{px(14)}px;color:{"rgba(255,255,255,0.92)" if hl else NEU};line-height:1.65">{de}</div>
<div @@A3@@ style="margin-top:auto;height:{px(3)}px;border-radius:{px(2)}px;background:{"rgba(255,255,255,0.55)" if hl else "rgba(52,199,123,0.55)"};width:46%"></div></div>'''
        b.append(B(ts[0], ks[0], html,
                    sub=[(1, ts[1] - ts[0], "left"), (2, ts[2] - ts[0], "up"),
                         (3, ts[3] - ts[0], "pop")]))
    return b


def page_02():
    """新第 2 页 · 背景：治理持续深化（对应原第 1 页 seg3..seg6，时刻已基准归零）。"""
    total = total_of(2)
    end = total - TAIL
    b = []
    # 左侧：三阶段演进时间轴
    w0 = seg_window(2, 1)
    b.append(B(seg(2, 1) + 0.3, "left", f'''<div @@A0@@ style="position:absolute;left:{px(64)}px;top:{px(112)}px;width:{px(604)}px;display:flex;align-items:center;gap:{px(10)}px;z-index:3">
{ico("timeline", 18, GL)}<span style="font-size:{px(15)}px;color:{NEU};line-height:1.5">治理节奏：由单项规范走向系统治理</span></div>'''))
    stages = [("gavel", "2025", "STEP 1", "推进\u201c报行合一\u201d", "重点规范费用和费率，遏制无序竞争与费用率虚高，把费率纪律重新立起来。", seg(2, 1), w0[1], False),
              ("file-invoice", "2026", "STEP 2", "增加\u201c见费出单\u201d", "着力解决应收保费问题，把保费实际到账作为承保的前提条件。", seg(2, 1) + 3.4, seg_window(2, 1)[1], False),
              ("layer-group", "2026.08", "STEP 3", "《非车险综合治理行动方案》", "治理范围拓展到产品、业务经营、数据、中介和治理保障，由单项规范转向系统治理。", seg(2, 2), seg_window(2, 2)[1], True)]
    for i, (ic, yr, st, ti, de, t0, w_end, hl) in enumerate(stages):
        cls = "card-hl" if hl else "card"
        ibg = "rgba(255,255,255,0.22)" if hl else MIST
        ts, ks = block(t0, w_end, 5, ["fade", "left", "up", "grow", "pop"])
        html = f'''<div @@A0@@ class="{cls}" style="position:absolute;left:{px(64)}px;top:{px(150 + i * 160)}px;width:{px(604)}px;height:{px(144)}px;padding:{px(16)}px {px(18)}px;display:flex;flex-direction:row;align-items:center;gap:{px(14)}px;z-index:3">
<div @@A1@@ style="width:{px(74)}px;display:flex;flex-direction:column;align-items:center;gap:{px(3)}px;flex:none">
<div style="font-size:{px(23)}px;font-weight:700;color:{"#FFFFFF" if hl else GL};font-family:'Space Grotesk',sans-serif">{yr}</div>
<div style="font-size:{px(11)}px;font-weight:600;color:{"rgba(255,255,255,0.85)" if hl else NEU};letter-spacing:{px(0.5)}px">{st}</div></div>
<div style="width:1px;height:{px(82)}px;background:{"rgba(255,255,255,0.35)" if hl else "rgba(52,199,123,0.25)"};flex:none"></div>
<div style="flex:1;display:flex;flex-direction:row;align-items:center;gap:{px(12)}px">{icobox(ic, 36, 17, ibg, "#FFFFFF" if hl else GL, 10)}
<div @@A2@@ style="flex:1;display:flex;flex-direction:column;gap:{px(3)}px">
<div style="font-size:{px(16)}px;font-weight:700;color:{"#FFFFFF" if hl else DEEP};line-height:1.35">{ti}</div>
<div @@A3@@ style="font-size:{px(13)}px;color:{"rgba(255,255,255,0.94)" if hl else NEU};line-height:1.6">{de}</div></div></div>
<div @@A4@@ style="position:absolute;left:{px(18)}px;bottom:{px(0)}px;height:{px(3)}px;border-radius:{px(2)}px;background:{"rgba(255,255,255,0.5)" if hl else "rgba(52,199,123,0.5)"};width:{px(200)}px"></div></div>'''
        b.append(B(ts[0], ks[0], html,
                    sub=[(1, ts[1] - ts[0], "left"), (2, ts[2] - ts[0], "up"),
                         (3, ts[3] - ts[0], "grow"), (4, ts[4] - ts[0], "pop")]))
    # 右侧：主视觉 + 结论卡
    b.append(B(1.0, "clip", f'''<div @@A0@@ style="position:absolute;left:{px(686)}px;top:{px(112)}px;width:{px(530)}px;height:{px(344)}px;border-radius:{px(16)}px;overflow:hidden;background:{MIST};box-shadow:0 {px(6)}px {px(24)}px rgba(15,61,46,0.06);z-index:3">
<img src="../assets/reform_evolution.png" style="width:100%;height:100%;object-fit:cover;display:block"></div>''', dur=1.0))
    b.append(B(1.0, "fade", f'<div @@A0@@ style="position:absolute;left:{px(686)}px;top:{px(112)}px;width:{px(530)}px;height:{px(344)}px;border-radius:{px(16)}px;background:linear-gradient(180deg,rgba(15,61,46,0) 52%,rgba(15,61,46,0.80) 100%);z-index:4"></div>', dur=1.2))
    b.append(B(seg(2, 2) + 1.2, "up", f'<div @@A0@@ style="position:absolute;left:{px(712)}px;top:{px(380)}px;width:{px(480)}px;font-size:{px(16)}px;font-weight:700;color:#FFFFFF;line-height:1.45;z-index:5">{sub("治理从\u201c单项规范\u201d走向\u201c系统治理\u201d", 16, "#FFF", 700, 1.45)}</div>'))
    ts, ks = block(seg(2, 3), end, 2, ["up", "pop"])
    b.append(B(ts[0], ks[0], f'''<div @@A0@@ style="position:absolute;left:{px(686)}px;top:{px(472)}px;width:{px(530)}px;height:{px(168)}px;background:{MIST};border-radius:{px(14)}px;padding:{px(18)}px {px(20)}px;display:flex;gap:{px(12)}px;align-items:flex-start;border-left:{px(4)}px solid {GL};z-index:3">
<div @@A1@@>{ico("diagram-project", 20, "#1F9D5F", f"margin-top:{px(2)}px;flex:none")}</div>
<div @@A2@@ style="font-size:{px(15)}px;color:{DEEP};line-height:1.7;flex:1">涵盖 <b>产品、业务经营、数据、中介与治理保障</b> 多个方面，把过去分散推进的单项要求整合为统一的治理框架。</div></div>''',
              sub=[(1, 0.15, "zoom"), (2, ts[1] - ts[0], "up")]))
    return b


def page_03():
    total = total_of(3)
    end = total - TAIL
    b = []
    b.append(B(0.8, "left", f'''<div @@A0@@ style="position:absolute;left:{px(66)}px;top:{px(112)}px;width:{px(1150)}px;display:flex;align-items:center;gap:{px(12)}px;z-index:3">
{ico("shield-halved", 20, GL)}<span style="font-size:{px(16)}px;color:{NEU};line-height:1.5">非车险综合治理坚持四项基本原则，共同界定治理的力度与节奏</span></div>'''))
    cards = [("crosshairs", "01", "问题导向", "聚焦市场无序竞争、基础薄弱等突出问题，找准问题、靶向治理，不为治理而治理。", "找准问题", seg(3, 1), False),
             ("layer-group", "02", "分类施策", "立足非车险业务的多样性与复杂性，针对不同主体和业务分级分类、精准治理，避免一刀切。", "分级分类", seg(3, 2), False),
             ("hammer", "03", "先立后破", "科学把握治理节奏，做好新旧政策衔接，保障市场平稳运行和行业有序转型。", "新旧衔接", seg(3, 3), False),
             ("gauge-high", "04", "稳步推进", "加强全局谋划、过程管控和动态评估，让治理举措在实践中持续校准、滚动迭代。", "动态评估", seg(3, 4), True)]
    wins = [seg(3, 1), seg(3, 2), seg(3, 3), end]
    for i, (ic, no, ti, de, ft, t0, hl) in enumerate(cards):
        cls = "card-hl" if hl else "card"
        ibg = "rgba(255,255,255,0.22)" if hl else MIST
        ts, ks = block(t0, wins[i], 4, ["up", "right", "pop", "zoom"])
        html = f'''<div class="{cls}" style="position:absolute;left:{px(64 + i * 291.5)}px;top:{px(150)}px;width:{px(277.5)}px;height:{px(490)}px;padding:{px(20)}px {px(18)}px;display:flex;flex-direction:column;z-index:3">
<div @@A0@@ style="display:flex;align-items:center;gap:{px(10)}px">{icobox(ic, 44, 21, ibg, "#FFFFFF" if hl else GL, 12)}
<div style="font-size:{px(26)}px;font-weight:700;color:{"rgba(255,255,255,0.45)" if hl else MIST};font-family:'Space Grotesk',sans-serif">{no}</div></div>
<div @@A1@@ style="font-size:{px(19)}px;font-weight:600;color:{"#FFFFFF" if hl else DEEP};margin-top:{px(12)}px">{ti}</div>
<div @@A2@@ style="font-size:{px(15)}px;color:{"rgba(255,255,255,0.93)" if hl else NEU};line-height:1.7;margin-top:{px(8)}px">{de}</div>
<div @@A3@@ style="margin-top:auto;padding-top:{px(12)}px;display:flex;align-items:center;gap:{px(6)}px">
{ico("angle-right", 12, "#FFFFFF" if hl else GL)}<span style="font-size:{px(13)}px;font-weight:600;color:{"#FFFFFF" if hl else GL}">{ft}</span></div></div>'''
        b.append(B(ts[0], "fade", html,
                    sub=[(1, ts[1] - ts[0], "up"), (2, ts[2] - ts[0], "up"), (3, ts[3] - ts[0], "pop")]))
    return b


def page_04():
    total = total_of(4)
    end = total - TAIL
    b = []
    b.append(B(0.8, "left", f'''<div @@A0@@ style="position:absolute;left:{px(64)}px;top:{px(112)}px;width:{px(668)}px;height:{px(528)}px;border-radius:{px(16)}px;background:linear-gradient(135deg,#0F3D2E 0%,#14523C 100%);padding:{px(30)}px {px(32)}px;display:flex;flex-direction:column;overflow:hidden;z-index:3">
<div @@A1@@ style="display:flex;align-items:center;gap:{px(8)}px">
<div style="width:{px(18)}px;height:{px(2)}px;background:{GL}"></div>
<div style="font-size:{px(13)}px;font-weight:600;color:{GL};letter-spacing:{px(1.5)}px">TARGET WINDOW</div></div>
<div @@A2@@ style="font-size:{px(88)}px;font-weight:700;color:#FFF;line-height:1.5;letter-spacing:{px(-1)}px;margin-top:{px(10)}px">十五五</div>
<div @@A3@@ style="font-size:{px(16)}px;color:rgba(255,255,255,0.75);line-height:1.6;margin-top:{px(8)}px">治理不是一次性整顿<br>而是跨越五年的体系建设</div></div>''',
              sub=[(1, 0.7, "left"), (2, 1.5, "zoom"), (3, 2.6, "up")]))
    pts = ["市场无序竞争得到有效整治", "管理制度体系持续完善", "行业生态加快构建"]
    pts_end = [seg(4, 2), seg(4, 3), end]
    for i, p in enumerate(pts):
        ts, ks = block(seg(4, 1 + i), pts_end[i], 2, ["left", "grow"])
        b.append(B(ts[0], ks[0], f'<div @@A0@@ style="position:absolute;left:{px(98)}px;top:{px(508 + i * 36)}px;width:{px(620)}px;z-index:4">{check(p, "rgba(255,255,255,0.92)", 15, GL)}</div>',
                    sub=[(0, 0, ks[0])]))
    b.append(B(1.3, "clip", f'''<div @@A0@@ style="position:absolute;left:{px(750)}px;top:{px(112)}px;width:{px(466)}px;height:{px(360)}px;border-radius:{px(16)}px;overflow:hidden;background:{MIST};box-shadow:0 {px(6)}px {px(24)}px rgba(15,61,46,0.06);z-index:3">
<img src="../assets/goal_vision.png" style="width:100%;height:100%;object-fit:cover;display:block"></div>''', dur=1.0))
    ts, ks = block(seg(4, 4), end, 2, ["up", "pop"])
    b.append(B(ts[0], ks[0], f'''<div @@A0@@ style="position:absolute;left:{px(750)}px;top:{px(486)}px;width:{px(466)}px;height:{px(154)}px;background:{MIST};border-radius:{px(14)}px;padding:{px(16)}px {px(18)}px;display:flex;gap:{px(12)}px;align-items:flex-start;border-left:{px(4)}px solid {GL};z-index:3">
<div @@A1@@>{ico("bullseye", 20, "#1F9D5F", f"margin-top:{px(2)}px;flex:none")}</div>
<div @@A2@@ style="font-size:{px(15)}px;color:{DEEP};line-height:1.7;flex:1">最终指向 <b>规范化、专业化、精细化</b> 的非车险市场体系</div></div>''',
              sub=[(1, 0.15, "zoom"), (2, ts[1] - ts[0], "up")]))
    return b


def page_05():
    total = total_of(5)
    end = total - TAIL
    b = []
    b.append(B(0.8, "left", f'''<div @@A0@@ style="position:absolute;left:{px(64)}px;top:{px(112)}px;width:{px(366)}px;height:{px(528)}px;border-radius:{px(16)}px;background:linear-gradient(135deg,#34C77B 0%,#1F9D5F 100%);padding:{px(26)}px {px(24)}px;display:flex;flex-direction:column;overflow:hidden;z-index:3">
<div @@A1@@>{icobox("file-shield", 52, 25, "rgba(255,255,255,0.22)", "#FFFFFF", 14)}</div>
<div @@A2@@ style="font-size:{px(24)}px;font-weight:700;color:#FFFFFF;line-height:1.35;margin-top:{px(18)}px">风险在动<br>产品管理就必须<br>从源头入手</div>
<div @@A3@@ style="margin-top:auto;display:flex;flex-direction:column;gap:{px(8)}px">
<div style="display:flex;flex-wrap:wrap;gap:{px(6)}px">{''.join(tag(t, "#FFFFFF", "rgba(255,255,255,0.2)", 12) for t in ["企财险","责任险","工程险","货运险"])}</div>
<div style="font-size:{px(13)}px;color:rgba(255,255,255,0.85);line-height:1.6">条款与费率差异大，治理须避免\u201c一刀切\u201d</div></div></div>''',
              sub=[(1, 0.5, "zoom"), (2, 1.4, "left"), (3, 3.2, "up")]))
    ts, ks = block(seg(5, 0), seg(5, 1), 4, ["up", "right", "pop", "fade"])
    b.append(B(ts[0], ks[0], f'''<div class="card" style="position:absolute;left:{px(450)}px;top:{px(112)}px;width:{px(766)}px;height:{px(150)}px;padding:{px(18)}px {px(20)}px;display:flex;flex-direction:row;gap:{px(14)}px;align-items:flex-start;z-index:3">
<div @@A0@@>{ico("triangle-exclamation", 20, GL, f"margin-top:{px(2)}px;flex:none")}</div>
<div @@A1@@ style="font-size:{px(16)}px;color:{DEEP};line-height:1.7;flex:1">制造企业新增设备、生产规模发生变化，意味着<b>实际风险也可能随之变化</b>——这正体现了非车险产品管理的复杂性。</div>
<div @@A2@@ style="position:absolute;right:{px(20)}px;bottom:{px(16)}px;font-size:{px(12)}px;font-weight:700;color:#1F9D5F;letter-spacing:{px(0.5)}px">01 / 复杂性</div></div>''',
              sub=[(1, ts[1] - ts[0], "up"), (2, ts[2] - ts[0], "pop")]))
    b.append(B(seg(5, 1), "up", f'''<div class="card" style="position:absolute;left:{px(450)}px;top:{px(274)}px;width:{px(766)}px;height:{px(150)}px;padding:{px(18)}px {px(20)}px;display:flex;flex-direction:row;gap:{px(14)}px;align-items:flex-start;z-index:3">
<div @@A0@@>{ico("diagram-project", 20, GL, f"margin-top:{px(2)}px;flex:none")}</div>
<div @@A1@@ style="font-size:{px(16)}px;color:{DEEP};line-height:1.7;flex:1">非车险涵盖企财险、责任险、工程险、货运险等众多险种，不同业务场景下条款和费率差异较大，因此产品治理需要<b>从源头入手</b>。</div>
<div @@A2@@ style="position:absolute;right:{px(20)}px;bottom:{px(16)}px;font-size:{px(12)}px;font-weight:700;color:#1F9D5F;letter-spacing:{px(0.5)}px">02 / 源头治理</div></div>''',
              sub=[(1, 1.3, "up"), (2, 3.0, "pop")]))
    b.append(B(seg(5, 2), "up", f'''<div style="position:absolute;left:{px(450)}px;top:{px(436)}px;width:{px(766)}px;height:{px(204)}px;background:linear-gradient(135deg,#E8F7EF 0%,#F2FBF6 100%);border-radius:{px(14)}px;padding:{px(18)}px {px(20)}px;border:1px solid rgba(52,199,123,0.30);display:flex;flex-direction:column;z-index:3">
<div @@A0@@ style="display:flex;align-items:center;gap:{px(10)}px">{icobox("clipboard-check", 36, 18, GL, "#FFFFFF", 10)}
<div style="font-size:{px(20)}px;font-weight:700;color:{DEEP}">首要动作 · 健全产品监管政策体系</div></div></div>'''))
    subs = [("file-pen", "修订开发指引", "完善产品备案标准"), ("list-check", "分险种分阶段", "存量产品重新备案"), ("broom", "清虚提质", "加快产品结构优化")]
    ts, ks = block(seg(5, 2) + 1.8, end, 3, ["up", "left", "pop"])
    for i, (ic, t, d) in enumerate(subs):
        b.append(B(ts[i], ks[i], f'''<div style="position:absolute;left:{px(470 + i * 246)}px;top:{px(498)}px;width:{px(234)}px;height:{px(124)}px;background:#FFFFFF;border-radius:{px(10)}px;padding:{px(12)}px {px(14)}px;display:flex;flex-direction:column;gap:{px(6)}px;z-index:4">
<div @@A0@@>{ico(ic, 16, GL)}</div>
<div @@A1@@ style="font-size:{px(14)}px;font-weight:600;color:{DEEP}">{t}</div>
<div @@A2@@ style="font-size:{px(13)}px;color:{NEU};line-height:1.6">{d}</div></div>''',
              sub=[(1, 0.5, "up"), (2, 1.1, "fade")]))
    return b


def page_06():
    total = total_of(6)
    end = total - TAIL
    b = []
    b.append(B(0.9, "clip", f'''<div @@A0@@ style="position:absolute;left:{px(64)}px;top:{px(112)}px;width:{px(1152)}px;height:{px(252)}px;border-radius:{px(16)}px;overflow:hidden;background:{MIST};box-shadow:0 {px(6)}px {px(24)}px rgba(15,61,46,0.06);z-index:3">
<img src="../assets/product_mgmt.png" style="width:100%;height:100%;object-fit:cover;display:block"></div>''', dur=1.0))
    b.append(B(0.9, "fade", f'<div @@A0@@ style="position:absolute;left:{px(64)}px;top:{px(112)}px;width:{px(400)}px;height:{px(252)}px;border-radius:{px(16)}px 0 0 {px(16)}px;background:linear-gradient(90deg,rgba(15,61,46,0.85) 0%,rgba(15,61,46,0.55) 70%,rgba(15,61,46,0) 100%);z-index:4"></div>', dur=1.2))
    b.append(B(seg(6, 0), "left", f'''<div @@A0@@ style="position:absolute;left:{px(90)}px;top:{px(150)}px;width:{px(340)}px;z-index:5">
<div @@A1@@>{ico("user-tie", 22, GL)}</div>
<div @@A2@@ style="font-size:{px(21)}px;font-weight:700;color:#FFFFFF;line-height:1.4;margin-top:{px(12)}px">责任要落到人<br>基础支撑要靠行业</div></div>''',
              sub=[(1, 0.5, "zoom"), (2, 1.2, "up")]))
    b.append(B(seg(6, 1), "up", f'<div @@A0@@ style="position:absolute;left:{px(90)}px;top:{px(288)}px;width:{px(340)}px;font-size:{px(14)}px;color:rgba(255,255,255,0.88);line-height:1.6;z-index:5">{sub("产品管理委员会 + 三家协会分工协作", 14, "rgba(255,255,255,0.88)", lh=1.6)}</div>'))
    ts, ks = block(seg(6, 1), seg(6, 2), 4, ["up", "left", "pop", "fade"])
    b.append(B(ts[0], ks[0], f'''<div class="card" style="position:absolute;left:{px(64)}px;top:{px(378)}px;width:{px(626)}px;height:{px(262)}px;padding:{px(18)}px {px(20)}px;display:flex;flex-direction:column;z-index:3">
<div @@A0@@ style="display:flex;align-items:center;gap:{px(10)}px">{icobox("user-shield", 34, 17, GL, "#FFFFFF", 10)}
<div style="font-size:{px(19)}px;font-weight:700;color:{DEEP}">压实主体责任</div></div>
<div @@A1@@ style="font-size:{px(15)}px;color:{NEU};line-height:1.75;margin-top:{px(12)}px">明确由财产保险公司<b style="color:{DEEP}">主要负责人牵头产品管理委员会</b>，健全内部审核机制，强化追责处罚，进一步落实产品管理责任——把产品管理的最终责任压到经营层一把手。</div>
<div @@A2@@ style="margin-top:auto;padding-top:{px(10)}px;display:flex;gap:{px(8)}px">{tag("内部审核", "#1F9D5F", MIST, 12)}{tag("追责处罚", "#1F9D5F", MIST, 12)}</div></div>''',
              sub=[(1, ts[1] - ts[0], "up"), (2, ts[2] - ts[0], "pop")]))
    ts, ks = block(seg(6, 2), end, 4, ["right", "up", "left", "pop"])
    b.append(B(ts[0], ks[0], f'''<div class="card-soft" style="position:absolute;left:{px(704)}px;top:{px(378)}px;width:{px(512)}px;height:{px(262)}px;padding:{px(18)}px {px(20)}px;display:flex;flex-direction:column;z-index:3">
<div @@A0@@ style="display:flex;align-items:center;gap:{px(10)}px">{icobox("handshake", 34, 17, "#1F9D5F", "#FFFFFF", 10)}
<div style="font-size:{px(19)}px;font-weight:700;color:{DEEP}">完善行业支撑</div></div>
<div @@A3@@ style="margin-top:auto;padding-top:{px(10)}px;font-size:{px(13)}px;color:#1F9D5F;font-weight:600;line-height:1.5">三家协会各管一段，共同提升规范化水平</div></div>''',
              sub=[(3, ts[3] - ts[0], "up")]))
    three = [("file-lines", "保险业协会", "标准化条款建设"), ("calculator", "精算师协会", "基准风险测算"), ("microchip", "银保信公司", "智能检核系统优化")]
    for i, (ic, nm, d) in enumerate(three):
        b.append(B(ts[1 + min(i, 2)] + 0.15 * i, ["left", "right", "pop"][i], f'''<div @@A0@@ style="position:absolute;left:{px(724)}px;top:{px(452 + i * 44)}px;width:{px(472)}px;height:{px(36)}px;display:flex;align-items:center;gap:{px(10)}px;background:#FFFFFF;border-radius:{px(9)}px;padding:0 {px(12)}px;z-index:4">
<div @@A1@@>{ico(ic, 15, GL, "flex:none")}</div>
<div @@A2@@ style="font-size:{px(14)}px;color:{DEEP};flex:1"><b>{nm}</b> · {d}</div></div>''',
                  sub=[(1, 0.2, "zoom"), (2, 0.6, "fade")]))
    return b


def page_07():
    total = total_of(7)
    end = total - TAIL
    b = []
    b.append(B(0.9, "clip", f'''<div @@A0@@ style="position:absolute;left:{px(64)}px;top:{px(112)}px;width:{px(658)}px;height:{px(528)}px;border-radius:{px(16)}px;overflow:hidden;background:{MIST};box-shadow:0 {px(6)}px {px(24)}px rgba(15,61,46,0.06);z-index:3">
<img src="../assets/business_control.png" style="width:100%;height:100%;object-fit:cover;display:block"></div>''', dur=1.0))
    b.append(B(0.9, "fade", f'<div @@A0@@ style="position:absolute;left:{px(64)}px;top:{px(112)}px;width:{px(658)}px;height:{px(528)}px;border-radius:{px(16)}px;background:linear-gradient(180deg,rgba(15,61,46,0) 48%,rgba(15,61,46,0.86) 100%);z-index:4"></div>', dur=1.2))
    mid = max(seg(7, 2), 14.0)
    ts, ks = block(4.0, mid, 4, ["up", "left", "pop", "fade"])
    b.append(B(ts[0], ks[0], f'<div @@A0@@ style="position:absolute;left:{px(90)}px;top:{px(468)}px;width:{px(606)}px;font-size:{px(20)}px;font-weight:700;color:#FFFFFF;line-height:1.4;z-index:5">{sub("费率纪律 + 分类施策", 20, "#FFF", 700, 1.4)}<br>{sub("才是稳健经营的实质", 20, "#FFF", 700, 1.4)}</div>'))
    for i, (txt, c) in enumerate([("续保中的价格协商本是正常市场行为，", "rgba(255,255,255,0.86)"),
                                  ("但为争夺业务不计成本降费率就偏离了稳健经营要求", "rgba(255,255,255,0.86)")]):
        b.append(B(ts[1 + i], ks[1 + i], f'<div @@A0@@ style="position:absolute;left:{px(90)}px;top:{px(562 + i * 26)}px;width:{px(606)}px;font-size:{px(13)}px;color:{c};z-index:5">{sub(txt, 13, c, lh=1.6)}</div>'))
    ts, ks = block(1.6, mid, 4, ["right", "up", "pop", "fade"])
    b.append(B(ts[0], ks[0], f'''<div class="card" style="position:absolute;left:{px(740)}px;top:{px(112)}px;width:{px(476)}px;height:{px(150)}px;padding:{px(16)}px {px(18)}px;display:flex;flex-direction:row;gap:{px(12)}px;align-items:flex-start;z-index:3">
<div @@A0@@>{ico("file-contract", 18, GL, f"margin-top:{px(2)}px;flex:none")}</div>
<div @@A1@@ style="font-size:{px(15)}px;color:{DEEP};line-height:1.7;flex:1">严格执行<b>备案条款费率</b>，把费率纪律作为业务经营的第一条底线。</div></div>''',
              sub=[(1, ts[1] - ts[0], "up")]))
    b.append(B(ts[2], ks[2], f'''<div @@A0@@ style="position:absolute;left:{px(740)}px;top:{px(276)}px;display:flex;align-items:center;gap:{px(8)}px;z-index:3">
<div style="width:{px(4)}px;height:{px(16)}px;border-radius:{px(2)}px;background:{GL}"></div>
<div style="font-size:{px(16)}px;font-weight:700;color:{DEEP}">差异化管理 · 三档施策</div></div>'''))
    tiers = [("ban", "严控 · 高风险业务", "收缩敞口、强化核保约束", seg(7, 2), "hl"),
             ("arrow-trend-up", "优化 · 长期严重亏损业务", "调整定价与结构、止损转正", seg(7, 2) + 2.2, "soft"),
             ("eye", "关注 · 高增速业务", "防止规模扩张掩盖风险积累", total * 0.72, "plain")]
    for i, (ic, t, d, t0, style) in enumerate(tiers):
        if style == "hl":
            cls, ibg, ifg, tc, dc = "card-hl", "rgba(255,255,255,0.22)", "#FFFFFF", "#FFFFFF", "rgba(255,255,255,0.88)"
        elif style == "soft":
            cls, ibg, ifg, tc, dc = "card-soft", "#1F9D5F", "#FFFFFF", DEEP, NEU
        else:
            cls, ibg, ifg, tc, dc = "card", MIST, GL, DEEP, NEU
        ts2, ks2 = block(t0, min(end, t0 + 5.6), 3, ["right", "up", "pop"])
        b.append(B(ts2[0], ks2[0], f'''<div class="{cls}" style="position:absolute;left:{px(740)}px;top:{px(320 + i * 110)}px;width:{px(476)}px;height:{px(98)}px;padding:{px(14)}px {px(16)}px;display:flex;flex-direction:row;align-items:center;gap:{px(12)}px;z-index:4">
<div @@A0@@>{icobox(ic, 38, 18, ibg, ifg, 10)}</div>
<div @@A1@@ style="flex:1"><div style="font-size:{px(15)}px;font-weight:700;color:{tc}">{t}</div>
<div @@A2@@ style="font-size:{px(12.5)}px;color:{dc};line-height:1.5;margin-top:{px(2)}px">{d}</div></div></div>''',
              sub=[(1, ts2[1] - ts2[0], "up"), (2, ts2[2] - ts2[0], "fade")]))
    return b


def page_08():
    total = total_of(8)
    end = total - TAIL
    b = []
    b.append(B(0.9, "left", f'''<div class="card" style="position:absolute;left:{px(64)}px;top:{px(112)}px;width:{px(430)}px;height:{px(258)}px;padding:{px(18)}px;display:flex;flex-direction:column;z-index:3">
<div @@A0@@ style="display:flex;align-items:center;gap:{px(10)}px">{icobox("arrow-up-right-dots", 36, 18, GL, "#FFFFFF", 10)}
<div style="font-size:{px(19)}px;font-weight:700;color:{DEEP}">提质升级</div></div>
<div @@A1@@ style="font-size:{px(15)}px;color:{NEU};line-height:1.75;margin-top:{px(10)}px">推动保险机构发挥比较优势、实现<b style="color:{DEEP}">错位发展</b>，避免在同质化赛道上打价格战。</div>
<div @@A2@@ style="font-size:{px(14)}px;color:{NEU};line-height:1.7;margin-top:{px(8)}px">加强与国家战略对接，在六大新兴领域拓展业务空间——</div></div>''',
              sub=[(1, 0.8, "up"), (2, 1.8, "up")]))
    tags6 = ["绿色", "智能制造", "低空经济", "海洋经济", "新市民", "地方特色产业"]
    ts, ks = block(seg(8, 1), seg(8, 2), 6, ["pop"] * 6)
    for i, t in enumerate(tags6):
        b.append(B(ts[i], "pop", f'''<div @@A0@@ style="position:absolute;left:{px(84 + (i % 3) * 138)}px;top:{px(320 + (i // 3) * 44)}px;z-index:4">{tag(t, "#1F9D5F", MIST, 12)}</div>'''))
    b.append(B(seg(8, 2), "left", f'''<div class="card-soft" style="position:absolute;left:{px(64)}px;top:{px(382)}px;width:{px(430)}px;height:{px(258)}px;padding:{px(18)}px;display:flex;flex-direction:column;z-index:3">
<div @@A0@@ style="display:flex;align-items:center;gap:{px(10)}px">{icobox("scale-balanced", 36, 18, "#1F9D5F", "#FFFFFF", 10)}
<div style="font-size:{px(19)}px;font-weight:700;color:{DEEP}">监管与自律</div></div>
<div @@A1@@ style="font-size:{px(15)}px;color:{NEU};line-height:1.75;margin-top:{px(10)}px">统一<b style="color:{DEEP}">跨区域监管尺度</b>，避免同类业务在不同地区适用不同标准。</div>
<div @@A2@@ style="margin-top:auto;padding-top:{px(10)}px">
<div style="background:#FFFFFF;border-radius:{px(10)}px;padding:{px(10)}px {px(12)}px;display:flex;align-items:center;gap:{px(8)}px">
{ico("link", 14, GL, "flex:none")}<div style="font-size:{px(13.5)}px;color:{DEEP};font-weight:600;flex:1">\u201c检查、通报、挂钩\u201d工作机制</div></div></div></div>''',
              sub=[(1, 1.2, "up"), (2, 2.6, "pop")]))
    b.append(B(seg(8, 3), "up", f'<div @@A0@@ style="position:absolute;left:{px(84)}px;top:{px(588)}px;width:{px(400)}px;font-size:{px(13)}px;color:{NEU};line-height:1.6;z-index:4">{sub("加强行业自律与典型违规案例通报", 13, NEU, lh=1.6)}</div>'))
    b.append(B(0.9, "clip", f'''<div @@A0@@ style="position:absolute;left:{px(512)}px;top:{px(112)}px;width:{px(704)}px;height:{px(528)}px;border-radius:{px(16)}px;overflow:hidden;background:{MIST};box-shadow:0 {px(6)}px {px(24)}px rgba(15,61,46,0.06);z-index:3">
<img src="../assets/growth_field.png" style="width:100%;height:100%;object-fit:cover;display:block"></div>''', dur=1.0))
    ts, ks = block(seg(8, 0), seg(8, 2), 2, ["down", "up"])
    b.append(B(ts[0], ks[0], f'<div @@A0@@ style="position:absolute;left:{px(538)}px;top:{px(136)}px;width:{px(652)}px;font-size:{px(20)}px;font-weight:700;color:#FFFFFF;line-height:1.4;z-index:4;text-shadow:0 2px 14px rgba(15,61,46,0.55)">{sub("在国家战略的坐标系里", 20, "#FFF", 700, 1.4)}<br>{sub("找非车险的新增长空间", 20, "#FFF", 700, 1.4)}</div>'))
    b.append(B(ts[1], ks[1], f'<div @@A0@@ style="position:absolute;left:{px(538)}px;top:{px(580)}px;display:flex;align-items:center;gap:{px(8)}px;padding:{px(7)}px {px(14)}px;border-radius:9999px;background:rgba(255,255,255,0.92);z-index:4">{ico("compass", 15, "#1F9D5F")}<div style="font-size:{px(13)}px;font-weight:600;color:{DEEP}">错位发展 · 差异化竞争</div></div>'))
    return b


def page_09():
    total = total_of(9)
    end = total - TAIL
    b = []
    b.append(B(0.9, "left", f'''<div @@A0@@ style="position:absolute;left:{px(64)}px;top:{px(112)}px;width:{px(386)}px;height:{px(528)}px;border-radius:{px(16)}px;background:linear-gradient(135deg,#0F3D2E 0%,#14523C 100%);padding:{px(26)}px {px(24)}px;display:flex;flex-direction:column;overflow:hidden;z-index:3">
<div @@A1@@>{icobox("database", 52, 25, "rgba(52,199,123,0.22)", GL, 14)}</div>
<div @@A2@@ style="font-size:{px(22)}px;font-weight:700;color:#FFFFFF;line-height:1.4;margin-top:{px(18)}px">专业精细的管理<br>需要统一准确的数据</div>
<div @@A3@@ style="margin-top:{px(14)}px;background:rgba(52,199,123,0.14);border-radius:{px(12)}px;padding:{px(14)}px {px(16)}px;border-left:{px(3)}px solid {GL}">
<div style="font-size:{px(15)}px;font-weight:700;color:{GL};line-height:1.5">解决\u201c数出多门、口径不一\u201d</div>
<div style="font-size:{px(13)}px;color:rgba(255,255,255,0.82);line-height:1.6;margin-top:{px(6)}px">统一险种分类、费用分摊和统计指标</div></div>
<div @@A4@@ style="margin-top:auto;font-size:{px(13)}px;color:rgba(255,255,255,0.70);line-height:1.6">为经营指标监测和费率回溯<br>提供数据基础</div></div>''',
              sub=[(1, 0.5, "zoom"), (2, 1.4, "up"), (3, 2.6, "left"), (4, 4.0, "up")]))
    b.append(B(1.5, "clip", f'''<div @@A0@@ style="position:absolute;left:{px(470)}px;top:{px(112)}px;width:{px(746)}px;height:{px(158)}px;border-radius:{px(14)}px;overflow:hidden;background:{MIST};box-shadow:0 {px(6)}px {px(24)}px rgba(15,61,46,0.06);z-index:3">
<img src="../assets/data_platform.png" style="width:100%;height:100%;object-fit:cover;display:block"></div>''', dur=1.0))
    b.append(B(2.4, "right", f'<div @@A0@@ style="position:absolute;left:{px(700)}px;top:{px(112)}px;width:{px(516)}px;height:{px(158)}px;display:flex;align-items:center;justify-content:flex-end;background:linear-gradient(270deg,rgba(15,61,46,0.80) 0%,rgba(15,61,46,0.30) 60%,rgba(15,61,46,0) 100%);z-index:4;padding-right:{px(20)}px"><div style="font-size:{px(16)}px;font-weight:700;color:#FFFFFF;line-height:1.45;text-align:right">把标准固化到系统里<br>从\u201c多口径\u201d走向\u201c一套数\u201d</div></div>'))
    # 三层路径：每层铺满到下一层
    layers = [("ruler-combined", "统一行业数据标准", "STEP 1", "统一险种分类、费用分摊和统计指标；通过制定费用分摊指引，规范分摊程序与标准。", seg(9, 1), "plain", 282, seg(9, 2)),
              ("server", "加快系统建设", "STEP 2", "依托监管统信、银保信非车险平台、产品注册平台、保交所等基础设施，把标准固化到系统中。", seg(9, 2), "hl", 394, seg(9, 3)),
              ("chart-line", "强化数据积累和使用", "STEP 3", "归集全行业数据开展风险监测和费率回溯，发挥数据对监管、经营和风险管理的支撑作用。", seg(9, 3), "plain", 506, end)]
    for i, (ic, t, st, d, t0, style, top, w_end) in enumerate(layers):
        if style == "hl":
            cls = "card-hl"; ibg = "rgba(255,255,255,0.22)"; ifg = "#FFFFFF"; tc = "#FFFFFF"; dc = "rgba(255,255,255,0.92)"
            sbg = "rgba(255,255,255,0.24)"; sfg = "#FFFFFF"
        else:
            cls = "card"; ibg = MIST; ifg = GL; tc = DEEP; dc = NEU; sbg = MIST; sfg = "#1F9D5F"
        ts, ks = block(t0, w_end, 4, ["right", "zoom", "up", "grow"])
        b.append(B(ts[0], ks[0], f'''<div class="{cls}" style="position:absolute;left:{px(470)}px;top:{px(top)}px;width:{px(746)}px;height:{px(100)}px;padding:{px(16)}px {px(18)}px;display:flex;flex-direction:row;gap:{px(14)}px;align-items:center;z-index:3">
<div @@A0@@>{icobox(ic, 48, 22, ibg, ifg, 12)}</div>
<div @@A1@@ style="flex:1"><div style="display:flex;align-items:center;gap:{px(8)}px">
<div style="font-size:{px(18)}px;font-weight:700;color:{tc}">{t}</div>
<div style="padding:0 {px(8)}px;height:{px(19)}px;display:flex;align-items:center;border-radius:9999px;background:{sbg};font-size:{px(11)}px;font-weight:700;color:{sfg}">{st}</div></div>
<div @@A2@@ style="font-size:{px(14)}px;color:{dc};line-height:1.65;margin-top:{px(5)}px">{d}</div></div>
<div @@A3@@ style="position:absolute;left:{px(18)}px;bottom:{px(0)}px;height:{px(3)}px;border-radius:{px(2)}px;background:{"rgba(255,255,255,0.5)" if style == "hl" else "rgba(52,199,123,0.5)"};width:{px(220)}px"></div></div>''',
              sub=[(1, ts[1] - ts[0], "up"), (2, ts[2] - ts[0], "up"), (3, ts[3] - ts[0], "grow")]))
    return b


def page_10():
    total = total_of(10)
    end = total - TAIL
    b = []
    b.append(B(0.8, "left", f'<div @@A0@@ style="position:absolute;left:{px(66)}px;top:{px(112)}px;width:{px(1150)}px;display:flex;align-items:center;gap:{px(10)}px;z-index:3">{ico("circle-exclamation", 18, GL)}<span style="font-size:{px(16)}px;color:{NEU};line-height:1.5">价格之外，手续费是非车险市场竞争中最容易失范的环节</span></div>'))
    cards = [("handshake", "保险中介机构", "真实核算 · 明示透明", ["真实、准确核算各项收入支出", "严禁虚假核算和账外经营", "探索建立手续费保单明示制度"], "提高中介手续费透明度", seg(10, 2), False, seg(10, 3)),
             ("globe", "互联网平台", "整治流量优势滥用", ["规范利用\u201c流量优势\u201d收取不合理费用", "严肃查处强制捆绑或搭售行为", "严肃查处销售误导等违规行为"], "维护消费者合法权益", seg(10, 3), False, seg(10, 4)),
             ("building-shield", "财产保险公司", "强化中介管理责任", ["建立从准入到退出的全流程管理机制", "加强合作方资质核验", "堵塞变相套取、变相支付手续费通道"], "从合作源头规范中介业务", seg(10, 4), True, end)]
    for i, (ic, t, st, items, ft, t0, hl, w_end) in enumerate(cards):
        cls = "card-hl" if hl else "card"
        ibg = "rgba(255,255,255,0.22)" if hl else MIST
        ifg = "#FFFFFF" if hl else GL
        tc = "#FFFFFF" if hl else DEEP
        sc = "rgba(255,255,255,0.85)" if hl else "#1F9D5F"
        dc = "rgba(255,255,255,0.94)" if hl else NEU
        bd = "1px solid rgba(255,255,255,0.25)" if hl else "1px solid rgba(52,199,123,0.16)"
        ts, ks = block(t0, w_end, 6, ["left", "up", "pop", "left", "up", "pop"])
        b.append(B(ts[0], ks[0], f'''<div class="{cls}" style="position:absolute;left:{px(64 + i * 393)}px;top:{px(158)}px;width:{px(366)}px;height:{px(482)}px;padding:{px(20)}px {px(18)}px;display:flex;flex-direction:column;z-index:3">
<div @@A0@@>{icobox(ic, 48, 22, ibg, ifg, 12)}</div>
<div @@A1@@ style="font-size:{px(20)}px;font-weight:700;color:{tc};margin-top:{px(14)}px">{t}</div>
<div @@A2@@ style="font-size:{px(13)}px;color:{sc};font-weight:600;margin-top:{px(4)}px">{st}</div>
<div @@A3@@ style="margin-top:{px(12)}px;display:flex;flex-direction:column;gap:{px(8)}px"></div>
<div @@A4@@ style="margin-top:auto;padding-top:{px(12)}px;border-top:{bd}"><div style="font-size:{px(13)}px;font-weight:600;color:{sc};line-height:1.5">{ft}</div></div></div>''',
              sub=[(1, ts[1] - ts[0], "up"), (2, ts[2] - ts[0], "fade")]))
        ico_c = "#FFFFFF" if hl else GL
        for j, x in enumerate(items):
            b.append(B(ts[3 + j], ks[3 + j], f'''<div @@A0@@ style="position:absolute;left:{px(82 + i * 393)}px;top:{px(360 + j * 46)}px;width:{px(330)}px;display:flex;gap:{px(8)}px;align-items:flex-start;z-index:4">
<div @@A1@@>{ico("check", 12, ico_c, f"margin-top:{px(4)}px;flex:none")}</div>
<div @@A2@@ style="font-size:{px(14)}px;color:{dc};line-height:1.6;flex:1">{x}</div></div>''',
                  sub=[(1, 0.15, "zoom"), (2, 0.5, "fade")]))
        if w_end - ts[5] > 5.0:
            b.append(B((ts[5] + w_end) / 2, "grow", f'<div @@A0@@ style="position:absolute;left:{px(82 + i * 393)}px;top:{px(512)}px;width:{px(200)}px;height:{px(3)}px;border-radius:{px(2)}px;background:{"rgba(255,255,255,0.5)" if hl else "rgba(52,199,123,0.5)"};z-index:4"></div>'))
    return b


def page_11():
    total = total_of(11)
    end = total - TAIL
    b = []
    b.append(B(0.9, "left", f'''<div @@A0@@ style="position:absolute;left:{px(64)}px;top:{px(112)}px;width:{px(366)}px;height:{px(528)}px;border-radius:{px(16)}px;background:linear-gradient(135deg,#34C77B 0%,#1F9D5F 100%);padding:{px(26)}px {px(22)}px;display:flex;flex-direction:column;overflow:hidden;z-index:3">
<div @@A1@@>{icobox("shield-halved", 52, 25, "rgba(255,255,255,0.22)", "#FFFFFF", 14)}</div>
<div @@A2@@ style="font-size:{px(22)}px;font-weight:700;color:#FFFFFF;line-height:1.4;margin-top:{px(18)}px">治理要求要落地<br>需要责任机制兜底</div>
<div @@A3@@ style="margin-top:auto;background:rgba(255,255,255,0.18);border-radius:{px(12)}px;padding:{px(14)}px {px(16)}px">
<div style="font-size:{px(14)}px;color:#FFFFFF;font-weight:700;line-height:1.5">监管 — 主体 — 行业</div>
<div style="font-size:{px(13)}px;color:rgba(255,255,255,0.88);line-height:1.6;margin-top:{px(6)}px">三级各就各位，形成治理闭环</div></div></div>''',
              sub=[(1, 0.5, "zoom"), (2, 1.4, "left"), (3, 3.0, "up")]))
    lv = [("landmark", "LEVEL 1", "金融监管总局及其派出机构", '统筹落实治理要求，发挥<b style="color:#34C77B">\u201c四级垂管\u201d</b>优势，把治理要求一贯到底。', seg(11, 0), "dark", 13.0),
          ("building", "LEVEL 2", "保险公司和中介机构", '履行<b style="color:0F3D2E">主体责任</b>，把治理要求转化为内部制度与经营行为。', 16.2, "plain", 22.0),
          ("users-gear", "LEVEL 3", "行业协会与基础设施机构", '保险业协会、精算师协会、银保信公司、保交所发挥<b style="color:0F3D2E">协同治理作用</b>。', 22.0, "soft", end)]
    for i, (ic, lvl, t, d, t0, style, w_end) in enumerate(lv):
        if style == "dark":
            cls, ibg, ifg, tc, dc, lc = "card-dark", "rgba(52,199,123,0.24)", GL, "#FFFFFF", "rgba(255,255,255,0.85)", GL
        elif style == "soft":
            cls, ibg, ifg, tc, dc, lc = "card-soft", "#1F9D5F", "#FFFFFF", DEEP, NEU, "#1F9D5F"
        else:
            cls, ibg, ifg, tc, dc, lc = "card", MIST, GL, DEEP, NEU, "#1F9D5F"
        ts, ks = block(t0, w_end, 4, ["left", "zoom", "up", "pop"])
        chips = ""
        if style == "soft":
            chips = f'''<div @@A3@@ style="display:flex;gap:{px(6)}px;margin-top:{px(7)}px">{"".join(tag(x, "#1F9D5F", "#FFFFFF", 11) for x in ["保险业协会", "精算师协会", "银保信公司", "保交所"])}</div>'''
        b.append(B(ts[0], ks[0], f'''<div class="{cls}" style="position:absolute;left:{px(450)}px;top:{px(112 + i * 180)}px;width:{px(766)}px;height:{px(168)}px;padding:{px(16)}px {px(20)}px;display:flex;flex-direction:row;gap:{px(16)}px;align-items:center;z-index:3">
<div @@A0@@ style="display:flex;flex-direction:column;align-items:center;gap:{px(6)}px;width:{px(54)}px;flex:none">
{icobox(ic, 42, 20, ibg, ifg, 12)}
<div style="font-size:{px(11)}px;font-weight:700;color:{lc};font-family:'Space Grotesk',sans-serif">{lvl}</div></div>
<div style="flex:1"><div @@A1@@ style="font-size:{px(18)}px;font-weight:700;color:{tc}">{t}</div>
<div @@A2@@ style="font-size:{px(14)}px;color:{dc};line-height:1.6;margin-top:{px(5)}px">{d}</div>{chips}</div></div>''',
              sub=[(1, ts[1] - ts[0], "up"), (2, ts[2] - ts[0], "up"), (3, ts[3] - ts[0], "pop")]))
    return b


def page_12():
    total = total_of(12)
    end = total - TAIL
    b = []
    b.append(B(0.9, "clip", f'''<div @@A0@@ style="position:absolute;left:{px(64)}px;top:{px(112)}px;width:{px(1152)}px;height:{px(250)}px;border-radius:{px(16)}px;overflow:hidden;background:{MIST};box-shadow:0 {px(6)}px {px(24)}px rgba(15,61,46,0.06);z-index:3">
<img src="../assets/env_assess.png" style="width:100%;height:100%;object-fit:cover;display:block"></div>''', dur=1.0))
    b.append(B(0.9, "fade", f'<div @@A0@@ style="position:absolute;left:{px(786)}px;top:{px(112)}px;width:{px(430)}px;height:{px(250)}px;border-radius:{px(16)}px;background:linear-gradient(270deg,rgba(15,61,46,0.85) 0%,rgba(15,61,46,0.50) 70%,rgba(15,61,46,0) 100%);z-index:4"></div>', dur=1.2))
    ts, ks = block(seg(12, 0), seg(12, 2), 3, ["right", "right", "fade"])
    b.append(B(ts[0], ks[0], f'<div @@A0@@ style="position:absolute;left:{px(816)}px;top:{px(142)}px;width:{px(376)}px;z-index:5"><div @@A1@@>{ico("arrows-rotate", 22, GL)}</div><div @@A2@@ style="font-size:{px(21)}px;font-weight:700;color:#FFFFFF;line-height:1.4;margin-top:{px(12)}px;text-align:right">治理不是发完文件就结束<br>而是滚动迭代的过程</div></div>''',
              sub=[(1, 0.3, "zoom"), (2, 1.0, "up")]))
    ts, ks = block(seg(12, 0), seg(12, 2), 5, ["up", "left", "left", "left", "grow"])
    b.append(B(ts[0], ks[0], f'''<div class="card" style="position:absolute;left:{px(64)}px;top:{px(376)}px;width:{px(569)}px;height:{px(264)}px;padding:{px(18)}px {px(20)}px;display:flex;flex-direction:column;z-index:3">
<div @@A0@@ style="display:flex;align-items:center;gap:{px(10)}px">{icobox("seedling", 34, 17, GL, "#FFFFFF", 10)}
<div style="font-size:{px(19)}px;font-weight:700;color:{DEEP}">优化发展环境</div></div></div>'''))
    env_items = ["持续完善非车险监管制度，加强与政府职能部门协同", "建立重点领域专项协作机制", "指导行业健全反欺诈工作体系"]
    for i, x in enumerate(env_items):
        b.append(B(ts[1 + i], ks[1 + i], f'<div @@A0@@ style="position:absolute;left:{px(84)}px;top:{px(448 + i * 50)}px;width:{px(530)}px;z-index:4">{check(x, NEU, 14.5, GL)}</div>'))
    ts, ks = block(seg(12, 2), end, 5, ["up", "right", "right", "right", "pop"])
    b.append(B(ts[0], ks[0], f'''<div class="card-hl" style="position:absolute;left:{px(647)}px;top:{px(376)}px;width:{px(569)}px;height:{px(264)}px;padding:{px(18)}px {px(20)}px;display:flex;flex-direction:column;z-index:3">
<div @@A0@@ style="display:flex;align-items:center;gap:{px(10)}px">{icobox("clipboard-list", 34, 17, "rgba(255,255,255,0.22)", "#FFFFFF", 10)}
<div style="font-size:{px(19)}px;font-weight:700;color:#FFFFFF">加强动态评估</div></div>
<div @@A1@@ style="margin-top:auto;padding-top:{px(12)}px;border-top:1px solid rgba(255,255,255,0.25)">
<div style="font-size:{px(13)}px;font-weight:600;color:#FFFFFF;line-height:1.5">推动非车险综合治理持续深化</div></div></div>''',
              sub=[(1, ts[4] - ts[0], "up")]))
    ev_items = ["建立定期评估机制，持续跟踪综合治理进展", "根据评估结果与市场变化及时调整治理举措"]
    for i, x in enumerate(ev_items):
        b.append(B(ts[1 + i], ks[1 + i], f'<div @@A0@@ style="position:absolute;left:{px(667)}px;top:{px(448 + i * 50)}px;width:{px(530)}px;z-index:4">{check(x, "rgba(255,255,255,0.95)", 14.5, "#FFFFFF")}</div>'))
    return b


def page_13():
    total = total_of(13)
    end = total - TAIL
    b = []
    b.append(B(0.9, "left", f'''<div @@A0@@ style="position:absolute;left:{px(64)}px;top:{px(112)}px;width:{px(645)}px;height:{px(528)}px;border-radius:{px(16)}px;background:linear-gradient(135deg,#0F3D2E 0%,#14523C 100%);padding:{px(26)}px {px(30)}px;display:flex;flex-direction:column;overflow:hidden;z-index:3">
<div @@A1@@ style="display:flex;align-items:center;gap:{px(8)}px">
<div style="width:{px(18)}px;height:{px(2)}px;background:{GL}"></div>
<div style="font-size:{px(13)}px;font-weight:600;color:{GL};letter-spacing:{px(1.5)}px">GOVERNANCE FRAMEWORK</div></div>
<div @@A2@@ style="display:flex;align-items:baseline;gap:{px(14)}px;margin-top:{px(8)}px">
<div style="font-size:{px(88)}px;font-weight:700;color:#FFFFFF;line-height:1.42;letter-spacing:{px(-2)}px;font-family:'Space Grotesk',sans-serif">4</div>
<div style="font-size:{px(30)}px;font-weight:700;color:{GL};line-height:1.35">+</div>
<div style="font-size:{px(88)}px;font-weight:700;color:#FFFFFF;line-height:1.42;letter-spacing:{px(-2)}px;font-family:'Space Grotesk',sans-serif">5</div></div>
<div @@A3@@ style="font-size:{px(15)}px;color:rgba(255,255,255,0.75);line-height:1.55;margin-top:{px(6)}px">四项基本原则为纲 · 五个方面系统推进</div></div>''',
              sub=[(1, 0.7, "left"), (2, 1.6, "zoom"), (3, 2.6, "up")]))
    # 四个原则：按第 1 句旁白窗口均匀展开（而非固定步进），与语音念读节奏一致
    s0 = seg(13, 0)
    w0 = TL["pages"]["13"]["segs"][0]["dur"]
    tps = spread(s0 + 0.5, s0 + w0 - 0.3, 4)
    for i, x in enumerate(["问题导向", "分类施策", "先立后破", "稳步推进"]):
        ts = tps[i]
        b.append(B(ts, "zoom", f'<div @@A0@@ style="position:absolute;left:{px(98 + (i % 2) * 132)}px;top:{px(400 + (i // 2) * 46)}px;padding:{px(5)}px {px(12)}px;border-radius:9999px;background:rgba(52,199,123,0.18);border:1px solid rgba(52,199,123,0.45);font-size:{px(13)}px;font-weight:600;color:#FFFFFF;z-index:4">{x}</div>'))
    # 五个方面：按第 2 句旁白窗口均匀展开
    s1 = seg(13, 1)
    w1 = TL["pages"]["13"]["segs"][1]["dur"]
    aps = spread(s1 + 0.5, s1 + w1 - 0.3, 5)
    for i, x in enumerate(["产品源头管理", "业务稳健经营", "系统数据支撑", "中介业务规范", "治理保障措施"]):
        ts = aps[i]
        b.append(B(ts, "up", f'<div @@A0@@ style="position:absolute;left:{px(98 + (i % 3) * 154)}px;top:{px(508 + (i // 3) * 44)}px;padding:{px(4)}px {px(11)}px;border-radius:{px(8)}px;background:rgba(255,255,255,0.12);font-size:{px(13)}px;color:rgba(255,255,255,0.92);white-space:nowrap;z-index:4">{x}</div>'))
    b.append(B(1.4, "clip", f'''<div @@A0@@ style="position:absolute;left:{px(727)}px;top:{px(112)}px;width:{px(489)}px;height:{px(360)}px;border-radius:{px(16)}px;overflow:hidden;background:{MIST};box-shadow:0 {px(6)}px {px(24)}px rgba(15,61,46,0.06);z-index:3">
<img src="../assets/panorama.png" style="width:100%;height:100%;object-fit:cover;display:block"></div>''', dur=1.0))
    ts, ks = block(seg(13, 2), end, 3, ["up", "pop", "fade"])
    b.append(B(ts[0], ks[0], f'''<div @@A0@@ style="position:absolute;left:{px(727)}px;top:{px(486)}px;width:{px(489)}px;height:{px(154)}px;background:{MIST};border-radius:{px(14)}px;padding:{px(16)}px {px(18)}px;display:flex;flex-direction:column;gap:{px(8)}px;border-left:{px(4)}px solid {GL};z-index:3">
<div @@A1@@ style="display:flex;align-items:center;gap:{px(8)}px">{ico("arrow-right-long", 16, "#1F9D5F")}
<div style="font-size:{px(15)}px;font-weight:700;color:{DEEP};flex:1">由单项规范向系统治理深化</div></div>
<div @@A2@@ style="font-size:{px(13)}px;color:{NEU};line-height:1.65">持续改善市场秩序，构建规范化、专业化、精细化的非车险市场体系。</div></div>''',
              sub=[(1, ts[1] - ts[0], "right"), (2, ts[2] - ts[0], "up")]))
    return b


PAGE_DEF = {1: page_01, 2: page_02, 3: page_03, 4: page_04, 5: page_05, 6: page_06,
            7: page_07, 8: page_08, 9: page_09, 10: page_10, 11: page_11, 12: page_12,
            13: page_13}

HDRS = {
    1: ("无序竞争与经营质量失衡", "背景 · 现状", False),
    2: ("治理持续深化：由单项规范到系统治理", "背景 · 演进", False),
    3: ("总体要求 · 四项基本原则", "一 · 总体要求", False),
    4: ("\u201c十五五\u201d治理目标", "一 · 总体要求", False),
    5: ("强化产品源头管理", "治理方向 一", True),
    6: ("压实主体责任 · 完善行业支撑", "治理方向 一", True),
    7: ("推动业务稳健经营", "治理方向 二", True),
    8: ("提质升级 · 监管与自律", "治理方向 二", True),
    9: ("夯实系统数据支撑", "治理方向 三", True),
    10: ("规范中介业务行为", "治理方向 四", True),
    11: ("加强治理保障措施", "治理方向 五", True),
    12: ("优化发展环境 · 加强动态评估", "治理方向 五", True),
    13: ("小结 · 非车险综合治理全景", "小结", True),
}
GLOWS = {
    1: (-140, "right", -140, 460, 0.13), 2: (-150, "right", -120, 440, 0.12),
    3: (-150, "right", -120, 440, 0.12), 4: (-160, "right", -100, 480, 0.14),
    5: (-140, "right", -130, 440, 0.11), 6: (-150, "left", -140, 460, 0.11),
    7: (-150, "right", -120, 460, 0.12), 8: (540, "left", -130, 440, 0.11),
    9: (-160, "right", -120, 470, 0.12), 10: (-150, "left", -130, 450, 0.11),
    11: (-150, "right", -120, 450, 0.11), 12: (-150, "left", -130, 460, 0.12),
    13: (-160, "right", -100, 480, 0.14),
}


def main():
    global _CURPAGE
    LEDGER.clear()
    for n in range(1, NPC + 1):
        _CURPAGE = n
        beats = PAGE_DEF[n]()
        html = ('<!DOCTYPE html>\n<html><head><meta charset="utf-8">\n'
                '<link rel="stylesheet" href="../fa/css/all.min.css">\n'
                '<link rel="stylesheet" href="../common.css">\n'
                '</head><body>\n' + finalize(n, beats) + '\n'
                '<script src="../anim.js"></script>\n'
                '<script>window.seek(0);</script>\n</body></html>')
        with open(os.path.join(PAGES_DIR, "p%02d.html" % n), "w", encoding="utf-8") as f:
            f.write(html)
        print("p%02d.html  beats=%2d  %6d bytes" % (n, len(beats), len(html)))

    # ---- 源级同步自检：每个 block() 节拍都必须落在其锚点句的语音区间内 ----
    over = [r for r in LEDGER if r["t"] > r["sent_end"] + 0.001]
    print("\n[sync] checked %d beats across %d pages; %d over sentence end"
          % (len(LEDGER), NPC, len(over)))
    if over:
        for r in over[:10]:
            print("  ! p%d beat t=%.3f > 句尾 %.3f" % (r["page"], r["t"], r["sent_end"]))
    return 0 if not over else 1


if __name__ == "__main__":
    main()