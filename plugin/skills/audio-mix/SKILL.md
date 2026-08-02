---
name: audio-mix
description: Audio work with ffmpeg — add background music, auto-duck music under speech, loop or trim music to video length, normalize loudness for social platforms, replace or extract audio, denoise. Use when the user mentions music, backsound, BGM, audio levels, volume, or noise.
---

# Audio Mix

Invoke `videocut-basics` first. `[ENC]` = `-c:v copy -c:a aac -b:a 192k`
(video is untouched by audio-only ops — copy it).

## Add background music with auto-ducking (music dips when someone speaks)
```bash
ffmpeg -y -i video.mp4 -stream_loop -1 -i music.mp3 -filter_complex \
 "[1:a]volume=0.9[m];
  [m][0:a]sidechaincompress=threshold=0.05:ratio=8:attack=50:release=400[duck];
  [0:a][duck]amix=inputs=2:duration=first:normalize=0[a]" \
 -map 0:v -map "[a]" -shortest [ENC] work/music_v1.mp4
```
Tune: music too loud → lower `volume=`; ducking too aggressive → lower `ratio` to 4.

## Music without ducking (b-roll, no speech)
```bash
ffmpeg -y -i video.mp4 -stream_loop -1 -i music.mp3 -filter_complex \
 "[1:a]volume=0.25,afade=t=in:d=1[m]" -map 0:v -map "[m]" -shortest [ENC] work/music_v1.mp4
```

## Normalize loudness (do this on every final export; -14 LUFS = YouTube/Spotify standard)
```bash
ffmpeg -y -i in.mp4 -af "loudnorm=I=-14:TP=-1.5:LRA=11" [ENC] work/norm_v1.mp4
```

## Replace / extract audio
```bash
ffmpeg -y -i video.mp4 -i voiceover.wav -map 0:v -map 1:a -shortest [ENC] work/dub_v1.mp4
ffmpeg -y -i video.mp4 -vn -c:a libmp3lame -q:a 2 work/audio.mp3
```

## Quick denoise / hum removal
```bash
ffmpeg -y -i in.mp4 -af "highpass=f=80,afftdn=nf=-25" [ENC] work/denoise_v1.mp4
```

## Free music sources (tell the user; never claim rights you can't verify)
- YouTube Audio Library (free, attribution rules per track)
- Pixabay Music / Free Music Archive (check each license)
- Or generate a simple bed with ffmpeg tones only as a placeholder.

Verify by listening: export a 10 s sample (`-t 10`) around a speech section and let
the user check the speech/music balance before rendering the whole video.
