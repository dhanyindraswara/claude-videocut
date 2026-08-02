---
name: motion-graphics
description: CapCut-style motion graphics with ffmpeg + libass — animated titles, punch-in jump cuts, white-flash transitions, xfade transitions, progress bars, speed ramps, sliding lower-thirds. Use when the user asks for motion graphics, animated text, transitions, jump cuts, "biar rame", "kasih efek", or a full auto-edit of a raw clip.
---

# Motion Graphics

Everything here is ffmpeg + libass — no external apps. Combine freely with the
captions and smart-cut skills. Verify every render with extracted frames
(videocut-basics §4) before calling it done.

## The full-auto recipe (raw clip in → edited clip out)

For "edit semuanya" requests, the proven single-pass stack, in filter order:

1. `fps=60,scale=1080:-2:flags=lanczos,crop=1080:1920` — normalize geometry first
2. **Punch-in jump cuts** (zoompan, below) at transcript segment boundaries
3. **White flash** (eq, below) at the same boundaries
4. `ass=captions.ass` then `ass=title.ass` — word-pop captions, then title layer
5. **Progress bar** overlay
6. `fade=t=out` + loudnorm two-pass on audio

Pick boundaries from the transcript JSON (segment starts), not by eye.

## Animated titles (ASS, second `ass=` filter)

Write a separate `title.ass` with `PlayResX/Y` matching the output exactly
(e.g. 1080/1920) so coordinates are pixel-true. Key tags:

- Pop-in: `{\fad(120,250)\fscx0\fscy0\t(0,260,\fscx112\fscy112)\t(260,380,\fscx100\fscy100)}TEXT`
- Slide-up: `{\fad(220,250)\move(540,560,540,528,0,320)}TEXT`
- Use fonts from `fc-list` (cloud VMs have DejaVu Sans, no Arial Black).
  Skip emoji in ASS — libass renders them unreliably.

## Punch-in jump cuts (no time removed → captions stay in sync)

Alternate zoom level per speech segment. Frame numbers = seconds × fps:

```
zoompan=z='if(lt(on,366),1.0,if(lt(on,603),1.10,1.0))':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':d=1:s=1080x1920:fps=60
```

1.08–1.12 reads as an intentional cut; more looks like a mistake. Because the
timeline length is unchanged, caption/audio sync is untouched — this is why
punch-ins are the default "cut" for talking-head edits.

## White-flash transition (also timeline-neutral)

Brightness spike decaying over ~0.18 s at each boundary:

```
eq=eval=frame:brightness='if(between(t,6.10,6.28),(6.28-t)*2.2,0)'
```

Chain more `if(between(...))` clauses for more cut points.

## Progress bar

`drawbox` can't animate, so overlay a sliding color strip:

```
color=c=0xFF453A@0.85:s=1080x12:r=60[bar];
[v][bar]overlay=x='-W+W*(t/DURATION)':y=H-12:shortest=1
```

## Real transitions between separate clips (xfade)

When joining clips (not one continuous take): `xfade=transition=slideleft`
(`fade`, `wipeleft`, `circleopen`, `smoothup`…) + `acrossfade` for audio.
**Warning:** each xfade eats `duration` seconds of timeline — regenerate
captions from a retimed transcript afterwards, or burn captions per-clip
before joining.

## Speed ramps

```
[0:v]setpts=0.5*PTS[v];[0:a]atempo=2.0[a]     # 2× section
```

Split → ramp the boring middle → concat. `atempo` accepts 0.5–100; chain two
`atempo` for extremes. Same caption-retiming warning as xfade.

## Lower-third / sticker text

Prefer ASS `\move` + `\fad` over drawtext — smoother, styled, one file. Use
drawtext only for values computed at render time (counters, timestamps).
