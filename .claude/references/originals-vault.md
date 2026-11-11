# Originals vault (Google Drive) — runbook

YED-384 · design YED-390 (Alex, 2026-11-11) · script `.claude/scripts/vault.py` (`--selftest` for the offline proof).

The knowledge graph mines originals: emails, transcripts, meeting notes, Notion comments. The originals themselves never enter git or the graph. They live in an owner-only Google Drive folder, **Graph Originals**. The graph holds one pointer row per original.

## What goes in

Any raw source the graph mines and might need to re-mine later. `--kind` is one of `email`, `transcript`, `meeting_note`, `notion_comment`, `other`. Off-the-record material is still redacted per CLAUDE.md §4.4 before any *derived* file is written; the vault keeps the untouched original privately.

## Local layout (outside every git work tree)

```
~/GraphOriginals/
  vault.json        {"drive_folder_id": "..."}   (the folder id is never in the repo)
  staging/<sha>.<ext>   copies waiting for upload
  pending.jsonl     prepared, not yet uploaded
  index.jsonl       sha · kind · date · ext · bytes · Drive file id
  manifests/<sha>.json  documents-row manifests
  work/<sha>.<ext>  re-mining downloads
```

`vault.py` refuses to write if any of these resolve inside a git work tree. It checks four layers: realpath, a `.git` ancestor walk, `git rev-parse` with `GIT_*` env stripped, and a casefold prefix match against the sibling checkouts. Original filenames are never stored, because they often carry subjects or names.

## Upload flow (the parent session does Drive I/O)

1. `python3 .claude/scripts/vault.py prepare <file>... --kind email [--date YYYY-MM-DD] [--event-id <uuid>]`
   This hashes the raw bytes, copies the file to staging, and prints one `create_file` call per file. A sha already prepared or recorded is skipped. `--date` defaults to the file's mtime date.
2. The parent calls the Google Drive connector's `create_file` with exactly the printed arguments: `title=<sha>.<ext>`, `parentId=<folder>`, `base64Content="sha256:<sha>:<abs path>"` (a file reference, so the bytes never pass through the model), `contentMimeType`, and `disableConversionToGoogleType=true`.
3. `vault.py record --sha <sha> --file-id <returned id>` moves the entry to the index and writes the manifest.
4. `vault.py stage --manifest ~/GraphOriginals/manifests/<sha>.json --dry-run`, then run it without `--dry-run`.

## Pointer shape (`public.documents`)

| column | value |
|---|---|
| `title` | `<vault_kind> <YYYY-MM-DD>`, generic, never a subject or a name |
| `source_type` | mapped: email→`other`, meeting_note→`note`, notion_comment→`note`, transcript→`transcript`, other→`other` |
| `sha256` | hash of the raw bytes |
| `blob_key` | `gdrive:<file_id>` |
| `visibility` | `private` |
| `doc_date`, `event_id` | as given (`event_id` optional) |
| `metadata` | `{vault: "gdrive", vault_kind, original_ext, bytes}` and nothing else |

The upsert is keyed on `(sha256, retrieval_profile)`, the live unique index; `retrieval_profile` stays at its `dense_v1` default. Writes go through `spine_client.write`, so the ADR-9 guard runs, and `vault.py` also refuses any manifest with non-pointer keys or a non-generic title.

**Native kinds.** Once migration 0022 widens `documents_source_type_check`, `stage --native-kinds` writes `source_type = vault_kind`. `backfill-native --dry-run` (then a live run) rewrites existing `gdrive:%` rows from `metadata.vault_kind`. Before 0022 lands, a live native write fails the CHECK.

## Nightly sharing audit

`vault.py audit` lists the index (sha, kind, date, file id; never content) and prints the folder id plus every file id. The parent calls `get_file_permissions` on each one and expects a single owner permission (Alex) with no `anyone`, domain or extra-user grants. Any extra grant is an incident: revoke it in Drive first, then open a Linear issue.

## Re-mining

1. `vault.py fetch-plan --sha <sha>` prints the Drive file id and the save path `~/GraphOriginals/work/<sha>.<ext>`.
2. The parent downloads the file through the Drive connector to exactly that path.
3. `vault.py verify --sha <sha>` re-hashes the copy against the index; a mismatch exits 1.
4. Mine from the work copy, then delete it when done.
