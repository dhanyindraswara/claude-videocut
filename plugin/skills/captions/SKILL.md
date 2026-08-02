---
name: captions
description: Burn styled captions/subtitles into video — classic SRT subtitles or modern word-pop social-media captions (TikTok/Reels/Shorts style) generated from the transcript. Use when the user wants captions, subtitles, teks, or on-screen text of what is spoken.
---

# Captions

Invoke `videocut-basics` first. Requires a transcript (`transcribe` skill) **of the
final cut** — if the video was smart-cut after transcription, re-transcribe the cut file.

## Option A — classic subtitles (fast, clean)

Burn the SRT with styling via `force_style`:

```bash
ffmpeg -y -i work/cut_v1.mp4 -vf "subtitles=work/cut_v1.srt:force_style='FontName=Arial,FontSize=13,Bold=1,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=1.2,MarginV=28'" \
  -c:v libx264 -crf 18 -preset medium -c:a copy work/captioned_v1.mp4
```

Colour format is `&HAABBGGRR` (note BGR order). Yellow = `&H0000FFFF`.

## Option B — word-pop social captions (styled ASS)

Generate an ASS file with 1–4 words per caption line, bold, centered, with the
current word highlighted:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/make_ass.py" work/cut_v1.transcript.json \
  -o work/captions.ass --max-words 3 --font "Arial Black" --size 16 \
  --highlight "&H0000FFFF" --position mid
ffmpeg -y -i work/cut_v1.mp4 -vf "ass=work/captions.ass" \
  -c:v libx264 -crf 18 -preset medium -c:a copy work/captioned_v1.mp4
```

- `--position mid|low` — `mid` for 9:16 vertical (keeps captions off UI overlays), `low` for 16:9.
- `--size` is relative to a 384-line reference; 14–18 suits vertical video.

## Verify (mandatory)

Extract frames at 3–4 caption moments and **look at them**: text inside safe area,
not overlapping faces, readable contrast, correct words. Fix wording by editing the
SRT/ASS (or transcript JSON) directly — never ship captions you haven't seen rendered.
