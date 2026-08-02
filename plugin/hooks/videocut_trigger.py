#!/usr/bin/env python3
"""UserPromptSubmit hook: turn a casual opener into a real VideoCut start.

Description-based skill triggering is advisory — for a short conversational
prompt like "bro kerja edit video" the model will often just answer instead of
loading the skill. This hook makes the common openers deterministic by
injecting an explicit instruction alongside the user's message.
"""

import json
import re
import sys

# Openers that mean "start editing a video", Indonesian and English.
# Each must mention the medium (video/klip/footage) so unrelated prompts
# like "edit this file" never match.
TRIGGERS = [
    # bro / gas / ayo / tolong / mau / pengen ... edit|potong|garap video
    r"\b(bro|sis|gas|ayo|yuk|tolong|mau|pengen|pengin|kerja)\b[\w\s]{0,20}?"
    r"\b(edit|potong|garap|olah|cut)\w*\s+(video|klip|footage)\b",
    # bare verb-first openers: "edit video", "potong video", "cut video"
    r"^\s*(edit|potong|garap|olah|cut|trim)\w*\s+(video|klip|footage)\b",
    # english
    r"\b(let'?s|lets|help me|i want to|wanna)\s+edit\s+(a\s+|my\s+|this\s+)?video\b",
    r"^\s*edit\s+(my|this|the)\s+video\b",
    # caption / subtitle openers
    r"^\s*(bikin|buat|tambah|add)\s+(caption|subtitle|takarir)\w*\b",
    # explicit product name
    r"\bvideocut\b",
]

INSTRUCTION = (
    "[VideoCut] The user is opening a video-editing session. "
    "Invoke the `videocut-basics` skill now, before replying, and follow its "
    "section 0 (Cold start): run the dependency check, report readiness in one "
    "line, then ask for the video and what they want done using the numbered "
    "presets. If the user already named a file or an edit in this message, skip "
    "the questions it already answers. Reply in the user's language."
)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # never block a prompt on a parse failure

    prompt = (payload.get("prompt") or "").lower()
    if not any(re.search(p, prompt) for p in TRIGGERS):
        return 0

    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": INSTRUCTION,
            }
        },
        sys.stdout,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
