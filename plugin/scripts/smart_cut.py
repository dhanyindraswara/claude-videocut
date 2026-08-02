#!/usr/bin/env python3
"""Transcript-driven cutting: build a keep-segment edit plan, then render it.

  plan   transcript.json -o edit_plan.json  [--max-pause 0.8] [--pad 0.10]
                                            [--lang id|en|both] [--fillers a,b]
                                            [--no-fillers]
  apply  edit_plan.json -i source.mp4 -o out.mp4 [--crf 18]

The plan is plain JSON (source + [{start,end,label}]) and is meant to be
reviewed/edited by hand before applying.
"""
import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path

FILLERS = {
    "en": {"um", "uh", "uhm", "er", "erm", "hmm", "mm", "mmm", "ah", "eh"},
    "id": {"eh", "em", "emm", "ehm", "hmm", "mmm", "anu", "apa", "ya"},
}
# "apa"/"ya" are only fillers when isolated between pauses; handled below.
WEAK_FILLERS = {"apa", "ya", "ah", "eh"}


def norm(word: str) -> str:
    return word.strip().strip(".,!?…-—\"'()[]").lower()


def load_words(transcript: dict) -> list:
    words = []
    for seg in transcript["segments"]:
        for w in seg.get("words", []):
            if w["word"].strip():
                words.append(w)
    return words


def build_plan(transcript: dict, max_pause: float, pad: float,
               fillers: set, duration: float) -> tuple:
    words = load_words(transcript)
    if not words:
        return [], {"error": "transcript has no word timestamps"}

    kept, dropped_fillers = [], []
    for i, w in enumerate(words):
        n = norm(w["word"])
        if n in fillers:
            gap_before = w["start"] - words[i - 1]["end"] if i else w["start"]
            gap_after = (words[i + 1]["start"] - w["end"]
                         if i + 1 < len(words) else duration - w["end"])
            # weak fillers only count when isolated by pauses on both sides
            if n not in WEAK_FILLERS or (gap_before > 0.25 and gap_after > 0.25):
                dropped_fillers.append(w)
                continue
        kept.append(w)

    if not kept:
        return [], {"error": "everything classified as filler; loosen options"}

    # merge kept words into segments, splitting where the pause exceeds max_pause
    segments = []
    cur_start, cur_end = kept[0]["start"], kept[0]["end"]
    for w in kept[1:]:
        if w["start"] - cur_end > max_pause:
            segments.append([cur_start, cur_end])
            cur_start = w["start"]
        cur_end = max(cur_end, w["end"])
    segments.append([cur_start, cur_end])

    # pad and clamp, then merge overlaps introduced by padding
    padded = []
    for s, e in segments:
        s, e = max(0.0, s - pad), min(duration, e + pad)
        if padded and s <= padded[-1][1]:
            padded[-1][1] = max(padded[-1][1], e)
        else:
            padded.append([s, e])

    plan_segments = [
        {"start": round(s, 3), "end": round(e, 3), "label": f"seg{i+1}"}
        for i, (s, e) in enumerate(padded)
    ]
    kept_total = sum(e - s for s, e in padded)
    stats = {
        "fillers_removed": len(dropped_fillers),
        "filler_words": [f'{w["word"].strip()}@{w["start"]:.1f}s'
                         for w in dropped_fillers][:40],
        "segments": len(plan_segments),
        "original_duration": round(duration, 2),
        "kept_duration": round(kept_total, 2),
        "time_saved": round(duration - kept_total, 2),
    }
    return plan_segments, stats


def cmd_plan(args) -> int:
    transcript = json.loads(Path(args.transcript).read_text(encoding="utf-8"))
    duration = float(transcript.get("duration") or
                     transcript["segments"][-1]["end"])
    fillers = set()
    if not args.no_fillers:
        if args.lang in ("id", "both"):
            fillers |= FILLERS["id"]
        if args.lang in ("en", "both"):
            fillers |= FILLERS["en"]
    if args.fillers:
        fillers |= {norm(f) for f in args.fillers.split(",")}

    segments, stats = build_plan(transcript, args.max_pause, args.pad,
                                 fillers, duration)
    if not segments:
        print(json.dumps(stats, indent=2), file=sys.stderr)
        return 1

    plan = {"source": transcript.get("source", ""), "segments": segments}
    Path(args.output).write_text(json.dumps(plan, ensure_ascii=False, indent=2),
                                 encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    print(f"\nwrote {args.output} — review/edit it, then run:  "
          f"smart_cut.py apply {args.output} -i <source> -o <out.mp4>")
    return 0


def cmd_apply(args) -> int:
    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    segs = plan["segments"]
    if not segs:
        print("plan has no segments", file=sys.stderr)
        return 1
    src = args.input or plan.get("source")
    if not src or not Path(src).exists():
        print(f"source not found: {src!r} (pass -i)", file=sys.stderr)
        return 1

    vf, af, refs = [], [], []
    for i, s in enumerate(segs):
        vf.append(f"[0:v]trim=start={s['start']}:end={s['end']},"
                  f"setpts=PTS-STARTPTS[v{i}]")
        af.append(f"[0:a]atrim=start={s['start']}:end={s['end']},"
                  f"asetpts=PTS-STARTPTS[a{i}]")
        refs.append(f"[v{i}][a{i}]")
    fc = ";".join(vf + af) + f";{''.join(refs)}concat=n={len(segs)}:v=1:a=1[v][a]"

    cmd = ["ffmpeg", "-y", "-i", src, "-filter_complex", fc,
           "-map", "[v]", "-map", "[a]",
           "-c:v", "libx264", "-crf", str(args.crf), "-preset", "medium",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
           args.output]
    print("running:", " ".join(shlex.quote(c) for c in cmd[:6]),
          f"... ({len(segs)} segments)")
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        print(proc.stderr[-2000:], file=sys.stderr)
        return proc.returncode
    total = sum(s["end"] - s["start"] for s in segs)
    print(f"wrote {args.output} (~{total:.1f}s from {len(segs)} segments)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("plan", help="build edit plan from transcript")
    p.add_argument("transcript")
    p.add_argument("-o", "--output", default="edit_plan.json")
    p.add_argument("--max-pause", type=float, default=0.8,
                   help="tighten silences longer than this (s)")
    p.add_argument("--pad", type=float, default=0.10,
                   help="padding around kept speech (s)")
    p.add_argument("--lang", choices=["id", "en", "both"], default="both")
    p.add_argument("--fillers", help="extra comma-separated filler words")
    p.add_argument("--no-fillers", action="store_true",
                   help="only tighten silences, keep fillers")
    p.set_defaults(func=cmd_plan)

    a = sub.add_parser("apply", help="render the plan with ffmpeg")
    a.add_argument("plan")
    a.add_argument("-i", "--input", help="source video (default: plan.source)")
    a.add_argument("-o", "--output", required=True)
    a.add_argument("--crf", type=int, default=18)
    a.set_defaults(func=cmd_apply)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
