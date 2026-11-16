import json, sys

def main():
    if len(sys.argv) < 2:
        print("用法: python calc_seg_times.py <timeline-full.json> [场景id 如 s09]")
        sys.exit(1)

    path = sys.argv[1]
    data = json.load(open(path, encoding="utf-8"))
    want = sys.argv[2] if len(sys.argv) > 2 else None

    scenes = data.get("scenes", {})
    ids = sorted(scenes.keys(), key=lambda x: int(x[1:]))
    if want and want in scenes:
        ids = [want]

    for sid in ids:
        s = scenes[sid]
        print(f"=== {sid} total={s['total']} ===")
        acc = 0.0
        for e in s["segs"]:
            start = acc
            end = acc + e["dur"]
            print(f"  i{e['i']}: start={start:.3f} end={end:.3f} dur={e['dur']:.3f} | {e['text'][:30]}")
            acc = end

if __name__ == "__main__":
    main()