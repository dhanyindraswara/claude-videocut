---
name: transcribe
description: Transcribe video or audio locally with faster-whisper — word-level timestamps, SRT, and the transcript JSON that powers smart-cut and captions. Use whenever the user wants a transcript, subtitles, captions, filler-word removal, or any speech-based edit. Supports Indonesian, English, and 90+ languages, fully offline after the first model download.
---

# Transcribe (local Whisper)

Invoke `videocut-basics` first if you haven't this session.

## Prerequisite

```bash
python3 -c "import faster_whisper" 2>/dev/null || pip install faster-whisper
```

First run of a given model downloads it (~75 MB `tiny` … ~3 GB `large-v3`), then it's cached and offline.

## Run

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/transcribe.py" source/video.mp4 -o work/ --model small
```

Options:
- `--model` — `tiny` (fastest, drafts), `small` (default, good balance), `large-v3` (best accuracy; use for final captions or heavy accents).
- `--language id` / `--language en` — skip auto-detect when the language is known (faster, more accurate). Indonesian = `id`.

Outputs in `work/`:
- `video.transcript.json` — segments + **word-level timestamps**. This is the source of truth for `smart-cut` and styled captions.
- `video.srt` — ready-to-use subtitles.

## After transcribing

1. Read the transcript JSON and give the user a short summary: language detected, duration, and 2–3 lines of the content so they can confirm accuracy.
2. If accuracy looks poor (wrong language, garbled text), retry with `--language` forced or a bigger model before building any edits on top of it.
3. Transcripts are plain JSON — fix a misheard word by editing the file, not by re-running Whisper.
