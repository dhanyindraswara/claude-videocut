---
name: export
description: Final delivery renders with the right preset — YouTube 1080p/4K, Instagram Reels / TikTok / Shorts 9:16, WhatsApp-friendly small file, GIF, or audio-only MP3. Use when the user says export, render, final, save, kirim, or names a target platform.
---

# Export

Invoke `videocut-basics` first. Exports are the ONLY files that go to `exports/`.
Run loudness normalization (see `audio-mix`) before or during export.

## Presets

```bash
# YouTube 1080p — quality first
ffmpeg -y -i work/final_cut.mp4 -c:v libx264 -crf 18 -preset slow -pix_fmt yuv420p \
  -c:a aac -b:a 192k -movflags +faststart exports/video_youtube.mp4

# Reels / TikTok / Shorts (must already be 9:16 — see edit-ops vertical recipe)
ffmpeg -y -i work/final_vertical.mp4 -c:v libx264 -crf 20 -preset slow -pix_fmt yuv420p \
  -c:a aac -b:a 160k -movflags +faststart exports/video_reels.mp4

# WhatsApp-friendly (small, still decent)
ffmpeg -y -i work/final_cut.mp4 -vf "scale=-2:720" -c:v libx264 -crf 26 -preset slow \
  -pix_fmt yuv420p -c:a aac -b:a 128k -movflags +faststart exports/video_wa.mp4

# GIF (short clips only)
ffmpeg -y -ss 0 -t 4 -i work/final_cut.mp4 -filter_complex \
 "fps=12,scale=480:-1:flags=lanczos,split[a][b];[a]palettegen[p];[b][p]paletteuse" exports/clip.gif

# Audio only
ffmpeg -y -i work/final_cut.mp4 -vn -c:a libmp3lame -q:a 2 exports/audio.mp3
```

`-movflags +faststart` matters: it lets the video start playing before it fully
downloads. `-pix_fmt yuv420p` guarantees playback on phones and web.

## Final verification (mandatory before telling the user it's done)

1. `ffprobe` the export: duration matches the final cut, resolution and fps as intended, file size sane.
2. Extract 3 preview frames across the timeline and look at them.
3. Report to the user: path, duration, resolution, size — and offer the next platform preset if they need more than one.
