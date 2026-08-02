# VideoCut 🎬

**Free, local AI video editor plugin for Claude Code.**
Edit and export video entirely from chat — Claude is the editor, `ffmpeg` is the
render engine, `faster-whisper` is the ear. No cloud, no accounts, no credits.

## What it does

- **Transcribe** — word-level timestamps, offline Whisper (Indonesian, English, 90+ languages)
- **Smart cut** — auto-remove filler words (*um, uh, eh, anu*), dead air, and any spoken section you name
- **Captions** — classic subtitles or TikTok/Reels-style word-pop captions, burned in
- **Edit ops** — trim, join, speed, vertical 9:16 crop, logo overlay, titles, crossfades
- **Audio** — background music with auto-ducking under speech, loudness normalize, denoise
- **Export** — presets for YouTube, Reels/TikTok/Shorts, WhatsApp, GIF, MP3

Everything is non-destructive: cuts live in a reviewable JSON edit plan, sources are
never touched, and Claude verifies every render with ffprobe + preview frames before
calling it done.

## Requirements

- [ffmpeg](https://ffmpeg.org/download.html) (`brew install ffmpeg` / `sudo apt install ffmpeg` / `winget install ffmpeg`)
- Python 3.9+
- `pip install faster-whisper` — only needed for transcription/caption features

## Install

From GitHub:

```bash
claude plugin marketplace add https://github.com/dhanyindraswara/claude-videocut.git
claude plugin install videocut@videocut
```

Or from a local clone:

```bash
claude plugin marketplace add /path/to/claude-videocut
claude plugin install videocut@videocut
```

Then start a **new** Claude Code conversation and try:

> Edit ~/Videos/talk.mp4: remove the filler words and long pauses, add captions,
> and export it for YouTube.

## Layout

```
.claude-plugin/marketplace.json   marketplace manifest
plugin/
  .claude-plugin/plugin.json      plugin manifest
  skills/                         7 skills Claude loads on demand
  scripts/
    transcribe.py                 faster-whisper → transcript JSON + SRT
    smart_cut.py                  plan (fillers/silences → edit plan) + apply (render)
    make_ass.py                   transcript → styled word-pop ASS captions
```

## License

MIT — do whatever you want with it.
