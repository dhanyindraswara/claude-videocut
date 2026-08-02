---
name: edit-ops
description: Core timeline operations with ffmpeg — trim, split, join/concat clips, speed up or slow down, crop 16:9 to vertical 9:16, resize, rotate, image/logo overlay, text titles, fade and crossfade transitions. Use for any structural video edit that is not transcript-driven.
---

# Edit Ops (ffmpeg recipes)

Invoke `videocut-basics` first. Outputs go to `work/`, re-encode defaults:
`-c:v libx264 -crf 18 -preset medium -c:a aac -b:a 192k` (shortened to `[ENC]` below).

## Trim
```bash
ffmpeg -y -ss 00:00:12.5 -to 00:01:03.0 -i in.mp4 [ENC] work/trim_v1.mp4
```
(`-ss` before `-i` = fast seek; accurate to the frame once re-encoding.)

## Join clips
Same codec/resolution/framerate — lossless concat:
```bash
printf "file '%s'\n" clip1.mp4 clip2.mp4 > work/list.txt
ffmpeg -y -f concat -safe 0 -i work/list.txt -c copy work/joined_v1.mp4
```
Different sizes/codecs — normalize through a filter:
```bash
ffmpeg -y -i a.mp4 -i b.mp4 -filter_complex \
 "[0:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:-1:-1,fps=30,setsar=1[v0];
  [1:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:-1:-1,fps=30,setsar=1[v1];
  [v0][0:a][v1][1:a]concat=n=2:v=1:a=1[v][a]" -map "[v]" -map "[a]" [ENC] work/joined_v1.mp4
```

## Speed
```bash
# 1.5x (atempo valid 0.5–2.0; chain atempo twice for more)
ffmpeg -y -i in.mp4 -vf "setpts=PTS/1.5" -af "atempo=1.5" [ENC] work/fast_v1.mp4
```

## Vertical 9:16 (Reels/TikTok/Shorts)
```bash
# center-crop; shift the crop x-offset to keep the speaker framed
ffmpeg -y -i in.mp4 -vf "crop=ih*9/16:ih,scale=1080:1920" [ENC] work/vertical_v1.mp4
# or blurred-background pillarbox (keeps full frame visible):
ffmpeg -y -i in.mp4 -filter_complex \
 "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20[bg];
  [0:v]scale=1080:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2" [ENC] work/vertical_v1.mp4
```

## Logo / image overlay
```bash
ffmpeg -y -i in.mp4 -i logo.png -filter_complex \
 "[1:v]scale=180:-1[lg];[0:v][lg]overlay=W-w-24:24" [ENC] work/logo_v1.mp4
```
Timed overlay: append `:enable='between(t,3,10)'`.

## Title text
```bash
ffmpeg -y -i in.mp4 -vf "drawtext=text='Judul Video':fontsize=64:fontcolor=white:borderw=3:bordercolor=black:x=(w-text_w)/2:y=h*0.12:enable='between(t,0,4)'" [ENC] work/title_v1.mp4
```
For fonts: `fontfile=/path/to/font.ttf`. Find fonts with `fc-list | head`.

## Transitions
```bash
# fade in/out on one clip (video+audio)
ffmpeg -y -i in.mp4 -vf "fade=t=in:d=0.5,fade=t=out:st=DUR-0.5:d=0.5" \
  -af "afade=t=in:d=0.5,afade=t=out:st=DUR-0.5:d=0.5" [ENC] work/fade_v1.mp4
# crossfade between two clips (offset = clipA duration - fade duration)
ffmpeg -y -i a.mp4 -i b.mp4 -filter_complex \
 "[0:v][1:v]xfade=transition=fade:duration=0.7:offset=OFFSET[v];
  [0:a][1:a]acrossfade=d=0.7[a]" -map "[v]" -map "[a]" [ENC] work/xfade_v1.mp4
```
`xfade` transitions worth knowing: `fade, wipeleft, slideleft, circleopen, pixelize`.

Get durations with `ffprobe -v error -show_entries format=duration -of csv=p=0 file.mp4`.
Always verify per `videocut-basics` after each op.
