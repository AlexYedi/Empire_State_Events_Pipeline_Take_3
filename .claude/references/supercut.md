# Supercut — the recording + transcript source

**Status (2026-09-28):** Supercut Pro (1-year plan) replaces the OBS capture lane (retired, see the
tombstone in `platform-constraints.md`). Consumer: `/post-event-content` Step 2A. Env var: `SUPERCUT_API`
in the repo `.env` (a **personal** token, `sk_u_…`). Never print it.

## Two surfaces, one backend

| | MCP | REST |
|---|---|---|
| Endpoint | `https://mcp.supercut.ai/mcp` (remote HTTP only) | `https://api.supercut.ai/v1` |
| Auth | OAuth (browser sign-in, DCR + PKCE). No token to paste | `Authorization: Bearer $SUPERCUT_API` |
| Tools / endpoints | `list_recordings` · `get_recording` · `get_transcript` · `get_frame` · `list_comments` · `list_reactions` · `list_playlists` · `get_playlist` · `list_playlist_recordings` · `add_playlist_recording` · `list_form_responses` | see below |
| Use when | interactive runs in the parent thread (default) | MCP not loaded in this session, or a script needs it |

**MCP first, REST fallback.** Like every claude.ai / MCP connector, the Supercut MCP is **not available
inside subagents**, so call it from the parent thread. A connector added mid-session is not visible until
Claude Code restarts. Tool names in-session will be prefixed (e.g. `mcp__supercut__get_transcript` or
`mcp__claude_ai_Supercut__…`); run ToolSearch `supercut` to find them.

## REST endpoints we use (from the official OpenAPI spec)

Docs: https://api.supercut.ai/api/platform/v1/docs/ (spec at `…/docs/openapi.json`).

| Call | Returns |
|---|---|
| `GET /recordings?limit=N&list=owned\|watched\|shared&search=…&cursor=…` | `data.items[]`: `public_id`, `title`, `created_at`, `duration_ms`; `data.next_cursor`. `search` works for `list=owned` only. Max `limit` 50 |
| `GET /recordings/search?q=…` | semantic + keyword match over titles and AI summaries, best first; `data.results[]` with `public_id`, `title`, `created_at`, `snippet`. An empty page with a non-null `next_cursor` is **not** the end |
| `GET /recordings/{id}` | metadata + `status` (`pending`/`processing`/`completed`/`failed`) + AI `summary` + `chapters[]` (`title`, `summary`, `start_ms`) |
| `GET /recordings/{id}/transcript` | `data.status`. When `completed`: `language`, `duration_ms`, `sentences[]` of `{text, start, end}`. Otherwise `pending`/`processing` (retry later) or `failed`/`unavailable` (final; e.g. no audio) |
| `GET /recordings/{id}/assets/aligned-transcription` | short-lived signed URL to `aligned_transcription.json` (word-level, force-aligned) |
| `GET /recordings/{id}/assets/system-audio` · `…/microphone-audio?variant=original\|normalised\|denoised` | short-lived signed URL to the raw audio track |
| `GET /recordings/{id}/frame?time_ms=…` | signed URL to a frame image (slide capture without phone photos) |

Raw assets (`/assets/*`) need a personal token, edit access or ownership, and the plan's raw-asset
download feature. Errors are `{error: true, code, message}` with 400/401/402/403/404/409/429/500.

## How the pipeline uses it

1. Find the recording: MCP `list_recordings`, or REST `/recordings/search?q=<event name>`. Match on
   title + `created_at` against the Notion Event Date. If more than one matches, ask Alex.
2. Fetch the transcript (MCP `get_transcript` or REST `/transcript`) → write it to
   `event-transcripts/YYYY-MM-DD_<Event>.md` → Step 3.5 transcript-conditioning runs unchanged.
3. **When quotes will be attributed to named speakers**, the REST transcript has **no speaker labels**
   (sentences only). Download the audio asset (system audio for a webinar, microphone for an in-room
   recording) and run `/ingest-recording` on it: ElevenLabs Scribe diarizes it and seeds roster keyterms.
   Supercut's own transcript then serves as a cross-check.

## Gotchas

- **Cloudflare blocks Python's default user agent** (HTTP 403, "Error 1010: Access denied", before the API
  sees the request). Use `curl`, or set a `User-Agent` header in scripts.
- `list` defaults to owned recordings; recordings shared with Alex need `list=shared`.
- Signed asset URLs expire (`expires_in`), so download right away.
- The REST API sends no CORS headers: server-side or CLI calls only.
- "Stacks" were renamed "Playlists" in the app and MCP. REST keeps the `/stacks` paths.

## Verified on a live recording (2026-09-28, 32 s test, camera + mic, MCP)

| Item | Result |
|---|---|
| MCP tool names | Prefix `mcp__claude_ai_Supercut__`, **hyphenated** (`get-transcript`, `get-recording`, `list-recordings`, `search-recordings`, `get-frame`). The MCP has more than the table above: `get-recording-assets` (manifest of every raw asset + status), `get-microphone-audio` / `get-system-audio`, `get-aligned-transcription`, `download-recording` (rendered video), `download-recording-camera` / `-screen` (raw MP4), `get-mouse-events` / `get-keyboard-events`, `get-recording-analytics`, `list-workspace-members`. So the MCP covers everything; REST is only a fallback |
| Transcript shape | `sentences[]` of `{text, start, end}`, **no speaker labels** (MCP and REST alike) |
| Transcript time units | **seconds** (float, e.g. `1.3145`). Chapters, frames and reactions use **ms**, so multiply by 1000 before `get-frame` |
| AI summary + chapters | Summary present. `chapters[]` was empty on a 32 s clip; expect it on real-length recordings |
| Word-level transcript | `aligned_transcription.json` = `{words: [{word, start, end}]}`, seconds, same text as the sentences |
| Raw-asset download on Pro | **Yes.** Mic audio = `.m4a`, AAC, 48 kHz mono. Signed URLs expire in 900 s (audio, JSON) / 3600 s (video) |
| System audio | `unavailable` unless system-audio capture is on. **Turn it on for webinars**: it is the clean track for `/ingest-recording` |
| Video | Raw camera MP4 merged in about 1 min (first call returns `preparing`, poll). Rendered video and raw screen are also async |
| Frames | `get-frame` returns a 1280×720 JPEG. `source` = `screen` (default) / `camera` / `screen_and_camera` |
| Mouse / keyboard | Only captured when screen recording is on; `unavailable` otherwise |
| Accuracy | Clean for conversational speech; one mishearing in 32 s ("Google one" for "one"). Proper nouns are untested; that is what `/ingest-recording` keyterms are for |

**What this means for `/post-event-content`:** Supercut alone gives the transcript, timestamps, summary, chapters, slide frames (from screen or camera) and the audio. **Speaker attribution still needs `/ingest-recording`** on the downloaded audio (mic for in-room, system for webinars): Supercut's transcript has no diarization.
