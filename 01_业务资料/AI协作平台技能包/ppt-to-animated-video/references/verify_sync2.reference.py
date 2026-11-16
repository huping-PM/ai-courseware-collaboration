# -*- coding: utf-8 -*-
"""verify_sync2.py — 双向校验「画面元素出场时刻」与配音的对齐情况。

对每个带 data-anim 的元素取**首次可见**时刻 fv，定位其所属旁白句，计算
  signed = fv - 句.start
  late   = fv - (句.start + 句.dur)     # >0 表示本句读完很久才出现

判据（双向）：
- 早于语音超过 EARLY_OK 秒            → 提前（画面先动、语音后到）
- 晚于本句语音结束超过 LATE_OK 秒     → 滞后（配音读完画面才出现）★本次修复目标

另外单独统计「跨句滞后」：元素所属句已结束、且下一句也已开始后许久才出现。
"""
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
PAGES = os.path.join(BASE, "html", "pages")
EARLY_OK = 1.2    # 允许提前的最大秒数（入场动画需要一点提前量）
LATE_OK = 0.60    # 允许晚于本句语音结束的最大秒数

with open(os.path.join(BASE, "timeline.json"), encoding="utf-8") as f:
    TL = json.load(f)
NPC = len(TL["pages"])


def anim_start(ks):
    """元素**开始出现**的时刻 = 第一个关键帧的时间。

    注意：不能取"第一个 op>0 的关键帧"——`pop`/`up` 这类动画的首帧 op=0，
    到次帧才 op=1，用后者会把出场时刻误判为动画结束时刻（晚约 0.8s）。
    """
    return ks[0]["t"]


def anim_end(ks):
    return ks[-1]["t"]


def owner(fv, segs):
    """返回包含 fv 的句子；若落在停顿中，取前一句。"""
    for s in segs:
        if s["start"] <= fv <= s["start"] + s["dur"]:
            return s
    prev = [s for s in segs if s["start"] + s["dur"] <= fv]
    return prev[-1] if prev else segs[0]


def main():
    print("%-5s %6s %9s %9s %9s %6s %9s  %s"
          % ("page", "elems", "maxEarly", "avgSigned", "maxLate", "lateN", "endOver", "verdict"))
    bad = 0
    for n in range(1, NPC + 1):
        path = os.path.join(PAGES, "p%02d.html" % n)
        if not os.path.exists(path):
            continue
        html = open(path, encoding="utf-8").read()
        segs = TL["pages"][str(n)]["segs"]
        page_end = TL["pages"][str(n)]["total"] + 0.30   # 页面视频时长
        signed, late, endover = [], [], []
        for mo in re.finditer(r"data-anim='([^']*)'", html):
            try:
                ks = json.loads(mo.group(1))
            except Exception:
                continue
            if not ks:
                continue
            fv = anim_start(ks)
            if fv <= 0.5:
                continue                        # 页首常驻元素（底色/页头）不参与
            s = owner(fv, segs)
            signed.append(fv - s["start"])
            late.append(fv - (s["start"] + s["dur"]))
            endover.append(anim_end(ks) - page_end)

        if not signed:
            continue
        max_early = -min(min(signed), 0.0)
        max_late = max(late)
        n_late = sum(1 for x in late if x > LATE_OK)
        max_endover = max(endover)
        ok = (max_early <= EARLY_OK) and (max_late <= LATE_OK) and (max_endover <= 0.0)
        if not ok:
            bad += 1
        print("%-5d %6d %8.2fs %9.2fs %8.2fs %5d %8.2fs  %s"
              % (n, len(signed), max_early, sum(signed) / len(signed),
                 max_late, n_late, max_endover, "OK" if ok else "FAIL"))
        if max_late > LATE_OK:
            print("      滞后 %.2fs：本句读完才出现（应 <= %.2fs）" % (max_late, LATE_OK))
        if max_early > EARLY_OK:
            print("      提前 %.2fs（应 <= %.2fs）" % (max_early, EARLY_OK))
        if max_endover > 0:
            print("      动画晚于页长 %.2fs，会被截断" % max_endover)

    print("\nRESULT:", "ALL SYNCED（无提前、无滞后、无超出页长）" if bad == 0
          else "%d page(s) 存在音画不同步" % bad)
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())