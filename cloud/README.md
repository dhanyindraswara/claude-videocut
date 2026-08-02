# Run VideoCut entirely in Claude Code on the web

No laptop setup, no local ffmpeg. Configure the cloud environment once and every
future chat session starts ready to edit — attach a video and go.

Cloud sessions run on an Ubuntu VM with 4 vCPU, 16 GB RAM and 30 GB disk, behind
a proxy that only allows the domains your environment permits. Out of the box
`ffmpeg` is **not** installed and `huggingface.co` is **not** reachable, which is
why the two steps below exist.

## 1. Allow the Whisper model host

Whisper models are downloaded from Hugging Face. Under the default **Trusted**
network level that host is blocked, so transcription, smart-cut, and automatic
captions cannot work.

At [claude.ai/code](https://claude.ai/code): open the environment selector (the
cloud icon above the message box) → settings icon on your environment →
**Network access** → **Custom**, and add:

```
huggingface.co
*.huggingface.co
*.hf.co
```

Tick **Also include default list of common package managers** — the setup script
needs PyPI and the Ubuntu archive, which live on that default list.

Model files are served from `cdn-lfs*.huggingface.co`, so the `*.huggingface.co`
wildcard is required, not optional — allowing the bare domain alone gets you a
metadata request that succeeds and a download that fails.

## 2. Add the setup script

Paste this into the **Setup script** field of the same dialog — three lines,
which matters if you are doing this on a phone:

```bash
#!/bin/bash
curl -fsSL https://raw.githubusercontent.com/dhanyindraswara/claude-videocut/main/cloud/setup.sh | bash || true
exit 0
```

`raw.githubusercontent.com` is on the default Trusted allowlist, so this fetch
works regardless of your custom domain list. It pulls [`setup.sh`](./setup.sh),
which installs `ffmpeg`, installs `faster-whisper`, and pre-downloads the model.
Paste the full file instead if you would rather pin the contents than track
`main`.

The result is snapshotted and cached, so the script runs *once* — later sessions
start with everything already on disk. The cache rebuilds when you change the
script or the allowed domains, and expires after about seven days.

Keep it under the ~5 minute setup budget: `small` (~460 MB) is the default and
fits comfortably. To use a different size, add `VIDEOCUT_WHISPER_MODEL=base` (or
`medium`, `large-v3`) to the environment's **Environment variables**.

## 3. Use it

Start a session and say:

> bro kerja edit video

then attach the video. Renders come back as files in the chat.

## Verifying it worked

Ask Claude to run:

```bash
ffmpeg -version | head -1
python3 -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8'); print('model OK')"
```

`model OK` means step 1 worked. A `ProxyError: 403 Forbidden` means the domain
allowlist did not take effect — re-check the wildcard entry, and note that
environment changes apply to **new** sessions, not the one you are sitting in.

## What still differs from running locally

- **Sessions are ephemeral.** The VM is reclaimed after inactivity. Anything you
  want to keep must be downloaded from the chat or committed and pushed.
- **Uploads are the bottleneck**, not the render. Long 4K source files are
  painful to get in and out; trim before uploading when you can.
- **No GPU.** Transcription runs on CPU (int8), so allow roughly real-time for
  `small` on a long recording. `ffmpeg` operations are unaffected.
