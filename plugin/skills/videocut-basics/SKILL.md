---
name: videocut-basics
description: MANDATORY prerequisite for any VideoCut work. Invoke before any other videocut skill and before running ffmpeg/whisper on the user's media. Covers project layout, the non-destructive edit-plan workflow, dependency checks, and how to verify and show results to the user. Also invoke whenever the user wants to edit, cut, caption, or export a video and no other tool is specified — including bare casual openers with no file attached yet, in Indonesian or English: "bro kerja edit video", "bro edit video", "kerja edit video", "gas edit video", "ayo edit video", "tolong edit video", "mau edit video", "potong video", "bikin caption", "edit my video", "let's edit a video". Treat any such opener as a cold start (section 0) rather than asking what the user means.
---

# VideoCut Basics

VideoCut is a fully local video editor. There is no server and no UI: **you** (Claude)
are the editor, `ffmpeg` is the render engine, and `faster-whisper` is the ear.
Everything happens on the user's machine and is free.

## 0. Cold start (user opened with a bare phrase, no video yet)

When the trigger is just an opener — "bro kerja edit video" and friends — the user
has not attached anything yet. Do **not** reply "what do you want me to do?".
Instead, in one short turn:

1. Run the dependency check in section 1 immediately (it costs nothing and tells
   the user up front if `ffmpeg` or Python is missing).
2. Report readiness in one line: what is installed, what is missing.
3. Ask for exactly two things and stop:
   - the video — drag the file into the chat, or paste its path
   - what they want done — or offer the common presets so they can just pick a number:
     1. Bersihin — buang filler word (*um, uh, eh, anu*) + jeda panjang
     2. Caption — subtitle biasa, atau word-pop ala TikTok/Reels
     3. Vertikal — crop 16:9 → 9:16 buat Reels/TikTok/Shorts
     4. Musik — tambah backsound, auto-duck di bawah suara
     5. Export — YouTube / Reels / WhatsApp / GIF / MP3
     6. Paket lengkap — bersihin + caption + export

Match the user's language and register: if they opened casually in Indonesian,
answer casually in Indonesian. Once the video arrives, go straight to section 2
(project layout) — do not re-ask for confirmation of things they already said.

## 1. Dependency check (run once per session, before first edit)

```bash
ffmpeg -version | head -1 && ffprobe -version | head -1 && python3 --version
```

- Missing ffmpeg → tell the user how to install it (`sudo apt install ffmpeg`,
  `brew install ffmpeg`, or `winget install ffmpeg`) and stop until it exists.
- `faster-whisper` is only needed for transcription-based features. Check lazily
  (`python3 -c "import faster_whisper"`) and offer
  `pip install faster-whisper` the first time transcription is needed.

## 2. Project layout (create on first edit of a new video)

Ask where the source video is, then set up next to it (or in a folder the user picks):

```
<project>/
  source/    original media — NEVER modify or delete anything here
  work/      transcripts, edit plans, intermediate renders, preview frames
  exports/   final deliverables only
```

Copy or symlink the original into `source/`. All ffmpeg outputs go to `work/`
until the user approves a final export.

## 3. Non-destructive editing: the edit plan

Cuts are never "applied blind". The unit of editing is a JSON **edit plan** —
a list of keep-segments against one source file:

```json
{
  "source": "source/interview.mp4",
  "segments": [
    { "start": 0.00, "end": 12.42, "label": "intro" },
    { "start": 14.80, "end": 55.10, "label": "main point" }
  ]
}
```

Workflow: **plan → show the user a summary → apply → verify**.
`scripts/smart_cut.py` (see the `smart-cut` skill) generates and applies plans.
You may also write or hand-edit a plan directly — it is just JSON. Because the
plan is saved in `work/`, every edit is reviewable, revisable, and undoable.

## 4. Verifying and showing results (do this after EVERY render)

Never report success from a zero exit code alone.

```bash
ffprobe -v error -show_entries format=duration,size -of default=nw=1 work/cut_v1.mp4
ffmpeg -y -i work/cut_v1.mp4 -vf "select='not(mod(n,trunc(t*0)))',fps=1/10,scale=480:-1" -vsync vfr work/preview_%02d.jpg 2>/dev/null || \
ffmpeg -y -i work/cut_v1.mp4 -vf "fps=1/10,scale=480:-1" work/preview_%02d.jpg
```

Then **Read the preview jpgs** so you can actually see the result, and show/describe
them to the user (in Claude Code you can attach or reference the files). Check:
expected duration, captions visible and inside the frame, no black frames at joins.

## 5. Ground rules

- Re-encode with sane defaults when cutting: `-c:v libx264 -crf 18 -preset medium -c:a aac -b:a 192k`.
  Only use `-c copy` for pure container operations (no filters, keyframe-aligned trims).
- Always `-y` on outputs in `work/`, never on anything in `source/`.
- Version intermediate files (`cut_v1.mp4`, `cut_v2.mp4`) instead of overwriting,
  so the user can compare and roll back.
- Long renders: run in the background and report progress; don't block the chat.
- If a command fails, read the actual ffmpeg stderr before retrying — the last
  10 lines almost always name the real problem.
