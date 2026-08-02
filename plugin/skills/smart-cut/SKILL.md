---
name: smart-cut
description: Transcript-driven editing — remove filler words (um, uh, eh, anu), long silences and dead air, repeated takes, or any spoken section the user names ("cut the part where I talk about pricing"). The core talking-head cleanup tool. Requires a transcript from the transcribe skill.
---

# Smart Cut

Invoke `videocut-basics` first. Requires `work/<name>.transcript.json` (run `transcribe` if missing).

## 1. Generate a plan (never render blind)

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/smart_cut.py" plan work/video.transcript.json \
  -o work/edit_plan.json --max-pause 0.8 --pad 0.10 --lang id
```

- `--max-pause` — silence longer than this (seconds) gets tightened. 0.8 is natural; 0.4 is punchy/social-media pace.
- `--lang id|en|both` — which built-in filler list to use. `--fillers "anu,gitu"` adds custom words.
- `--no-fillers` — keep fillers, only tighten silences.

The command prints a summary: fillers removed, pauses tightened, time saved.

## 2. Review with the user

Show the summary and any borderline cuts. For content cuts ("remove the pricing part"),
find the words in the transcript JSON and edit `edit_plan.json` segments yourself —
it's just start/end/label JSON. Merge or reinstate segments as the user directs.

## 3. Apply

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/smart_cut.py" apply work/edit_plan.json \
  -i source/video.mp4 -o work/cut_v1.mp4
```

Re-encodes with clean joins (libx264 CRF 18 + AAC). Then verify per `videocut-basics`
(ffprobe duration ≈ plan total, preview frames, spot-check a join by exporting
2 s around it).

## Tips

- Cutting mid-word sounds terrible — the planner already pads word boundaries;
  keep `--pad ≥ 0.08` unless the user asks for jump-cut style.
- Repeated takes: find near-duplicate sentences in the transcript, keep the last take
  (usually the best), and drop earlier ones from the plan.
- After a big cut, captions must be regenerated from the cut video (re-transcribe
  the cut output) — old timestamps no longer match.
