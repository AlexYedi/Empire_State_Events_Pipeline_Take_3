#!/usr/bin/env python3
"""vault — the private originals vault for the knowledge graph (YED-384; design YED-390, 2026-11-11).

Originals (emails, transcripts, meeting notes, Notion comments) live in an owner-only Google Drive folder,
"Graph Originals". The graph holds a POINTER only: one `public.documents` row per original with a generic
title, the sha256 and `blob_key = 'gdrive:<file_id>'`. No content, excerpt, subject line or name ever
enters the graph, the repo, or this script's output.

Drive I/O is done by the PARENT session through the Google Drive connector (no new credential). This
script does everything else, entirely on local files under VAULT_HOME (default ~/GraphOriginals, which
must sit outside every git work tree):

  prepare <path>... --kind K [--date YYYY-MM-DD] [--event-id UUID]
        hash raw bytes, copy to staging/<sha>.<ext>, append pending.jsonl, print the create_file call
  record --sha S --file-id F      pending -> index.jsonl; write + print the documents-row manifest
  stage --manifest M [--dry-run] [--native-kinds]
        upsert the row through spine_client.write (on_conflict=sha256,retrieval_profile)
  backfill-native [--dry-run]     rewrite source_type from metadata.vault_kind for gdrive:% rows
                                  (needs migration 0022's widened CHECK before a live run)
  audit                           list the index + the file ids to check with get_file_permissions
  fetch-plan --sha S              where to save a re-mining download (work/<sha>.<ext>)
  verify --sha S                  re-hash the work copy against the index
  --selftest                      offline: temp fixtures, stubbed spine_client

Config: VAULT_HOME/vault.json = {"drive_folder_id": "..."} (never in the repo). Runbook:
.claude/references/originals-vault.md
"""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, mimetypes, os, re, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import spine_client  # noqa: E402

_spine = spine_client          # the selftest swaps in a stub; every graph read/write goes through this name

# CLI kind -> documents.source_type allowed by the live CHECK (0009). --native-kinds writes the kind itself
# once migration 0022 widens the CHECK. The fine kind always rides along as metadata.vault_kind.
KIND_TO_SOURCE_TYPE = {
    "email": "other",
    "transcript": "transcript",
    "meeting_note": "note",
    "notion_comment": "note",
    "other": "other",
}
UPSERT_TABLE = "documents?on_conflict=sha256,retrieval_profile"   # retrieval_profile stays at its dense_v1 default
ROW_KEYS = {"title", "source_type", "sha256", "blob_key", "visibility", "doc_date", "event_id", "metadata"}
META_KEYS = {"vault", "vault_kind", "original_ext", "bytes"}
TITLE_RE = re.compile(r"^(%s) \d{4}-\d{2}-\d{2}$" % "|".join(KIND_TO_SOURCE_TYPE))
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
FILE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{10,100}$")
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
EXT_RE = re.compile(r"^[a-z0-9]{1,10}$")


class VaultError(Exception):
    pass


# ---------------------------------------------------------------------------------------------
# paths + the outside-every-git-work-tree rule
# ---------------------------------------------------------------------------------------------
def home() -> str:
    return os.path.expanduser(os.environ.get("VAULT_HOME", "~/GraphOriginals"))


def p(*parts: str) -> str:
    return os.path.join(home(), *parts)


def _nearest_existing(path: str) -> str:
    while not os.path.exists(path):
        parent = os.path.dirname(path)
        if parent == path:
            break
        path = parent
    return path


def _known_roots() -> list[str]:
    """This repo plus every sibling checkout (worktrees included) — a case-insensitive prefix backstop."""
    repo = os.path.realpath(os.path.join(HERE, "..", ".."))
    roots = {repo}
    parent = os.path.dirname(repo)
    try:
        for name in os.listdir(parent):
            cand = os.path.join(parent, name)
            if os.path.exists(os.path.join(cand, ".git")):
                roots.add(os.path.realpath(cand))
    except OSError:
        pass
    return sorted(roots)


def in_git_tree(path: str) -> str | None:
    """Why `path` is inside a git work tree, or None. Fail-closed: any doubt is a refusal reason.
    Layers (each tested alone in --selftest):
      1. realpath — symlinks anywhere in the path are resolved before any check;
      2. an ancestor walk for a `.git` entry (file or dir: covers worktrees and submodules);
      3. `git rev-parse --is-inside-work-tree` from the nearest existing ancestor, with GIT_DIR /
         GIT_WORK_TREE stripped from the environment so a caller's env cannot redirect it;
      4. casefold prefix match against the known checkouts (macOS volumes are case-insensitive, and
         realpath does not canonicalise case)."""
    real = os.path.realpath(os.path.expanduser(path))
    probe = _nearest_existing(real)
    d = probe if os.path.isdir(probe) else os.path.dirname(probe)
    cur = d
    while True:
        if os.path.lexists(os.path.join(cur, ".git")):
            return f"ancestor {cur} has a .git entry"
        nxt = os.path.dirname(cur)
        if nxt == cur:
            break
        cur = nxt
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    try:
        r = subprocess.run(["git", "-C", d, "rev-parse", "--is-inside-work-tree"], capture_output=True,
                           text=True, env=env, timeout=10)
    except (OSError, subprocess.SubprocessError) as e:
        return f"git check could not run ({type(e).__name__}); refusing"
    if r.returncode == 0 and r.stdout.strip() == "true":
        return "git rev-parse reports a work tree"
    if r.returncode != 0 and "not a git repository" not in (r.stderr or "").lower():
        return "git rev-parse failed unexpectedly; refusing"
    low = real.casefold()
    for root in _known_roots():
        rl = root.casefold()
        if low == rl or low.startswith(rl + os.sep):
            return f"inside known checkout {root}"
    return None


def require_outside_git(path: str) -> None:
    why = in_git_tree(path)
    if why:
        raise VaultError(f"refusing: {path} is inside a git work tree ({why}). Vault files never enter a repo.")


def ensure_dirs() -> None:
    require_outside_git(home())
    for sub in ("", "staging", "work", "manifests"):
        os.makedirs(p(sub), mode=0o700, exist_ok=True)
    require_outside_git(home())            # re-check after creation: a pre-planted symlink resolves now


def folder_id() -> str:
    try:
        fid = json.load(open(p("vault.json"), encoding="utf-8"))["drive_folder_id"]
    except (OSError, ValueError, KeyError) as e:
        raise VaultError(f"missing {p('vault.json')} with drive_folder_id ({type(e).__name__})")
    if not FILE_ID_RE.match(fid):
        raise VaultError("vault.json drive_folder_id has an unexpected shape")
    return fid


# ---------------------------------------------------------------------------------------------
# jsonl stores (local, outside git)
# ---------------------------------------------------------------------------------------------
def load(name: str) -> list[dict]:
    try:
        return [json.loads(l) for l in open(p(name), encoding="utf-8") if l.strip()]
    except FileNotFoundError:
        return []


def save(name: str, rows: list[dict]) -> None:
    tmp = p(name + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    os.replace(tmp, p(name))


def append(name: str, row: dict) -> None:
    with open(p(name), "a", encoding="utf-8") as f:
        f.write(json.dumps(row, sort_keys=True) + "\n")


def find(rows: list[dict], sha: str) -> dict | None:
    return next((r for r in rows if r["sha256"] == sha), None)


def sha_file(path: str) -> tuple[str, int]:
    h, n = hashlib.sha256(), 0
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
            n += len(chunk)
    return h.hexdigest(), n


def ext_of(path: str) -> str:
    e = os.path.splitext(path)[1].lstrip(".").lower()
    return e if EXT_RE.match(e) else "bin"


def check_sha(s: str) -> str:
    if not SHA_RE.match(s or ""):
        raise VaultError("--sha must be 64 lowercase hex")
    return s


# ---------------------------------------------------------------------------------------------
# verbs
# ---------------------------------------------------------------------------------------------
def prepare(paths: list[str], kind: str, date: str | None, event_id: str | None, out=print) -> int:
    if kind not in KIND_TO_SOURCE_TYPE:
        raise VaultError(f"--kind must be one of {sorted(KIND_TO_SOURCE_TYPE)}")
    if date:
        dt.date.fromisoformat(date)
    if event_id and not UUID_RE.match(event_id):
        raise VaultError("--event-id must be a lowercase uuid")
    ensure_dirs()
    fid = folder_id()
    known = {r["sha256"] for r in load("index.jsonl")} | {r["sha256"] for r in load("pending.jsonl")}
    for src in paths:
        if not os.path.isfile(src):
            raise VaultError("not a regular file (path withheld from output)")
        sha, n = sha_file(src)
        ext = ext_of(src)
        dest = p("staging", f"{sha}.{ext}")
        if sha in known:
            out(f"skip {sha} (already staged or recorded)")
            continue
        require_outside_git(dest)
        if os.path.lexists(dest):
            if os.path.islink(dest):
                raise VaultError(f"refusing: {dest} is a symlink")
        else:
            shutil.copyfile(src, dest)
            os.chmod(dest, 0o600)
        if sha_file(dest)[0] != sha:
            raise VaultError(f"staging copy of {sha} does not re-hash; aborting")
        mime = mimetypes.guess_type(f"x.{ext}")[0] or "application/octet-stream"
        d = date or dt.datetime.fromtimestamp(os.stat(src).st_mtime).date().isoformat()
        entry = {"sha256": sha, "kind": kind, "doc_date": d, "event_id": event_id, "ext": ext, "bytes": n,
                 "mime": mime, "prepared_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
        append("pending.jsonl", entry)
        known.add(sha)
        out(f"prepared {sha} ({kind}, {d}, {n} bytes)")
        out("  create_file " + json.dumps({
            "title": f"{sha}.{ext}", "parentId": fid,
            "base64Content": f"sha256:{sha}:{os.path.realpath(dest)}",
            "contentMimeType": mime, "disableConversionToGoogleType": True}))
        out(f"  then: vault.py record --sha {sha} --file-id <returned file id>")
    return 0


def manifest_for(entry: dict, file_id: str) -> dict:
    row = {
        "title": f"{entry['kind']} {entry['doc_date']}",
        "source_type": KIND_TO_SOURCE_TYPE[entry["kind"]],
        "sha256": entry["sha256"],
        "blob_key": f"gdrive:{file_id}",
        "visibility": "private",
        "doc_date": entry["doc_date"],
        "metadata": {"vault": "gdrive", "vault_kind": entry["kind"], "original_ext": entry["ext"],
                     "bytes": entry["bytes"]},
    }
    if entry.get("event_id"):
        row["event_id"] = entry["event_id"]
    return {"table": "documents", "row": row}


def validate_manifest(m: dict) -> dict:
    """The pointer contract, independent of spine_client's PII guard: only known keys, generic title."""
    if set(m) != {"table", "row"} or m["table"] != "documents":
        raise VaultError("manifest must be exactly {table: documents, row: {...}}")
    row = m["row"]
    extra = set(row) - ROW_KEYS
    if extra:
        raise VaultError(f"manifest row has non-pointer keys {sorted(extra)}")
    meta = row.get("metadata") or {}
    if set(meta) - META_KEYS or meta.get("vault") != "gdrive":
        raise VaultError("manifest metadata must be exactly vault/vault_kind/original_ext/bytes")
    kind = meta.get("vault_kind")
    if kind not in KIND_TO_SOURCE_TYPE or not TITLE_RE.match(row.get("title", "")) \
            or not row["title"].startswith(kind + " "):
        raise VaultError("title must be the generic '<vault_kind> <YYYY-MM-DD>'")
    if not SHA_RE.match(row.get("sha256", "")) or not str(row.get("blob_key", "")).startswith("gdrive:") \
            or not FILE_ID_RE.match(row["blob_key"][7:]) or row.get("visibility") != "private":
        raise VaultError("manifest needs sha256 (64 hex), blob_key gdrive:<id>, visibility private")
    if row.get("source_type") not in (KIND_TO_SOURCE_TYPE[kind], kind):
        raise VaultError("source_type must be the mapped or native value of vault_kind")
    if not isinstance(meta.get("bytes"), int) or not EXT_RE.match(str(meta.get("original_ext", ""))):
        raise VaultError("metadata.bytes must be an int and original_ext a short extension")
    return row


def record(sha: str, file_id: str, out=print) -> int:
    check_sha(sha)
    if not FILE_ID_RE.match(file_id or ""):
        raise VaultError("--file-id has an unexpected shape")
    ensure_dirs()
    index = load("index.jsonl")
    entry = find(index, sha)
    if entry is None:
        pending = load("pending.jsonl")
        entry = find(pending, sha)
        if entry is None:
            raise VaultError(f"{sha} is not pending; run prepare first")
        entry = {**entry, "file_id": file_id,
                 "recorded_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
        append("index.jsonl", entry)
        save("pending.jsonl", [r for r in pending if r["sha256"] != sha])
    elif entry["file_id"] != file_id:
        raise VaultError(f"{sha} is already recorded with a different file id; resolve by hand")
    m = manifest_for(entry, entry["file_id"])
    validate_manifest(m)
    mp = p("manifests", f"{sha}.json")
    with open(mp, "w", encoding="utf-8") as f:
        json.dump(m, f, indent=2, sort_keys=True)
    out(json.dumps(m, sort_keys=True))
    out(f"manifest: {mp}")
    return 0


def stage(manifest_path: str, dry_run: bool, native_kinds: bool, out=print) -> int:
    m = json.load(open(manifest_path, encoding="utf-8"))
    row = dict(validate_manifest(m))
    if native_kinds:
        row["source_type"] = row["metadata"]["vault_kind"]
    st, body = _spine.write(UPSERT_TABLE, row, prefer="resolution=ignore-duplicates,return=representation",
                            dry_run=dry_run)
    if not dry_run and st not in (200, 201):
        out(f"stage: POST documents -> {st}: {str(body)[:300]}")
        return 1
    out(("DRY-RUN " if dry_run else "") + f"stage documents sha256={row['sha256']} source_type={row['source_type']} "
        f"title={row['title']!r} blob_key={row['blob_key']} -> status {st}")
    return 0


def backfill_native(dry_run: bool, out=print) -> int:
    st, rows = _spine.req("GET", "/documents?blob_key=like.gdrive:*&select=id,source_type,metadata")
    if st != 200:
        out(f"backfill-native: GET -> {st}: {str(rows)[:300]}")
        return 1
    todo = [(r["id"], (r.get("metadata") or {}).get("vault_kind")) for r in rows or []
            if (r.get("metadata") or {}).get("vault_kind") in KIND_TO_SOURCE_TYPE
            and r.get("source_type") != (r.get("metadata") or {}).get("vault_kind")]
    for i, k in todo:
        st, body = _spine.write("documents", {"source_type": k}, prefer="return=minimal",
                                patch_filter=f"id=eq.{i}", dry_run=dry_run)
        if not dry_run and st not in (200, 204):
            out(f"backfill-native: PATCH {i} -> {st}: {str(body)[:300]}")
            return 1
    out(("DRY-RUN " if dry_run else "") + f"backfill-native: {len(rows or [])} vault row(s), {len(todo)} to rewrite")
    return 0


def audit(out=print) -> int:
    ensure_dirs()
    index, pending = load("index.jsonl"), load("pending.jsonl")
    out(f"index: {len(index)} recorded · pending: {len(pending)} awaiting upload")
    for r in index:
        out(f"  {r['sha256']}  {r['kind']:<14} {r['doc_date']}  {r['file_id']}")
    for r in pending:
        out(f"  {r['sha256']}  {r['kind']:<14} {r['doc_date']}  (pending)")
    out("get_file_permissions — expect owner-only on each (folder first):")
    out(f"  folder {folder_id()}")
    for r in index:
        out(f"  file   {r['file_id']}")
    return 0


def _indexed(sha: str) -> dict:
    ensure_dirs()
    e = find(load("index.jsonl"), check_sha(sha))
    if not e:
        raise VaultError(f"{sha} is not in the index")
    return e


def fetch_plan(sha: str, out=print) -> int:
    e = _indexed(sha)
    dest = p("work", f"{sha}.{e['ext']}")
    require_outside_git(dest)
    out(json.dumps({"download_file_id": e["file_id"], "save_to": os.path.realpath(dest),
                    "then": f"vault.py verify --sha {sha}"}))
    return 0


def verify(sha: str, out=print) -> int:
    e = _indexed(sha)
    dest = p("work", f"{sha}.{e['ext']}")
    require_outside_git(dest)
    if not os.path.isfile(dest):
        out(f"verify: no work copy at {dest}")
        return 1
    got, n = sha_file(dest)
    ok = got == sha and n == e["bytes"]
    out(f"verify {sha}: {'OK' if ok else 'MISMATCH'} ({n} bytes)")
    return 0 if ok else 1


# ---------------------------------------------------------------------------------------------
# selftest — offline, temp fixtures, stubbed spine_client
# ---------------------------------------------------------------------------------------------
class _StubSpine:
    """Records calls; runs the REAL spine_client guard so the row is proven guard-clean too."""
    def __init__(self, rows=None):
        self.calls, self.rows = [], rows or []

    def write(self, table, rows, prefer=None, *, patch_filter=None, dry_run=False, **kw):
        path = f"/{table.strip('/')}" + (f"?{patch_filter}" if patch_filter else "")
        spine_client.guard_body(path, rows)
        self.calls.append(("PATCH" if patch_filter else "POST", path, rows, prefer, dry_run))
        return (0 if dry_run else 201), {"dry_run": dry_run}

    def req(self, method, path, body=None, prefer=None, **kw):
        self.calls.append((method, path, body, prefer, None))
        return 200, self.rows


def selftest() -> bool:
    global _spine
    results = []

    def case(name, fn):
        try:
            fn()
            results.append((True, name, ""))
        except Exception as e:  # noqa: BLE001
            results.append((False, name, f"{type(e).__name__}: {e}"))

    def raises(fn, needle=""):
        try:
            fn()
        except VaultError as e:
            assert needle in str(e), f"wrong refusal: {e}"
            return
        raise AssertionError("expected a refusal")

    saved_home, saved_spine = os.environ.get("VAULT_HOME"), _spine
    tmp = os.path.realpath(tempfile.mkdtemp(prefix="vault-selftest-"))
    secret = "Subject: Q3 plan with Jane Roe jane@example.com"
    try:
        vh = os.path.join(tmp, "home")
        os.environ["VAULT_HOME"] = vh
        os.makedirs(vh)
        json.dump({"drive_folder_id": "FAKEfolder_0123456789"}, open(os.path.join(vh, "vault.json"), "w"))
        src_dir = os.path.join(tmp, "inbox")
        os.makedirs(src_dir)
        f1 = os.path.join(src_dir, "Q3 plan - Jane Roe.eml")
        open(f1, "w").write(secret + "\n\nbody text that must never leave\n")
        sha1 = sha_file(f1)[0]
        repo = os.path.join(tmp, "FakeRepo")
        os.makedirs(repo)
        subprocess.run(["git", "init", "-q", repo], check=True)
        out: list[str] = []
        o = out.append

        # --- outside-git refusal, each layer and each trick --------------------------------------
        case("plain path outside git passes", lambda: require_outside_git(vh))
        case("path inside a git repo is refused",
             lambda: raises(lambda: require_outside_git(os.path.join(repo, "staging")), "git work tree"))
        case("not-yet-existing nested path in repo is refused",
             lambda: raises(lambda: require_outside_git(os.path.join(repo, "a", "b", "c"))))
        link = os.path.join(tmp, "innocent-link")
        os.symlink(repo, link)
        case("symlink into a repo is refused (realpath)",
             lambda: raises(lambda: require_outside_git(os.path.join(link, "staging"))))
        sneaky = os.path.join(tmp, "sneaky-home")
        os.symlink(os.path.join(repo, "vault"), sneaky)
        def _vh_symlink():
            os.environ["VAULT_HOME"] = sneaky
            try:
                raises(lambda: ensure_dirs())
            finally:
                os.environ["VAULT_HOME"] = vh
        case("VAULT_HOME symlinked into a repo is refused", _vh_symlink)
        def _case_trick():
            alt = os.path.join(tmp, "fakerepo", "staging")          # FakeRepo with different case
            if os.path.exists(os.path.join(tmp, "fakerepo")):       # case-insensitive volume: must refuse
                raises(lambda: require_outside_git(alt))
            else:                                                  # case-sensitive: a different dir, fine
                assert in_git_tree(alt) is None
        case("case-variant path to a repo is refused on case-insensitive volumes", _case_trick)
        def _casefold_layer():
            real_roots = globals()["_known_roots"]
            plain = os.path.join(tmp, "NoGitHere")
            os.makedirs(plain, exist_ok=True)
            globals()["_known_roots"] = lambda: [plain]
            try:     # no .git and no git repo here: only layer 4 can fire, for both spellings
                assert "known checkout" in (in_git_tree(os.path.join(plain, "x")) or "")
                assert "known checkout" in (in_git_tree(os.path.join(tmp, "NOGITHERE", "x")) or "")
                assert in_git_tree(os.path.join(tmp, "NoGitHereNot", "x")) is None   # prefix needs a separator
                alias = os.path.join(tmp, "alias-to-checkout")
                os.symlink(plain, alias)    # a symlink only realpath can see through, before the casefold match
                assert "known checkout" in (in_git_tree(os.path.join(alias, "x")) or "")
            finally:
                globals()["_known_roots"] = real_roots
        case("casefold prefix layer alone catches a known checkout", _casefold_layer)
        def _git_env():
            os.environ["GIT_DIR"] = os.path.join(tmp, "nowhere")
            try:
                raises(lambda: require_outside_git(os.path.join(repo, "x")))
            finally:
                del os.environ["GIT_DIR"]
        case("GIT_DIR in the env cannot redirect the check", _git_env)
        wt_link = os.path.join(tmp, "WT")
        os.makedirs(wt_link)
        open(os.path.join(wt_link, ".git"), "w").write("gitdir: /nonexistent\n")
        case("a .git FILE (worktree) ancestor is refused",
             lambda: raises(lambda: require_outside_git(os.path.join(wt_link, "s"))))
        case("the real staging dir for this run is outside git", lambda: require_outside_git(home()))

        # --- prepare / record / idempotency ------------------------------------------------------
        _spine = _StubSpine()
        case("prepare stages one file", lambda: prepare([f1], "email", "2026-11-10", None, out=o))
        case("staged copy is in staging/<sha>.eml and re-hashes",
             lambda: (assert_(os.path.isfile(p("staging", f"{sha1}.eml"))),
                      assert_(sha_file(p("staging", f"{sha1}.eml"))[0] == sha1)))
        n_before = len(out)
        case("prepare again is skipped (idempotent)", lambda: prepare([f1], "email", "2026-11-10", None, out=o))
        case("second prepare printed a skip, no new pending row",
             lambda: (assert_(any("skip" in l for l in out[n_before:])), assert_(len(load("pending.jsonl")) == 1)))
        case("create_file args are exact", lambda: assert_(any(
            f'"title": "{sha1}.eml"' in l and '"parentId": "FAKEfolder_0123456789"' in l
            and f'"base64Content": "sha256:{sha1}:' in l and '"disableConversionToGoogleType": true' in l
            for l in out)))
        case("record moves pending -> index", lambda: (record(sha1, "FAKEfile_abcdefghij", out=o),
                                                         assert_(not load("pending.jsonl")),
                                                         assert_(len(load("index.jsonl")) == 1)))
        case("record again is idempotent", lambda: (record(sha1, "FAKEfile_abcdefghij", out=o),
                                                      assert_(len(load("index.jsonl")) == 1)))
        case("record with a different file id is refused",
             lambda: raises(lambda: record(sha1, "OTHERfile_abcdefghij", out=o), "different file id"))
        case("prepare after record is skipped", lambda: (prepare([f1], "email", None, None, out=o),
                                                          assert_(not load("pending.jsonl"))))

        # --- generic titles + no content ---------------------------------------------------------
        mpath = p("manifests", f"{sha1}.json")
        case("manifest title is generic", lambda: assert_(
            json.load(open(mpath))["row"]["title"] == "email 2026-11-10"))
        case("manifest maps email -> other, vault_kind kept", lambda: assert_(
            json.load(open(mpath))["row"]["source_type"] == "other"
            and json.load(open(mpath))["row"]["metadata"]["vault_kind"] == "email"))
        def _no_content():
            blob = open(mpath).read() + "\n".join(out) + open(p("index.jsonl")).read()
            for needle in ("Jane", "Roe", "Q3 plan", "Subject", "example.com", "body text", "never leave"):
                assert needle not in blob, f"leaked {needle!r}"
        case("manifest, index and stdout carry no content, subject or names", _no_content)
        bad = {"table": "documents", "row": {**json.load(open(mpath))["row"], "title": "Q3 plan with Jane"}}
        case("a subject-line title is refused", lambda: raises(lambda: validate_manifest(bad), "generic"))
        bad2 = {"table": "documents", "row": {**json.load(open(mpath))["row"], "excerpt": "x"}}
        case("an extra content column is refused", lambda: raises(lambda: validate_manifest(bad2), "non-pointer"))
        bad3 = json.loads(open(mpath).read())
        bad3["row"]["metadata"]["subject"] = "Q3"
        case("extra metadata keys are refused", lambda: raises(lambda: validate_manifest(bad3), "metadata"))
        for k in KIND_TO_SOURCE_TYPE:
            e = {"sha256": "a" * 64, "kind": k, "doc_date": "2026-01-02", "ext": "txt", "bytes": 1}
            case(f"generic title for {k}", lambda e=e, k=k: assert_(
                validate_manifest(manifest_for(e, "FAKEfile_abcdefghij"))["title"] == f"{k} 2026-01-02"))

        # --- stage + backfill through the stub ----------------------------------------------------
        def _stage(native):
            _spine.calls.clear()
            assert stage(mpath, True, native, out=o) == 0
            method, path, row, prefer, dry = _spine.calls[0]
            assert method == "POST" and path == "/documents?on_conflict=sha256,retrieval_profile" and dry
            assert "ignore-duplicates" in prefer and "retrieval_profile" not in row
            assert row["source_type"] == ("email" if native else "other")
        case("stage dry-run upserts on (sha256, retrieval_profile), mapped kind", lambda: _stage(False))
        case("stage --native-kinds writes source_type = vault_kind", lambda: _stage(True))
        _spine = _StubSpine(rows=[
            {"id": "11111111-1111-1111-1111-111111111111", "source_type": "other", "metadata": {"vault_kind": "email"}},
            {"id": "22222222-2222-2222-2222-222222222222", "source_type": "transcript",
             "metadata": {"vault_kind": "transcript"}}])
        def _backfill():
            assert backfill_native(True, out=o) == 0
            patches = [c for c in _spine.calls if c[0] == "PATCH"]
            assert len(patches) == 1 and patches[0][1].endswith("id=eq.11111111-1111-1111-1111-111111111111")
            assert patches[0][2] == {"source_type": "email"} and patches[0][4] is True
            assert "blob_key=like.gdrive:*" in _spine.calls[0][1]
        case("backfill-native rewrites only rows whose kind differs (dry-run)", _backfill)

        # --- audit / fetch-plan / verify ----------------------------------------------------------
        n0 = len(out)
        case("audit lists file + folder ids", lambda: (audit(out=o), assert_(
            any("FAKEfile_abcdefghij" in l for l in out[n0:]) and any("FAKEfolder" in l for l in out[n0:]))))
        n1 = len(out)
        case("fetch-plan points at work/<sha>.eml", lambda: (fetch_plan(sha1, out=o), assert_(
            json.loads(out[n1])["save_to"].endswith(f"work/{sha1}.eml"))))
        case("verify fails with no work copy", lambda: assert_(verify(sha1, out=o) == 1))
        def _verify_ok():
            shutil.copyfile(f1, p("work", f"{sha1}.eml"))
            assert verify(sha1, out=o) == 0
            open(p("work", f"{sha1}.eml"), "a").write("tamper")
            assert verify(sha1, out=o) == 1
        case("verify passes on a true copy and fails on a tampered one", _verify_ok)
        case("no output line anywhere contains file content", _no_content)
    finally:
        _spine = saved_spine
        if saved_home is None:
            os.environ.pop("VAULT_HOME", None)
        else:
            os.environ["VAULT_HOME"] = saved_home
        shutil.rmtree(tmp, ignore_errors=True)
    for ok, name, why in results:
        print(f"  {'✓' if ok else '✗'} {name}" + (f" — {why}" if why else ""))
    passed = sum(ok for ok, _, _ in results)
    print(f"vault selftest: {passed}/{len(results)} passed")
    return passed == len(results)


def assert_(cond, msg="assertion failed"):
    if not cond:
        raise AssertionError(msg)


# ---------------------------------------------------------------------------------------------
def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return 0 if selftest() else 1
    ap = argparse.ArgumentParser(prog="vault.py", description="private originals vault (YED-384)")
    sub = ap.add_subparsers(dest="verb", required=True)
    s = sub.add_parser("prepare")
    s.add_argument("paths", nargs="+")
    s.add_argument("--kind", required=True, choices=sorted(KIND_TO_SOURCE_TYPE))
    s.add_argument("--date")
    s.add_argument("--event-id")
    s = sub.add_parser("record")
    s.add_argument("--sha", required=True)
    s.add_argument("--file-id", required=True)
    s = sub.add_parser("stage")
    s.add_argument("--manifest", required=True)
    s.add_argument("--dry-run", action="store_true")
    s.add_argument("--native-kinds", action="store_true", help="source_type = vault_kind (needs migration 0022)")
    s = sub.add_parser("backfill-native")
    s.add_argument("--dry-run", action="store_true")
    sub.add_parser("audit")
    for name in ("fetch-plan", "verify"):
        sub.add_parser(name).add_argument("--sha", required=True)
    a = ap.parse_args(argv)
    if a.verb == "prepare":
        return prepare(a.paths, a.kind, a.date, a.event_id)
    if a.verb == "record":
        return record(a.sha, a.file_id)
    if a.verb == "stage":
        return stage(a.manifest, a.dry_run, a.native_kinds)
    if a.verb == "backfill-native":
        return backfill_native(a.dry_run)
    if a.verb == "audit":
        return audit()
    if a.verb == "fetch-plan":
        return fetch_plan(a.sha)
    return verify(a.sha)


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except VaultError as e:
        print(f"vault: {e}", file=sys.stderr)
        sys.exit(3)
    except spine_client.PIIViolation as e:
        print(f"PIIViolation: {e}", file=sys.stderr)
        sys.exit(spine_client.PIIViolation.exit_code)
