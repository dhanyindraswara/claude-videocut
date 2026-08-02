#!/usr/bin/env python3
"""Build styled ASS captions (social-media word-pop style) from a transcript JSON.

Groups words into short caption lines (default 3 words) and highlights the
word being spoken. Burn with:  ffmpeg -i in.mp4 -vf "ass=captions.ass" ...

Usage:
  python3 make_ass.py work/video.transcript.json -o work/captions.ass \
      [--max-words 3] [--font "Arial Black"] [--size 16] \
      [--highlight "&H0000FFFF"] [--position mid|low]
"""
import argparse
import json
import sys
from pathlib import Path

HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 384
PlayResY: 288
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{font},{size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,2,1,{align},20,20,{marginv},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def ts(t: float) -> str:
    cs = int(round(t * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02}:{s:02}.{cs:02}"


def esc(text: str) -> str:
    return text.replace("{", "(").replace("}", ")").replace("\n", " ")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("transcript")
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--max-words", type=int, default=3)
    ap.add_argument("--font", default="Arial Black")
    ap.add_argument("--size", type=int, default=16)
    ap.add_argument("--highlight", default="&H0000FFFF",
                    help="ASS colour &HAABBGGRR for the active word "
                         "(default yellow); empty string disables highlighting")
    ap.add_argument("--position", choices=["mid", "low"], default="low",
                    help="mid = center-ish (vertical video), low = bottom")
    args = ap.parse_args()

    transcript = json.loads(Path(args.transcript).read_text(encoding="utf-8"))
    words = [w for seg in transcript["segments"]
             for w in seg.get("words", []) if w["word"].strip()]
    if not words:
        print("transcript has no word timestamps", file=sys.stderr)
        return 1

    align, marginv = ("5", "0") if args.position == "mid" else ("2", "24")
    lines = [HEADER.format(font=args.font, size=args.size,
                           align=align, marginv=marginv)]

    # group into caption chunks, breaking early at sentence punctuation
    groups, cur = [], []
    for w in words:
        cur.append(w)
        if (len(cur) >= args.max_words
                or w["word"].strip()[-1:] in ".!?…"):
            groups.append(cur)
            cur = []
    if cur:
        groups.append(cur)

    for gi, group in enumerate(groups):
        g_start = group[0]["start"]
        # hold the caption until the next group starts (max 1.5s of silence)
        next_start = (groups[gi + 1][0]["start"] if gi + 1 < len(groups)
                      else group[-1]["end"])
        g_end = min(next_start, group[-1]["end"] + 1.5)
        if not args.highlight:
            text = esc(" ".join(w["word"].strip() for w in group))
            lines.append(f"Dialogue: 0,{ts(g_start)},{ts(g_end)},Cap,,0,0,0,,{text}")
            continue
        # one Dialogue per word-state so the active word is coloured
        for wi, w in enumerate(group):
            w_start = w["start"] if wi else g_start
            w_end = group[wi + 1]["start"] if wi + 1 < len(group) else g_end
            if w_end <= w_start:
                continue
            parts = []
            for wj, ww in enumerate(group):
                token = esc(ww["word"].strip())
                if wj == wi:
                    parts.append(f"{{\\c{args.highlight}}}{token}{{\\c&H00FFFFFF}}")
                else:
                    parts.append(token)
            lines.append(f"Dialogue: 0,{ts(w_start)},{ts(w_end)},Cap,,0,0,0,,"
                         + " ".join(parts))

    Path(args.output).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {args.output} ({len(groups)} captions, {len(words)} words)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
