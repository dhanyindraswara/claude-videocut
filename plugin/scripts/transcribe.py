#!/usr/bin/env python3
"""Transcribe media locally with faster-whisper.

Outputs, next to -o dir:
  <name>.transcript.json  - segments with word-level timestamps (drives smart_cut/make_ass)
  <name>.srt              - plain subtitles

Usage:
  python3 transcribe.py video.mp4 -o work/ [--model small] [--language id]
"""
import argparse
import json
import os
import sys
from pathlib import Path

BLOCKED_HINT = """
Could not obtain the Whisper model '{model}'.

The model downloads from huggingface.co on first use. If you are in a Claude Code
cloud session, that host is blocked under the default 'Trusted' network level —
set the environment's Network access to Custom and allow huggingface.co,
*.huggingface.co and *.hf.co, then start a NEW session. See cloud/README.md.

ffmpeg-only features (trim, join, crop, speed, overlay, music, export) do not
need this and keep working.

Underlying error: {err}
""".strip()


def fmt_srt(t: float) -> str:
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input")
    ap.add_argument("-o", "--outdir", default=".")
    ap.add_argument("--model", default=os.environ.get("VIDEOCUT_WHISPER_MODEL", "small"),
                    help="tiny|base|small|medium|large-v3, or a path to a local "
                         "model dir (default: $VIDEOCUT_WHISPER_MODEL or small)")
    ap.add_argument("--language", default=None,
                    help="ISO code e.g. id, en; omit for auto-detect")
    args = ap.parse_args()

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("faster-whisper is not installed. Run: pip install faster-whisper",
              file=sys.stderr)
        return 1

    src = Path(args.input)
    if not src.exists():
        print(f"input not found: {src}", file=sys.stderr)
        return 1
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    try:
        model = WhisperModel(args.model, device="auto", compute_type="auto")
    except Exception as err:  # network block, bad name, corrupt cache
        print(BLOCKED_HINT.format(model=args.model, err=err), file=sys.stderr)
        return 2
    segments_iter, info = model.transcribe(
        str(src),
        language=args.language,
        word_timestamps=True,
        vad_filter=True,
    )

    segments = []
    srt_lines = []
    for i, seg in enumerate(segments_iter, 1):
        words = [
            {"start": round(w.start, 3), "end": round(w.end, 3), "word": w.word.strip()}
            for w in (seg.words or [])
        ]
        segments.append({
            "start": round(seg.start, 3),
            "end": round(seg.end, 3),
            "text": seg.text.strip(),
            "words": words,
        })
        srt_lines += [str(i), f"{fmt_srt(seg.start)} --> {fmt_srt(seg.end)}",
                      seg.text.strip(), ""]
        print(f"[{fmt_srt(seg.start)}] {seg.text.strip()}", flush=True)

    stem = src.stem
    result = {
        "source": str(src),
        "language": info.language,
        "language_probability": round(info.language_probability, 3),
        "duration": round(info.duration, 3),
        "model": args.model,
        "segments": segments,
    }
    json_path = outdir / f"{stem}.transcript.json"
    srt_path = outdir / f"{stem}.srt"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2),
                         encoding="utf-8")
    srt_path.write_text("\n".join(srt_lines), encoding="utf-8")

    n_words = sum(len(s["words"]) for s in segments)
    print(f"\nlanguage={info.language} (p={info.language_probability:.2f}) "
          f"duration={info.duration:.1f}s segments={len(segments)} words={n_words}")
    print(f"wrote {json_path}\nwrote {srt_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
