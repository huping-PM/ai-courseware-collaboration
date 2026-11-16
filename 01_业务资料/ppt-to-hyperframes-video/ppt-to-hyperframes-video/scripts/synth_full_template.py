# -*- coding: utf-8 -*-
"""逐句配音合成模板（edge-tts 晓晓 -5%）。

复制本文件到项目根，替换 SCENES 为你的逐句稿，运行即生成：
  - audio_full/sNN_sMM.mp3   逐句音频
  - audio_full/concat.txt     拼接清单
  - timeline-full.json        每句时长 + 每场 total（时间轴唯一真相）

依赖：pip install edge-tts（装进隔离 venv）
ffprobe：优先用 .fftools/ffprobe.exe（见 setup.md），否则改 FFPROBE 路径。
"""
import asyncio, json, os, subprocess

VOICE = "zh-CN-XiaoxiaoNeural"
RATE  = "-5%"
BASE  = os.path.dirname(os.path.abspath(__file__))
OUT   = os.path.join(BASE, "audio_full")
os.makedirs(OUT, exist_ok=True)

# 优先项目本地 .fftools/ffprobe.exe；否则指向系统/工具 ffprobe
FFPROBE = os.path.join(BASE, ".fftools", "ffprobe.exe")
if not os.path.exists(FFPROBE):
    FFPROBE = "ffprobe"   # 假设在 PATH

# 12 场口播原文（逐句短句，第 1 句是小标题句）—— 按你的稿子改这里
SCENES = {
 1: [
  "近年来，随着非车险业务快速发展，一些长期积累的经营问题也逐渐显现。",
  "部分机构为争夺业务，不计成本降低费率、放宽条款，或依靠高额手续费吸引客户，",
  "导致无序竞争、费用率虚高、应收保费较高等问题，",
  "业务规模增长与经营质量提升不同步。",
 ],
 # …第 2~N 场照此结构补全…
}

import edge_tts

def dur_of(path):
    out = subprocess.run([FFPROBE, "-v", "error", "-show_entries",
                          "format=duration", "-of", "csv=p=0", path],
                         capture_output=True, text=True)
    try:
        return float(out.stdout.strip())
    except Exception:
        return None

async def synth(text, path):
    c = edge_tts.Communicate(text, VOICE, rate=RATE)
    await c.save(path)

async def main():
    timeline = {"scenes": {}, "voice": VOICE, "rate": RATE}
    concat_lines = []
    total_all = 0.0
    for sid in sorted(SCENES.keys()):
        entries = []
        for i, txt in enumerate(SCENES[sid]):
            p = os.path.join(OUT, f"s{sid:02d}_s{i:02d}.mp3")
            if not os.path.exists(p):
                await synth(txt, p)
            d = dur_of(p) or 0.0
            entries.append({"i": i, "text": txt,
                            "file": f"s{sid:02d}_s{i:02d}.mp3",
                            "dur": round(d, 3)})
            concat_lines.append(f"file '{p}'".replace("\\", "/"))
        total = round(sum(e["dur"] for e in entries), 3)
        total_all += total
        timeline["scenes"][f"s{sid:02d}"] = {"segs": entries, "total": total}
        print(f"[场景{sid:02d}] 句数={len(entries)} 总长={total}s")
    timeline["total"] = round(total_all, 3)

    with open(os.path.join(OUT, "concat.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(concat_lines) + "\n")
    with open(os.path.join(BASE, "timeline-full.json"), "w", encoding="utf-8") as f:
        json.dump(timeline, f, ensure_ascii=False, indent=2)
    print(f"\n=== 全片口播总长 = {round(total_all,3)}s = {round(total_all/60,2)} 分钟 ===")
    print("saved timeline-full.json + audio_full/concat.txt")

    # 顺带生成全片配音（需 ffmpeg）
    import subprocess as sp
    full = os.path.join(OUT, "narr_full.mp3")
    sp.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", os.path.join(OUT, "concat.txt"), "-c", "copy", full],
           check=False)
    print("saved narr_full.mp3")

if __name__ == "__main__":
    asyncio.run(main())