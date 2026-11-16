# -*- coding: utf-8 -*-
"""build_video.py — 把逐帧渲染结果合成为成片。

阶段：
  pages  : html_frames/pNN/f*.png 序列 → html_pages/page_NN.mp4（自带该页配音）
  concat : 拼接 12 页 → full_video.mp4
  srt    : 由配音稿（timeline.json 的 segs）生成「按标点分割」的字幕
  final  : 烧录字幕 → 有字幕版；同时输出无字幕版
"""
import json
import os
import re
import shutil
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
FF = r"C:\Users\chenfeng\.workbuddy\binaries\python\envs\default\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"
FRAME_ROOT = os.path.join(BASE, "html_frames2")
PAGE_DIR = os.path.join(BASE, "html_pages")
AUDIO_DIR = os.path.join(BASE, "audio", "pages")
FPS = 25
W, H = 1920, 1080
TAIL = 0.30
NAME = "非车险综合治理政策解读"

os.makedirs(PAGE_DIR, exist_ok=True)


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        print("STDERR:\n", r.stderr[-2500:])
        raise SystemExit("ffmpeg failed rc=%d" % r.returncode)
    return r


def load_tl():
    with open(os.path.join(BASE, "timeline.json"), encoding="utf-8") as f:
        return json.load(f)


def rename_frames(frame_dir):
    """f0.png → f00000.png，供 ffmpeg 用 f%05d.png 直接读取。

    注意：必须先重命名**新渲染的原始帧**（fN.png，无前导零），并覆盖可能残留的
    同名 f%05d.png，否则会误用上一次构建遗留的旧帧（表现为帧数翻倍）。
    """
    fs = [f for f in os.listdir(frame_dir) if re.fullmatch(r"f\d+\.png", f)]
    # 原始帧 = 不匹配 5 位补零规范名的文件
    raw = [f for f in fs if not re.fullmatch(r"f\d{5}\.png", f)]
    norm_idx = {int(m.group(1)) for f in fs
                if (m := re.fullmatch(r"f(\d{5})\.png", f))}
    raw_idx = []
    for f in raw:
        n = int(re.search(r"f(\d+)", f).group(1))
        raw_idx.append(n)
        os.replace(os.path.join(frame_dir, f),
                   os.path.join(frame_dir, "f%05d.png" % n))   # 覆盖旧帧
    # 删除超出本次帧范围的旧规范帧（页长变短时避免残留）
    if raw_idx:
        hi = max(raw_idx)
        for n in sorted(i for i in norm_idx if i > hi):
            os.remove(os.path.join(frame_dir, "f%05d.png" % n))


def stage_pages(tl):
    for k in sorted(tl["pages"], key=int):
        pid = int(k)
        fdir = os.path.join(FRAME_ROOT, "p%02d" % pid)
        audio = os.path.join(AUDIO_DIR, "page_%02d.wav" % pid)
        out = os.path.join(PAGE_DIR, "page_%02d.mp4" % pid)
        if not os.path.isdir(fdir):
            print("skip page %d (no frames)" % pid)
            continue
        if os.path.exists(out):
            print("skip page %d (exists)" % pid)
            continue
        # 校验本次渲染所需的连续帧 f00000..f{want-1} 是否齐全。
        # render.js 直接按 f%05d 命名输出（原地覆盖），因此无需重命名/删除；
        # ffmpeg 的 image2 解复用按序号连续读取，超出范围的旧帧不会被用到。
        want = max(1, round((tl["pages"][k]["total"] + TAIL) * FPS))
        missing = [i for i in range(want)
                   if not os.path.exists(os.path.join(fdir, "f%05d.png" % i))]
        if missing:
            print("skip page %d (missing %d/%d frames, e.g. f%05d)"
                  % (pid, len(missing), want, missing[0]))
            continue
        run([FF, "-y", "-framerate", str(FPS), "-i", os.path.join(fdir, "f%05d.png"),
             "-i", audio, "-frames:v", str(want),
             "-vf", "scale=%d:%d,format=yuv420p" % (W, H),
             "-af", "apad", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
             "-c:a", "aac", "-b:a", "192k", "-shortest", out])
        print("page %d -> %s" % (pid, os.path.basename(out)))
    print("STAGE PAGES DONE")


def stage_concat(tl):
    lst = os.path.join(PAGE_DIR, "list.txt")
    with open(lst, "w", encoding="utf-8") as f:
        for k in sorted(tl["pages"], key=int):
            f.write("file '%s'\n" % os.path.join(PAGE_DIR, "page_%02d.mp4" % int(k)).replace("\\", "/"))
    out = os.path.join(BASE, "full_video.mp4")
    run([FF, "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy",
         "-movflags", "+faststart", out])
    print("STAGE CONCAT DONE ->", out)


# ---------- 字幕：按标点符号分割 ----------
SPLIT_PUNCT = "，。；、！？："


def split_punct(text):
    """按标点切分为语义短句（标点保留在前句尾）。"""
    cues, buf = [], ""
    for ch in text:
        buf += ch
        if ch in SPLIT_PUNCT:
            cues.append(buf)
            buf = ""
    if buf.strip():
        cues.append(buf)
    # 合并过短句，避免闪字幕
    merged = []
    for c in cues:
        if merged and len(merged[-1]) < 8:
            merged[-1] += c
        else:
            merged.append(c)
    return [c.strip() for c in merged if c.strip()]


def wrap_cue(s, per_line=21):
    """过长字幕折行（最多 2 行，按标点/中点优先）。"""
    if len(s) <= per_line:
        return s
    # 优先在标点处折
    for i in range(per_line, max(6, per_line - 8), -1):
        if i < len(s) and s[i] in SPLIT_PUNCT:
            return s[:i + 1] + "\n" + s[i + 1:]
    mid = min(per_line, len(s))
    return s[:mid] + "\n" + s[mid:]


def fmt_ts(sec):
    ms = int(round(max(0.0, sec) * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return "%02d:%02d:%02d,%03d" % (h, m, s, ms)


def build_cues(tl):
    """按标点分割 + 页内/全局时间对齐，产出 (start, end, text) 列表。"""
    cues, offset = [], 0.0
    for k in sorted(tl["pages"], key=int):
        page = tl["pages"][k]
        for sg in page["segs"]:
            parts = split_punct(sg["text"])
            if not parts:
                continue
            weights = [len(c) for c in parts]
            tot = sum(weights) or 1
            acc = sg["start"]
            for c, w in zip(parts, weights):
                dur = max(0.7, sg["dur"] * w / tot)
                cues.append((offset + acc, offset + acc + dur, c))
                acc += dur
        offset += page["total"] + TAIL
    return cues


def stage_srt(tl):
    cues = build_cues(tl)
    lines = []
    for i, (s, e, c) in enumerate(cues, 1):
        lines += [str(i), fmt_ts(s) + " --> " + fmt_ts(e), wrap_cue(c), ""]
    out = os.path.join(BASE, "subs.srt")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("SRT -> %s  (%d cues)" % (out, len(cues)))
    return out


def fmt_ass_ts(sec):
    cs = int(round(max(0.0, sec) * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return "%d:%02d:%02d.%02d" % (h, m, s, cs)


def stage_ass(tl):
    """生成带显式分辨率的 ASS，避免 libass 默认 288p 造成的字号放大。"""
    cues = build_cues(tl)
    head = [
        "[Script Info]",
        "ScriptType: v4.00+",
        "PlayResX: 1920",
        "PlayResY: 1080",
        "WrapStyle: 2",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
        "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
        "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        # FontSize=52 -> 1080p 下约 52px 字高；描边深绿，底部居中
        "Style: Default,Microsoft YaHei,52,&H00FFFFFF,&H000000FF,&H001F3A16,"
        "&H64000000,0,0,0,0,100,100,0,0,1,2,1,2,80,80,46,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    body = []
    for s, e, c in cues:
        txt = c.strip().replace("\n", "\\N")
        body.append("Dialogue: 0,%s,%s,Default,,0,0,0,,%s" % (fmt_ass_ts(s), fmt_ass_ts(e), txt))
    out = os.path.join(BASE, "subs.ass")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(head + body) + "\n")
    print("ASS -> %s  (%d cues)" % (out, len(cues)))
    return out


def stage_final(tl):
    stage_srt(tl)
    ass = stage_ass(tl)
    # burn.srt 同目录解析（ffmpeg subtitles 滤镜相对 filters 工作目录）
    shutil.copyfile(ass, os.path.join(BASE, "burn.ass"))
    shutil.copyfile(os.path.join(BASE, "subs.srt"), os.path.join(BASE, "burn.srt"))
    src = os.path.join(BASE, "full_video.mp4")
    out_sub = os.path.join(BASE, "%s（动画版）.mp4" % NAME)
    out_no = os.path.join(BASE, "%s（动画版·无字幕）.mp4" % NAME)
    run([FF, "-y", "-i", src, "-vf", "subtitles=burn.ass",
         "-c:v", "libx264", "-preset", "medium", "-crf", "20",
         "-c:a", "copy", "-movflags", "+faststart", out_sub], cwd=BASE)
    # 无字幕版同样 remux 到 faststart，保证可秒开
    run([FF, "-y", "-i", src, "-c", "copy", "-movflags", "+faststart", out_no], cwd=BASE)
    print("STAGE FINAL DONE\n  %s\n  %s" % (out_sub, out_no))


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "pages"
    tl = load_tl()
    if stage == "pages":
        stage_pages(tl)
    elif stage == "concat":
        stage_concat(tl)
    elif stage == "srt":
        stage_srt(tl)
    elif stage == "final":
        stage_final(tl)
    elif stage == "all":
        stage_pages(tl)
        stage_concat(tl)
        stage_final(tl)