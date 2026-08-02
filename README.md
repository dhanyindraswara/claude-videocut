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

## No local install: run it in Claude Code on the web

You can skip your machine entirely and edit from a browser chat. It takes a
one-time environment change — allow `huggingface.co` and paste a setup script —
after which every session starts with ffmpeg and Whisper ready.

**→ [`cloud/README.md`](./cloud/README.md)**

Worth knowing before you commit to it: cloud sessions are ephemeral, uploads are
the slow part rather than the render, and transcription runs on CPU.

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

Install is **once per machine** — it is saved in your user settings, so you never
have to run those two commands again.

## Usage

Start a **new** Claude Code conversation and just say it like a human:

> bro kerja edit video

VideoCut wakes up, checks that `ffmpeg` and Python are ready, and asks you to drop
the video plus a numbered preset. Then attach the file (drag it into the chat or
paste the path) and pick. Other openers that work the same way: *bro edit video*,
*gas edit video*, *tolong edit video*, *potong video*, *bikin caption*,
*let's edit a video*, *edit my video*.

This is deterministic, not a guess: a bundled `UserPromptSubmit` hook
(`plugin/hooks/videocut_trigger.py`) recognises those openers and tells Claude to
load the skill. Every pattern requires you to name the medium — *video*, *klip*,
*footage* — so ordinary prompts are never hijacked. `/videocut:edit-video` does
the same thing if you prefer a slash command.

Or skip the back-and-forth and say the whole thing at once:

> Edit ~/Videos/talk.mp4: remove the filler words and long pauses, add captions,
> and export it for YouTube.

## Layout

```
.claude-plugin/marketplace.json   marketplace manifest
plugin/
  .claude-plugin/plugin.json      plugin manifest
  skills/                         7 skills Claude loads on demand
  commands/edit-video.md          /videocut:edit-video
  hooks/
    hooks.json                    UserPromptSubmit registration
    videocut_trigger.py           plain-language openers → load the skill
  scripts/
    transcribe.py                 faster-whisper → transcript JSON + SRT
    smart_cut.py                  plan (fillers/silences → edit plan) + apply (render)
    make_ass.py                   transcript → styled word-pop ASS captions
```

## License

MIT — do whatever you want with it.
