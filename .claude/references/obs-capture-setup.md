# OBS Capture Setup — the recording lane for `/post-event-content`

**Status:** spec (recording lane). Branch `feat/obs-capture`. Supersedes Granola (dead) and Clarify
(rejected 2026-09-09 — see memory `project_crm_capture_decision_2026-09-09`). Capture engine =
**OBS Studio (local recording) → ElevenLabs Scribe v2 + ffmpeg slide extraction**.

---

## Why the recording setup is decided first (concept)

Everything downstream inherits the quality of the raw recording. The ETL cannot recover audio a bad
mic config never captured, and OCR cannot read slide text that was captured at too low a resolution.
The whole reason we left Clarify is that its API gave us only a *paraphrased summary* — no raw
recording — so the value was pre-flattened. OBS gives us the full raw signal; this doc makes sure
that signal is **clean, complete, and split the way the ETL wants it** before a single line of ETL
code is written. Two design principles drive every field below:

1. **Separate the streams at capture time.** Speaker audio (→ transcription), your mic (→ your own
   questions), and the video (→ slides) are three different downstream jobs. Capturing them on
   separate tracks now is free; un-mixing them later is impossible. This is why we record
   **multi-track audio**, not one flattened mix.
2. **Record for the machine, not just the human.** A crash-safe container, a legible resolution for
   OCR, and a date-parseable filename matter more than a pretty picture.

---

## Machine baseline (verified 2026-09-10)

- macOS **26.6.2** → **ScreenCaptureKit** available: OBS captures webinar video **and** app audio
  natively. **BlackHole / virtual audio driver NOT needed** (and not installed).
- OBS **32.2.2** at `/Applications/OBS.app` → **Hybrid MP4** format available (crash-safe + multi-track).
- **ffmpeg** at `/opt/homebrew/bin/ffmpeg` → ETL audio-split + keyframe extraction tool present.
- Display: Built-in Liquid Retina XDR, working resolution ~1920×1080.

---

## Part 1 — One-time OBS configuration

Do this once. Every field value is given explicitly; where a field isn't named, leave it at its
current value.

### 1.1 Grant macOS permissions (do this first or capture is silently blank)
1. Open **System Settings → Privacy & Security → Screen & System Audio Recording**.
   - Toggle **OBS = ON**. (This one permission covers both the screen video and the app audio under
     ScreenCaptureKit.)
2. Open **System Settings → Privacy & Security → Microphone**.
   - Toggle **OBS = ON**.
3. **Quit and reopen OBS** after granting (permissions only take effect on relaunch).

### 1.2 Video settings — `OBS → Settings → Video`
- **Base (Canvas) Resolution:** `1920x1080`
- **Output (Scaled) Resolution:** `1920x1080`  *(no rescale — keeps slide text crisp for OCR)*
- **Downscale Filter:** `Bicubic`
- **Common FPS Values:** `30`
  - *Rationale:* slides are static, but 30 fps keeps A/V sync clean and captures any in-webinar demo
    video. If storage becomes an issue, `15` is acceptable for slide-only sessions.

> **If slide text ever looks marginal after OCR:** raise Base + Output to `3024x1964` (native panel)
> for that session. Default stays 1080p for file-size sanity.

### 1.3 Output settings — `OBS → Settings → Output`
- **Output Mode:** `Advanced` (top of the panel — switch from Simple).
- Go to the **Recording** tab:
  - **Type:** `Standard`
  - **Recording Path:** `/Users/sameoldexpressions/Documents/GitHub/Empire_State_Events_Pipeline_Take_3/event-transcripts/_obs-inbox`
    *(create this folder — see 1.7. Point at the MAIN checkout, not this worktree, so the ETL always
    reads from one canonical inbox.)*
  - **Recording Format:** `Hybrid MP4`  *(crash-safe like MKV, plays anywhere, supports multi-track —
    no remux step needed)*
  - **Audio Track:** check **Track 1, Track 2, and Track 3** (this enables multi-track recording)
  - **Video Encoder:** `Apple VT H264 Hardware Encoder`  *(hardware = low CPU, so recording never
    lags the live webinar)*
  - **Audio Encoder:** `AAC` (default)
  - Under the video encoder settings:
    - **Rate Control:** `CBR`
    - **Bitrate:** `10000` Kbps  *(generous for 1080p30 — do not starve it; slide text legibility
      depends on it)*
    - **Keyframe Interval:** `2` s
    - **Profile:** `high`

### 1.4 Audio settings — `OBS → Settings → Audio`
- **Sample Rate:** `48 kHz`
- **Channels:** `Stereo`
- Under **Global Audio Devices**:
  - **Desktop Audio:** `Disabled`  *(we capture app audio via the Screen Capture SOURCE in 1.5, which
    is cleaner and per-app — leave the global desktop device off to avoid double-capture)*
  - **Mic/Auxiliary Audio:** select your input (**MacBook Pro Microphone**, or your headset/USB mic if
    you use one).
- Go to the **Recording** tab (per-track audio bitrate):
  - **Track 1:** `256` Kbps
  - **Track 2:** `256` Kbps
  - **Track 3:** `256` Kbps

### 1.5 Scene + sources — the OBS main window
1. In the **Scenes** box (bottom-left), click **+** → name it `Webinar Capture`.
2. In the **Sources** box, click **+** → **macOS Screen Capture** → name it `Webinar Video+Audio` → OK.
   - **Method:** `Application`  *(captures one app's video + audio only — no desktop clutter, no
     notification pings). Pick the app your webinars run in (e.g. **Google Chrome**, or **zoom.us**).*
     - *If your webinar app varies or Application capture misbehaves, switch Method to* `Display` *and
       select the display the webinar is on. Robust, but capture the whole screen — keep other windows off it.*
   - **Capture Audio:** `ON` (checkbox in the source properties — this is what routes speaker audio
     into OBS via ScreenCaptureKit).
3. Your **Mic** already appears in the Audio Mixer from 1.4. That's all the sources you need.

### 1.6 Assign sources to tracks — Audio Mixer → Advanced Audio Properties
This is the step that makes the ETL clean. In the **Audio Mixer** panel, click the **⋮ (three dots) →
Advanced Audio Properties**. For each source, set the **Tracks** checkboxes:

| Source | Track 1 | Track 2 | Track 3 | Purpose |
|---|---|---|---|---|
| **Webinar Video+Audio** (speakers) | ✅ | ✅ | ⬜ | T2 = clean speaker-only → **Scribe transcribes this** |
| **Mic/Aux** (you) | ✅ | ⬜ | ✅ | T3 = your questions, kept separate |

- **Track 1** = safety composite (everything mixed) — the fallback if a track is ever misconfigured.
- **Track 2** = speakers only — the transcription source. Keeping your mic OFF T2 means Scribe's
  diarization never confuses you with a panelist.
- **Track 3** = your mic only — preserved so the ETL can optionally fold your questions in, but never
  pollutes the speaker transcript by default.

### 1.7 Filename + inbox folder (the ETL handoff)
1. Create the inbox once:
   `mkdir -p "/Users/sameoldexpressions/Documents/GitHub/Empire_State_Events_Pipeline_Take_3/event-transcripts/_obs-inbox"`
2. `OBS → Settings → Advanced → Recording → Filename Formatting:`
   `%CCYY-%MM-%DD_%hh-%mm-%ss_webinar`
   - *Produces e.g. `2026-09-15_18-04-22_webinar.mp4` — date is parseable, so the ETL resolves the
     event by date (matching `/post-event-content`'s existing date+title resolution), then you confirm.*
3. **Overwrite if file exists:** leave **OFF**.

---

## Part 2 — Per-webinar capture routine (the discipline)

1. **Before the webinar starts:** open OBS, confirm the `Webinar Capture` scene is selected, click
   **Start Recording**. Record the intro / title slide — speaker names + company on that first slide
   are gold for the Scribe **keyterms seed** (the YED-95 pattern that hit 100% entity accuracy).
2. **Keep the webinar app stable.** If using `Application` capture you can multitask; if using
   `Display` capture, don't drag other windows over it.
3. **Jot speaker names/companies** as they're introduced (a note, or say them near your mic). These
   seed the keyterms list the ETL feeds Scribe.
4. **At the end:** click **Stop Recording.** The `.mp4` lands in `_obs-inbox/`.
5. Hand off to the ETL (next build): it will transcribe T2, extract slides from the video, OCR them,
   and file the outputs into `event-transcripts/YYYY-MM-DD_Event-Name.*` for `/post-event-content`.

---

## Part 3 — Output contract (what the ETL will receive)

The ETL (built next) can rely on every recording being:

- **Container:** Hybrid MP4, `_obs-inbox/YYYY-MM-DD_HH-MM-SS_webinar.mp4`
- **Video:** H.264, 1920×1080, 30 fps → `ffmpeg` scene-change keyframe extraction → slide images → OCR
- **Audio Track 2:** speaker-only, 48 kHz AAC → ElevenLabs Scribe v2 (diarized, keyterm-seeded)
- **Audio Track 3:** Alex-mic-only → optional fold-in of your questions
- **Audio Track 1:** full mix → fallback only
- ffmpeg maps a track by index, e.g. `ffmpeg -i in.mp4 -map 0:a:1 speakers.wav` (0:a:1 = 2nd audio
  track = Track 2).

---

## Closing note (concept)

The payoff of this setup is that the ETL becomes *deterministic*: it always knows which track is the
speakers, which is you, and where the file lives — so it can run unattended. The one manual judgment
we keep is event resolution (which recording = which event), because a wrong mapping corrupts the
knowledge graph, and that's cheap for you to confirm and expensive to get wrong. Everything else —
splitting audio, transcribing, extracting slides, OCR, filing — is machine work, which is exactly the
"extract the granular value, don't flatten it" requirement that killed the Clarify summary-only path.

**Next build after this:** ~~the ETL script~~ **BUILT** — `.claude/tools/obs_ingest.py`
(`_obs-inbox/*.mp4` → speaker-track audio → Scribe v2 diarized transcript + ffmpeg slide extraction
+ tesseract OCR → `event-transcripts/<slug>/`). Generalizes the one-off `.claude/evals/run_scribe.py`.

---

## Pre-mortem — how this lane fails, and the guard (adversarial pass)

| Failure | Symptom | Guard |
|---|---|---|
| **Permissions not granted** | Recording is a black screen / silent | 1.1 is step ONE; the ETL's ffprobe will show 0 video or 0 speaker audio — verify the first recording before trusting the lane. |
| **Wrong track fed to Scribe** | Transcript includes Alex's questions as a "speaker", diarization confused | ETL defaults `--speaker-track 1` (OBS Track 2 = speakers only). If a recording was single-track, ETL auto-falls-back to track 0 and prints a warning. |
| **App-capture grabs no audio** | Silent recording despite webinar playing | ScreenCaptureKit audio needs the Screen Recording permission AND "Capture Audio" ON in the source. Display-capture fallback captures system-wide audio. |
| **Slide text unreadable by OCR** | `slides (OCR).md` full of `(no text detected)` | Bump capture to native res (1.2 note); OCR is explicitly flagged "verify against video" — it's a lead, not ground truth. |
| **Accidental paid transcription** | Surprise ElevenLabs spend | ETL gates the paid step behind an interactive `y/N` (or explicit `--yes`); refuses to spend non-interactively without `--yes`. |
| **OBS overwrites this config** | Settings revert | The applied config is snapshotted to `.claude/references/obs-config/` — restore by copying `basic.ini` + `recordEncoder.json` back to `~/Library/Application Support/obs-studio/basic/profiles/Untitled/` while OBS is quit. |

## Config snapshot / restore
`.claude/references/obs-config/` holds the applied `basic.ini` + `recordEncoder.json` (the profile is
the default **"Untitled"** — rename in-app via Profile → Rename if you want a friendlier label; do the
rename in the GUI so OBS updates its own bookkeeping). To restore after a bad edit: quit OBS, copy both
files back into `~/Library/Application Support/obs-studio/basic/profiles/Untitled/`, relaunch.
