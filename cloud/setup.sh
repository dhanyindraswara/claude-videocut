#!/bin/bash
# VideoCut — setup script for a Claude Code cloud environment.
#
# Paste this into the "Setup script" field of your cloud environment at
# claude.ai/code (environment selector → settings icon → Setup script).
#
# It runs once as root before Claude starts, and the resulting filesystem is
# snapshotted and cached, so every later session begins with ffmpeg, Whisper,
# and the model already on disk — nothing to install mid-chat.
#
# Requires Network access = Custom with huggingface.co allowed; see cloud/README.md.
# Every step is guarded with `|| true`: a non-zero exit here blocks the session
# from starting at all, and a missing Whisper model should degrade to
# "no transcription", not "no session".

set -u

# --- render engine: ffmpeg + ffprobe ------------------------------------------
apt-get update -qq || true
apt-get install -y --no-install-recommends ffmpeg || true

# --- the ear: faster-whisper --------------------------------------------------
pip install --quiet --no-input faster-whisper || true

# --- pre-cache the Whisper model ---------------------------------------------
# Downloading here (not on first use) is the whole point: it lands in the
# environment snapshot, so no session ever pays for it or needs the network.
# "small" is the quality/speed sweet spot for Indonesian talking-head audio;
# set VIDEOCUT_WHISPER_MODEL in the environment variables to override.
MODEL="${VIDEOCUT_WHISPER_MODEL:-small}"
python3 - "$MODEL" <<'PY' || true
import sys
try:
    from faster_whisper import WhisperModel
    name = sys.argv[1]
    WhisperModel(name, device="cpu", compute_type="int8")
    print(f"[videocut] whisper model '{name}' cached")
except Exception as exc:
    # Almost always a blocked huggingface.co — report, never fail the session.
    print(f"[videocut] model pre-cache skipped: {type(exc).__name__}: {exc}")
    print("[videocut] add huggingface.co to the environment's allowed domains")
PY

# --- report what the session actually got ------------------------------------
echo "[videocut] ffmpeg:  $(ffmpeg -version 2>/dev/null | head -1 || echo 'MISSING')"
echo "[videocut] python:  $(python3 --version 2>/dev/null || echo 'MISSING')"
python3 -c "import faster_whisper; print('[videocut] faster-whisper:', faster_whisper.__version__)" 2>/dev/null \
  || echo "[videocut] faster-whisper: MISSING"

exit 0
