#!/usr/bin/env python3
"""YED-307 lane 3 — research_frontier: Hugging Face trending models + last week's papers.

Two public, unauthenticated Hugging Face endpoints → `public.event` rows:
  * models  GET /api/models?sort=trendingScore&limit=50 → kind 'launch', signal_type 'model_release'.
    Derivatives are dropped (a base_model:quantized|adapter|merge|finetune: tag means someone else's
    release, re-packaged), and so is anything created more than MAX_MODEL_AGE_DAYS before the run
    week (trending-but-old is not a release signal).
  * papers  GET /api/daily_papers?date=D&limit=100 for each day of the PREVIOUS ISO week (Mon–Sun)
    → kind 'market', signal_type 'paper'. upvotes >= MIN_PAPER_UPVOTES, deduped on the arXiv id
    across days, capped at MAX_PAPERS_PER_WEEK by upvotes.

Contract (mirrors lane 1, ats_pulse.py):
  * `week` is the previous ISO week — the week a Monday 05:00 UTC run closes (ats_pulse runs Sunday
    and labels the week that Sunday ends; same semantics, one day later).
  * NO PERSON NAMES (ADR-9 boundary + ADR-7 R2): paper authors and submittedBy are never read into a
    row; no entity edges (an HF namespace is not a canonical company). Every row is PII-scanned with
    spine_client's own regexes (via ats_pulse.scan_pii) — a hit refuses THAT row — and the batch then
    goes through spine_client.write's guard (dry_run in the dry-run era, for real when live).
  * Idempotency is keyed on `source` (hf:model:<id> / hf:paper:<arxiv id>): before a live insert the
    lane reads which sources already exist (through spine_client.req, never a hand-built REST call)
    and inserts only the new ones. A re-run of a week, or a model still trending next week, is a no-op.
  * EVENT_WRITES_LIVE gate (YED-327): event rows are written only when that env is exactly 'true';
    otherwise they are built, validated and guard-checked, and items_written is 0 (honest: rows
    ACTUALLY written, as ats_pulse after #282).
  * lane_run is REAL and goes to PROD through spine_client.write (the lane-1 decision, same ledger);
    a fetch failure records status 'failed' with the message and the CLI exits 1 — never silent.
  * --dry-run touches no database at all: no prior-read, no event write, no lane_run.

Selftest: offline fixtures only. Run: python3 hf_frontier.py --selftest
"""
from __future__ import annotations

import argparse
import http.client
import io
import json
import os
import re
import subprocess
import sys
import textwrap
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(__file__))
from ats_pulse import scan_pii, week_bucket  # noqa: E402  (lane-1 helpers: ISO week key + ADR-9 scan)
from spine_client import ALLOW, PIIViolation  # noqa: E402

PRODUCER = "hf_frontier"
LANE = "research_frontier"            # public.lane_registry key (seeded by 0016)
MODELS_URL = "https://huggingface.co/api/models?sort=trendingScore&limit=50"
PAPERS_URL = "https://huggingface.co/api/daily_papers?date={day}&limit=100"
UA = "esep-hf-frontier/1 (+https://github.com/AlexYedi/Empire_State_Events_Pipeline_Take_3)"

DERIVATIVE_TAG_PREFIXES = ("base_model:quantized:", "base_model:adapter:",
                           "base_model:merge:", "base_model:finetune:")
MAX_MODEL_AGE_DAYS = 120              # created more than this before the run week's Monday → dropped
MIN_PAPER_UPVOTES = 20
MAX_PAPERS_PER_WEEK = 40
MAX_KEYWORDS = 8
CONFIDENCE = 0.9                      # same as lane 1: a first-party listing, not a verified claim
FETCH_TIMEOUT = 30
FETCH_RETRIES = 1                     # one retry after the first attempt
RETRY_WAIT = 3.0
PRIOR_READ_CHUNK = 40                 # sources per prior-read GET (keeps the URL short)
EVENT_WRITES_ENV = "EVENT_WRITES_LIVE"

MODEL_META = {"hf_id", "org", "trending_score", "likes", "downloads", "pipeline_tag", "week"}
PAPER_META = {"arxiv_id", "org", "upvotes", "keywords", "week"}
ROW_KEYS = {"title", "kind", "signal_type", "event_date", "url", "source", "confidence", "metadata"}


class FetchError(Exception):
    """A Hugging Face fetch that failed after its retry. The run records it; it never crashes silently."""


# ---------------------------------------------------------------------------
# Weeks
# ---------------------------------------------------------------------------

def report_week(asof: date) -> tuple[str, date, date]:
    """asof → (previous ISO week key, its Monday, its Sunday). A Monday run reports the week just closed."""
    monday = asof - timedelta(days=asof.isoweekday() - 1) - timedelta(days=7)
    return week_bucket(monday), monday, monday + timedelta(days=6)


def run_week_monday(asof: date) -> date:
    return asof - timedelta(days=asof.isoweekday() - 1)


# ---------------------------------------------------------------------------
# Fetch
# ---------------------------------------------------------------------------

def fetch_json(url: str, *, opener=None, retries: int = FETCH_RETRIES, sleep=time.sleep):
    """GET a JSON list with a timeout and `retries` retries. Raises FetchError with the cause."""
    opener = opener or urllib.request.urlopen
    last: Exception | None = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with opener(req, timeout=FETCH_TIMEOUT) as r:
                data = json.load(r)
            if not isinstance(data, list):
                raise ValueError(f"expected a JSON list, got {type(data).__name__}")
            return data
        except (urllib.error.URLError, http.client.HTTPException, OSError, ValueError) as e:
            last = e                  # HTTPError ⊂ URLError; JSONDecodeError ⊂ ValueError; timeouts ⊂ OSError
            if attempt < retries:
                sleep(RETRY_WAIT)
    raise FetchError(f"{url} failed after {retries + 1} attempt(s): {type(last).__name__}: {str(last)[:200]}")


def fetch_all(week_monday: date, fetch=fetch_json) -> tuple[list, dict]:
    """Trending models + the 7 days of papers for the report week."""
    models = fetch(MODELS_URL)
    papers = {}
    for i in range(7):
        day = (week_monday + timedelta(days=i)).isoformat()
        papers[day] = fetch(PAPERS_URL.format(day=day))
    return models, papers


# ---------------------------------------------------------------------------
# Filter + map
# ---------------------------------------------------------------------------

def _int_or_none(v):
    return v if type(v) is int else None


def _day(ts) -> str | None:
    s = str(ts or "")[:10]
    try:
        return date.fromisoformat(s).isoformat()
    except ValueError:
        return None


def is_derivative(model: dict) -> bool:
    return any(str(t).startswith(DERIVATIVE_TAG_PREFIXES) for t in (model.get("tags") or []))


def filter_models(raw: list, asof: date) -> tuple[list, dict]:
    cutoff = run_week_monday(asof) - timedelta(days=MAX_MODEL_AGE_DAYS)
    kept, c = [], {"seen": len(raw), "dropped_derivative": 0, "dropped_old": 0, "dropped_undated": 0}
    for m in raw:
        if not isinstance(m, dict) or not m.get("id"):
            c["dropped_undated"] += 1
            continue
        if is_derivative(m):
            c["dropped_derivative"] += 1
            continue
        created = _day(m.get("createdAt"))
        if not created:
            c["dropped_undated"] += 1    # no release date → no release signal
            continue
        if date.fromisoformat(created) < cutoff:
            c["dropped_old"] += 1
            continue
        kept.append(m)
    c["kept"] = len(kept)
    return kept, c


def filter_papers(raw_by_day: dict) -> tuple[list, dict]:
    seen, best = 0, {}
    below = dup = 0
    for day in sorted(raw_by_day):
        for entry in raw_by_day[day] or []:
            seen += 1
            p = (entry or {}).get("paper") or {}
            aid = str(p.get("id") or "").strip()
            up = _int_or_none(p.get("upvotes"))
            if not aid or up is None or up < MIN_PAPER_UPVOTES:
                below += 1
                continue
            if aid in best:
                dup += 1
                if up <= _int_or_none(best[aid]["paper"].get("upvotes")):
                    continue
            best[aid] = entry
    ranked = sorted(best.values(), key=lambda e: (-e["paper"]["upvotes"], e["paper"]["id"]))
    kept = ranked[:MAX_PAPERS_PER_WEEK]
    return kept, {"seen": seen, "below_threshold": below, "duplicates": dup,
                  "capped": len(ranked) - len(kept), "kept": len(kept)}


def model_row(m: dict, week: str) -> dict:
    hf_id = str(m["id"])
    org = m.get("author") or (hf_id.split("/", 1)[0] if "/" in hf_id else None)
    return {"title": hf_id, "kind": "launch", "signal_type": "model_release",
            "event_date": _day(m.get("createdAt")), "url": f"https://huggingface.co/{hf_id}",
            "source": f"hf:model:{hf_id}", "confidence": CONFIDENCE,
            "metadata": {"hf_id": hf_id, "org": org,
                         "trending_score": _int_or_none(m.get("trendingScore")),
                         "likes": _int_or_none(m.get("likes")),
                         "downloads": _int_or_none(m.get("downloads")),
                         "pipeline_tag": m.get("pipeline_tag"), "week": week}}


def paper_row(entry: dict, week: str) -> dict:
    """Reads ONLY id/title/upvotes/ai_keywords/publishedAt/organization.name — never authors,
    submittedBy, submittedOnDailyBy, summary or discussion (person names live there)."""
    p = entry["paper"]
    aid = str(p["id"])
    org = (entry.get("organization") or p.get("organization") or {}).get("name")
    title = " ".join(str(p.get("title") or entry.get("title") or aid).split())
    kws = [str(k) for k in (p.get("ai_keywords") or []) if isinstance(k, str)][:MAX_KEYWORDS]
    return {"title": title, "kind": "market", "signal_type": "paper",
            "event_date": _day(p.get("publishedAt") or entry.get("publishedAt")),
            "url": f"https://huggingface.co/papers/{aid}", "source": f"hf:paper:{aid}",
            "confidence": CONFIDENCE,
            "metadata": {"arxiv_id": aid, "org": org, "upvotes": p["upvotes"], "keywords": kws, "week": week}}


def build(raw_models: list, raw_papers: dict, asof: date) -> dict:
    """Fetched payloads → {week, rows, counts}. A row that trips the PII scan is refused, not fatal."""
    week, _, _ = report_week(asof)
    models, mc = filter_models(raw_models, asof)
    papers, pc = filter_papers(raw_papers)
    rows, refused = [], 0
    for r in [model_row(m, week) for m in models] + [paper_row(p, week) for p in papers]:
        try:
            scan_pii(r)
        except PIIViolation:
            refused += 1
            continue
        rows.append(r)
    return {"week": week, "rows": rows, "refused": refused, "models": mc, "papers": pc,
            "seen": mc["seen"] + pc["seen"]}


# ---------------------------------------------------------------------------
# Validate
# ---------------------------------------------------------------------------

def validate_row(r: dict) -> list[str]:
    problems = []
    tag = r.get("source") or "?"
    if set(r) != ROW_KEYS:
        problems.append(f"{tag}: keys {sorted(r)} != {sorted(ROW_KEYS)}")
    if not set(r) <= ALLOW["event"]:
        problems.append(f"{tag}: column(s) outside spine_client.ALLOW['event']: {sorted(set(r) - ALLOW['event'])}")
    meta = r.get("metadata") or {}
    if r.get("signal_type") == "model_release":
        if r.get("kind") != "launch" or not str(r.get("source", "")).startswith("hf:model:"):
            problems.append(f"{tag}: model rows are kind 'launch' with source hf:model:<id>")
        if set(meta) != MODEL_META:
            problems.append(f"{tag}: metadata keys must be exactly {sorted(MODEL_META)}")
        ints = ("trending_score", "likes", "downloads")
    elif r.get("signal_type") == "paper":
        if r.get("kind") != "market" or not str(r.get("source", "")).startswith("hf:paper:"):
            problems.append(f"{tag}: paper rows are kind 'market' with source hf:paper:<arxiv id>")
        if set(meta) != PAPER_META:
            problems.append(f"{tag}: metadata keys must be exactly {sorted(PAPER_META)}")
        kws = meta.get("keywords")
        if not isinstance(kws, list) or len(kws) > MAX_KEYWORDS:
            problems.append(f"{tag}: keywords must be a list of <= {MAX_KEYWORDS}")
        ints = ("upvotes",)
    else:
        return problems + [f"{tag}: signal_type {r.get('signal_type')!r} is not model_release/paper"]
    for k in ints:
        if meta.get(k) is not None and type(meta[k]) is not int:
            problems.append(f"{tag}: metadata.{k} must be an int or null")
    if not str(r.get("url", "")).startswith("https://huggingface.co/"):
        problems.append(f"{tag}: url must be a huggingface.co URL")
    if not re.fullmatch(r"\d{4}-W\d{2}", str(meta.get("week", ""))):
        problems.append(f"{tag}: metadata.week is not an ISO week bucket")
    try:
        scan_pii(r)
    except PIIViolation as e:
        problems.append(f"{tag}: {e}")
    return problems


def guard_rows(rows: list) -> None:
    """Layer 2: the batch through spine_client.write's own guard, dry_run (sends nothing). Raises PIIViolation."""
    import spine_client
    spine_client.write("event", rows, dry_run=True)


# ---------------------------------------------------------------------------
# Spine I/O (live only — every call goes through spine_client)
# ---------------------------------------------------------------------------

def read_existing_sources(sources: list[str]) -> set[str]:
    """Which of these `source` keys already exist on public.event (the idempotency prior-read)."""
    import spine_client
    found: set[str] = set()
    for i in range(0, len(sources), PRIOR_READ_CHUNK):
        chunk = sources[i:i + PRIOR_READ_CHUNK]
        vals = ",".join('"' + s.replace('"', "") + '"' for s in chunk)
        code, body = spine_client.req("GET", f"/event?select=source&source=in.({spine_client.q(vals)})")
        if code >= 400 or not isinstance(body, list):
            raise RuntimeError(f"prior-read of existing sources failed: HTTP {code}: {str(body)[:200]}")
        found |= {r.get("source") for r in body if isinstance(r, dict)}
    return found


def write_event_rows(rows: list) -> int:
    """One batch insert through spine_client.write (guarded). PostgREST inserts a batch in one
    statement, so on success every row landed — the count is exact."""
    import spine_client
    code, body = spine_client.write("event", rows, prefer="return=minimal")
    if code >= 400:
        raise RuntimeError(f"event insert failed: HTTP {code}: {str(body)[:300]}")
    return len(rows)


def write_lane_run(row: dict) -> None:
    """The REAL lane_run ledger row → PROD via spine_client.write (lane-1 decision: PII-free ledger,
    lane_registry + the freshness healthcheck live in prod)."""
    import spine_client
    code, body = spine_client.write("lane_run", [row], prefer="return=minimal")
    if code >= 400:
        raise RuntimeError(f"lane_run insert failed: HTTP {code}: {str(body)[:300]}")


def events_live(env=None) -> bool:
    return (env if env is not None else os.environ).get(EVENT_WRITES_ENV, "").strip().lower() == "true"


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def lane_run_row(started_at: str, finished_at: str, status: str, seen: int, written: int,
                 refused: int, error: str | None) -> dict:
    return {"lane": LANE, "started_at": started_at, "finished_at": finished_at, "status": status,
            "items_seen": seen, "items_written": written, "items_refused": refused,
            "credits_spent": 0,                       # public API, no credits
            "error": error[:1000] if error else None}


def run(asof: date, *, dry_run: bool, env=None, fetch=fetch_json, reader=read_existing_sources,
        writer=write_event_rows, lane_writer=write_lane_run) -> dict:
    """The whole lane. Returns a report; report['lane_run'] is the ledger row (written unless dry_run)."""
    started = _now()
    week, monday, sunday = report_week(asof)
    live = events_live(env) and not dry_run
    rep = {"week": week, "papers_window": f"{monday.isoformat()}..{sunday.isoformat()}",
           "mode": "dry-run (no database)" if dry_run else ("events LIVE" if live else
                   f"events dry-run ({EVENT_WRITES_ENV} not 'true'); lane_run to prod"),
           "status": "success", "error": None, "seen": 0, "refused": 0, "written": 0,
           "already_present": None, "rows": []}
    try:
        raw_models, raw_papers = fetch_all(monday, fetch)
        b = build(raw_models, raw_papers, asof)
        rep.update(models=b["models"], papers=b["papers"], seen=b["seen"], refused=b["refused"], rows=b["rows"])
        problems = [p for r in b["rows"] for p in validate_row(r)]
        if problems:
            raise ValueError("row validation failed: " + "; ".join(problems[:5]))
        guard_rows(b["rows"])
        if live and b["rows"]:
            existing = reader([r["source"] for r in b["rows"]])
            new = [r for r in b["rows"] if r["source"] not in existing]
            rep["already_present"] = len(b["rows"]) - len(new)
            rep["written"] = writer(new) if new else 0
    except (FetchError, ValueError, PIIViolation, RuntimeError, OSError) as e:
        rep["status"], rep["error"] = "failed", f"{type(e).__name__}: {e}"
    rep["lane_run"] = lane_run_row(started, _now(), rep["status"], rep["seen"], rep["written"],
                                   rep["refused"], rep["error"])
    if not dry_run:
        lane_writer(rep["lane_run"])
    return rep


def summary(rep: dict) -> dict:
    """Counts only — the uploadable artifact."""
    return {"week": rep["week"], "producer": PRODUCER, "status": rep["status"], "mode": rep["mode"],
            "models": rep.get("models"), "papers": rep.get("papers"), "events_built": len(rep["rows"]),
            "items_seen": rep["seen"], "items_refused": rep["refused"], "items_written": rep["written"],
            "already_present": rep["already_present"]}


# ---------------------------------------------------------------------------
# Workflow shell lint (minimal copy of #293's ats_pulse lint — not on main yet, so not importable).
# bash -n alone misses an EOF-terminated heredoc (a warning, exit 0): pair delimiters explicitly too.
# ---------------------------------------------------------------------------

_HEREDOC_OPEN = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")


def shell_script_problems(script: str) -> list[str]:
    problems, stack = [], []
    for line in script.splitlines():
        if stack and line.strip() == stack[-1]:
            stack.pop()
            continue
        m = _HEREDOC_OPEN.search(line)
        if m:
            stack.append(m.group(2))
    problems += [f"heredoc <<'{d}' never terminated" for d in stack]
    try:
        r = subprocess.run(["bash", "-n"], input=script, capture_output=True, text=True, timeout=15)
    except OSError as e:
        return problems + [f"bash -n could not run: {e}"]
    if r.returncode != 0 or "here-document" in r.stderr:
        problems.append("bash -n: " + (r.stderr.strip().splitlines() or [f"exit {r.returncode}"])[-1])
    return problems


def workflow_run_blocks(path: str) -> list[tuple[str, str]]:
    """(step name, script) for every `run: |` block — textual, no yaml dependency."""
    lines = open(path, encoding="utf-8").read().splitlines()
    run_re, name_re = re.compile(r"^(\s*)(?:- )?run: (\||>)"), re.compile(r"^\s*(?:- )?name:\s*(.*)$")
    blocks, name, i = [], "", 0
    while i < len(lines):
        m = run_re.match(lines[i])
        if not m:
            nm = name_re.match(lines[i])
            if nm:
                name = nm.group(1).strip().strip("'\"")
            i += 1
            continue
        indent, body, j = len(m.group(1)), [], i + 1
        while j < len(lines) and (not lines[j].strip() or len(lines[j]) - len(lines[j].lstrip(" ")) > indent):
            body.append(lines[j] if lines[j].strip() else "")
            j += 1
        blocks.append((name, textwrap.dedent("\n".join(body))))
        i = j
    return blocks


# ---------------------------------------------------------------------------
# Selftest — offline fixtures, no network, no database
# ---------------------------------------------------------------------------

ASOF = date(2026, 11, 9)              # a Monday → report week 2026-W45 (Nov 2..8), run-week Monday Nov 9


def _fixture_models() -> list:
    def m(mid, created, tags=(), **kw):
        return {"id": mid, "createdAt": f"{created}T04:13:51.000Z", "tags": list(tags), "likes": 819,
                "downloads": 11658, "trendingScore": 774, "pipeline_tag": "text-generation", **kw}
    return [
        m("moonshotai/Kimi-K3.1-Pro", "2026-11-02"),                                  # original → kept
        m("AtomicChat/DeepSeek-V4.1-Flash-1017-Uncensored-GSQ-RCO-GGUF", "2026-11-03",
          ["gguf", "base_model:deepseek-ai/DeepSeek-V4.1", "base_model:quantized:deepseek-ai/DeepSeek-V4.1"]),
        m("someone/lora-thing", "2026-11-03", ["base_model:adapter:org/base"]),
        m("someone/merge-thing", "2026-11-03", ["base_model:merge:org/base"]),
        m("someone/ft-thing", "2026-11-03", ["base_model:finetune:org/base"]),
        m("acme/plain-base-tag", "2026-10-20", ["base_model:org/base"]),               # bare base_model tag → kept
        m("oldlab/Old-But-Trending", "2026-07-01"),                                    # > 120 days → dropped
        m("edge/Exactly-120", "2026-07-12"),                                           # Nov 9 − 120 d → kept
        {"id": "nodate/model", "tags": [], "likes": 1},                                # no createdAt → dropped
    ]


def _paper(aid, upvotes, title="A Paper", org="nvidia", day="2026-11-03"):
    return {"paper": {"id": aid, "title": title, "upvotes": upvotes, "publishedAt": f"{day}T00:00:00.000Z",
                      "ai_keywords": [f"kw{i}" for i in range(12)],
                      "authors": [{"name": "Jane Q. Researcher", "user": {"fullname": "Jane Q. Researcher"}}],
                      "submittedOnDailyBy": {"fullname": "Pat Submitter", "user": "patsub"},
                      "summary": "We study things."},
            "submittedBy": {"fullname": "Pat Submitter", "name": "patsub"},
            "organization": {"name": org, "fullname": "NVIDIA"} if org else None,
            "title": title}


def _fixture_papers() -> dict:
    days = {(date(2026, 11, 2) + timedelta(days=i)).isoformat(): [] for i in range(7)}
    days["2026-11-02"] = [_paper("2611.00001", 150, "Top\n  Paper"), _paper("2611.00002", 19), _paper("2611.00003", 20)]
    days["2026-11-04"] = [_paper("2611.00001", 160, "Top\n  Paper", day="2026-11-02"),     # dup across days
                          _paper("2611.00004", 55, org=None)]
    return days


class _Store:
    """An in-memory public.event keyed like the real prior-read (by source)."""
    def __init__(self):
        self.rows: list = []
        self.writes = 0

    def reader(self, sources):
        return {r["source"] for r in self.rows if r["source"] in set(sources)}

    def writer(self, rows):
        self.writes += 1
        self.rows.extend(json.loads(json.dumps(rows)))
        return len(rows)


def _fetch_fixture(url):
    if url == MODELS_URL:
        return _fixture_models()
    day = re.search(r"date=(\d{4}-\d{2}-\d{2})", url)[1]
    return _fixture_papers().get(day, [])


def selftest() -> int:
    import spine_client
    spine_client.telemetry(False)
    ok = n = 0

    def check(name, cond):
        nonlocal ok, n
        n += 1
        ok += bool(cond)
        print(f"  {'✓' if cond else '✗'} {name}")

    def no_call(*a, **k):
        raise AssertionError("must not be called")

    # --- weeks -------------------------------------------------------------------------------
    w, mon, sun = report_week(ASOF)
    check("week: Monday 2026-11-09 reports the previous ISO week 2026-W45 (Nov 2..8)",
          (w, mon, sun) == ("2026-W45", date(2026, 11, 2), date(2026, 11, 8)))
    check("week: Sunday 2026-11-08 reports 2026-W44 (its own week is not over until it ends)",
          report_week(date(2026, 11, 8))[0] == "2026-W44")
    check("week: year boundary — Monday 2027-01-04 reports 2026-W53",
          report_week(date(2027, 1, 4))[:2] == ("2026-W53", date(2026, 12, 28)))
    urls = []
    fetch_all(mon, lambda u: urls.append(u) or [])
    check("week: papers fetched for exactly the 7 days Mon..Sun of the previous week",
          [re.search(r"date=([\d-]+)", u)[1] for u in urls[1:]]
          == [(date(2026, 11, 2) + timedelta(days=i)).isoformat() for i in range(7)] and urls[0] == MODELS_URL)

    # --- models ------------------------------------------------------------------------------
    kept, mc = filter_models(_fixture_models(), ASOF)
    ids = {m["id"] for m in kept}
    check("models: quantized/adapter/merge/finetune derivatives dropped (4)",
          mc["dropped_derivative"] == 4 and not any("thing" in i or "GGUF" in i for i in ids))
    check("models: originals kept, incl. a bare base_model: tag (not a derivative marker)",
          {"moonshotai/Kimi-K3.1-Pro", "acme/plain-base-tag"} <= ids)
    check(f"models: age cutoff — older than {MAX_MODEL_AGE_DAYS} days before the run week dropped, boundary kept",
          mc["dropped_old"] == 1 and "oldlab/Old-But-Trending" not in ids and "edge/Exactly-120" in ids)
    check("models: undated model dropped and counted", mc["dropped_undated"] == 1)
    check("models: counts add up (seen = kept + every drop)",
          mc["seen"] == mc["kept"] + mc["dropped_derivative"] + mc["dropped_old"] + mc["dropped_undated"] == 9)

    # --- papers ------------------------------------------------------------------------------
    pk, pc = filter_papers(_fixture_papers())
    pids = [p["paper"]["id"] for p in pk]
    check(f"papers: upvotes >= {MIN_PAPER_UPVOTES} kept (20 in, 19 out)",
          "2611.00003" in pids and "2611.00002" not in pids and pc["below_threshold"] == 1)
    check("papers: deduped by arXiv id across days, the higher-upvote copy wins",
          pids.count("2611.00001") == 1 and pc["duplicates"] == 1
          and next(p for p in pk if p["paper"]["id"] == "2611.00001")["paper"]["upvotes"] == 160)
    big = {"2026-11-05": [_paper(f"2611.{i:05d}", 20 + i) for i in range(100, 150)]}
    bk, bc = filter_papers(big)
    check(f"papers: capped at {MAX_PAPERS_PER_WEEK} by upvotes (50 in → top 40, 10 capped)",
          len(bk) == 40 and bc["capped"] == 10 and min(p["paper"]["upvotes"] for p in bk) == 20 + 110)

    # --- rows --------------------------------------------------------------------------------
    b = build(_fixture_models(), _fixture_papers(), ASOF)
    rows = b["rows"]
    mr = next(r for r in rows if r["source"] == "hf:model:moonshotai/Kimi-K3.1-Pro")
    check("row: model mapping (launch/model_release, title=id, url, createdAt date, source key, org from id)",
          mr["kind"] == "launch" and mr["signal_type"] == "model_release" and mr["title"] == "moonshotai/Kimi-K3.1-Pro"
          and mr["url"] == "https://huggingface.co/moonshotai/Kimi-K3.1-Pro" and mr["event_date"] == "2026-11-02"
          and mr["metadata"] == {"hf_id": "moonshotai/Kimi-K3.1-Pro", "org": "moonshotai", "trending_score": 774,
                                 "likes": 819, "downloads": 11658, "pipeline_tag": "text-generation",
                                 "week": "2026-W45"})
    pr = next(r for r in rows if r["source"] == "hf:paper:2611.00001")
    check("row: paper mapping (market/paper, whitespace-normalised title, papers URL, publishedAt date)",
          pr["kind"] == "market" and pr["signal_type"] == "paper" and pr["title"] == "Top Paper"
          and pr["url"] == "https://huggingface.co/papers/2611.00001" and pr["event_date"] == "2026-11-02")
    check(f"row: paper metadata exact, keywords capped at {MAX_KEYWORDS}, org from organization.name",
          set(pr["metadata"]) == PAPER_META and len(pr["metadata"]["keywords"]) == MAX_KEYWORDS
          and pr["metadata"]["org"] == "nvidia" and pr["metadata"]["upvotes"] == 160)
    check("row: paper with no organization → org null (no invented org)",
          next(r for r in rows if r["source"] == "hf:paper:2611.00004")["metadata"]["org"] is None)
    blob = json.dumps(rows)
    check("PII: no author / submitter name or handle leaks into any row (fixture carries them)",
          not any(s in blob for s in ("Jane", "Researcher", "Pat Submitter", "patsub", "authors",
                                      "submitted", "We study")))
    check("rows: every row validates clean and stays inside spine_client.ALLOW['event']",
          rows and all(validate_row(r) == [] for r in rows))
    code, body = spine_client.write("event", rows, dry_run=True)
    check("guard: the batch passes spine_client.write(dry_run=True) — nothing sent",
          code == 0 and body["dry_run"] is True and len(body["rows"]) == len(rows))
    try:
        spine_client.write("event", [dict(rows[0], authors=["Jane Q. Researcher"])], dry_run=True)
        check("guard: an 'authors' column is refused by the spine guard (not allowlisted)", False)
    except PIIViolation:
        check("guard: an 'authors' column is refused by the spine guard (not allowlisted)", True)
    poisoned = _fixture_papers()
    poisoned["2026-11-06"] = [_paper("2611.00099", 99, title="Contact lab@example.org for weights")]
    bp = build(_fixture_models(), poisoned, ASOF)
    check("PII: a row carrying an email is refused (counted), the rest of the lane lives",
          bp["refused"] == 1 and len(bp["rows"]) == len(rows)
          and not any("2611.00099" in r["source"] for r in bp["rows"]))
    bad = dict(mr, metadata={**mr["metadata"], "likes": True})
    check("validate: a bool count is refused (type() is int, not isinstance)",
          any("must be an int" in p for p in validate_row(bad)))
    check("validate: drifted kind is refused", validate_row(dict(mr, kind="market")) != [])

    # --- gate + idempotency + failure ----------------------------------------------------------
    lanes: list = []
    rep = run(ASOF, dry_run=False, env={}, fetch=_fetch_fixture, reader=no_call, writer=no_call,
              lane_writer=lambda r: lanes.append(r))
    check(f"gate: {EVENT_WRITES_ENV} unset → zero event writes, no prior-read, items_written 0",
          rep["status"] == "success" and rep["written"] == 0 and rep["lane_run"]["items_written"] == 0)
    check("gate: lane_run still written (ledger), honest seen/refused/written",
          len(lanes) == 1 and lanes[0]["items_seen"] == 9 + 5 and lanes[0]["items_refused"] == 0
          and lanes[0]["status"] == "success" and lanes[0]["lane"] == LANE)
    rep1 = run(ASOF, dry_run=False, env={EVENT_WRITES_ENV: "1"}, fetch=_fetch_fixture, reader=no_call,
               writer=no_call, lane_writer=lambda r: None)
    check(f"gate: {EVENT_WRITES_ENV}=1 is not 'true' → still zero writes", rep1["written"] == 0)
    store = _Store()
    live = {EVENT_WRITES_ENV: "true"}
    r1 = run(ASOF, dry_run=False, env=live, fetch=_fetch_fixture, reader=store.reader, writer=store.writer,
             lane_writer=lambda r: None)
    check("live: first run writes every built row once; items_written = rows actually written",
          r1["written"] == len(rows) == len(store.rows) and r1["lane_run"]["items_written"] == len(rows))
    r2 = run(ASOF, dry_run=False, env=live, fetch=_fetch_fixture, reader=store.reader, writer=store.writer,
             lane_writer=lambda r: None)
    check("idempotency: re-running the week writes 0, duplicates nothing (keyed on source)",
          r2["written"] == 0 and r2["already_present"] == len(rows) and len(store.rows) == len(rows)
          and store.writes == 1 and len({x["source"] for x in store.rows}) == len(store.rows))
    r3 = run(ASOF + timedelta(days=7), dry_run=False, env=live, fetch=_fetch_fixture, reader=store.reader,
             writer=store.writer, lane_writer=lambda r: None)
    check("idempotency: a model still trending next week is not re-inserted",
          not any(x["source"] == "hf:model:moonshotai/Kimi-K3.1-Pro" for x in store.rows[len(rows):])
          and r3["status"] == "success")
    rd = run(ASOF, dry_run=True, env=live, fetch=_fetch_fixture, reader=no_call, writer=no_call,
             lane_writer=no_call)
    check("--dry-run: no prior-read, no event write, no lane_run — even with the live gate on",
          rd["status"] == "success" and rd["written"] == 0 and len(rd["rows"]) == len(rows))

    def boom(url):
        if "daily_papers" in url and "2026-11-05" in url:
            raise FetchError(f"{url} failed after 2 attempt(s): HTTPError: HTTP Error 503")
        return _fetch_fixture(url)
    lanes = []
    rf = run(ASOF, dry_run=False, env=live, fetch=boom, reader=no_call, writer=no_call,
             lane_writer=lambda r: lanes.append(r))
    check("fetch failure: status 'failed' with the message, zero writes, lane_run still recorded",
          rf["status"] == "failed" and "503" in rf["error"] and len(lanes) == 1
          and lanes[0]["status"] == "failed" and "503" in lanes[0]["error"] and lanes[0]["items_written"] == 0)

    def bad_reader(sources):
        raise RuntimeError("prior-read of existing sources failed: HTTP 500")
    rr = run(ASOF, dry_run=False, env=live, fetch=_fetch_fixture, reader=bad_reader, writer=no_call,
             lane_writer=lambda r: None)
    check("idempotency: a failed prior-read never falls through to a blind insert",
          rr["status"] == "failed" and rr["written"] == 0)

    # fetch_json: timeout + exactly one retry, through an injected opener
    calls = []

    def flaky(req, timeout):
        calls.append(timeout)
        if len(calls) == 1:
            raise urllib.error.URLError("timed out")
        return io.BytesIO(b'[{"id": "x"}]')
    got = fetch_json("https://example.invalid/x", opener=flaky, sleep=lambda s: None)
    check("fetch: one retry recovers a transient failure; timeout passed",
          got == [{"id": "x"}] and calls == [FETCH_TIMEOUT, FETCH_TIMEOUT])
    calls.clear()

    def dead(req, timeout):
        calls.append(1)
        raise urllib.error.URLError("connection refused")
    try:
        fetch_json("https://example.invalid/x", opener=dead, sleep=lambda s: None)
        check("fetch: two failures → FetchError (no third attempt)", False)
    except FetchError as e:
        check("fetch: two failures → FetchError (no third attempt)", len(calls) == 2 and "refused" in str(e))
    try:
        fetch_json("https://example.invalid/x", opener=lambda r, timeout: io.BytesIO(b'{"error": "x"}'),
                   sleep=lambda s: None)
        check("fetch: a non-list JSON body is a FetchError, not silently empty", False)
    except FetchError:
        check("fetch: a non-list JSON body is a FetchError, not silently empty", True)

    # --- lane_run row ----------------------------------------------------------------------------
    lr = lane_run_row("2026-11-09T05:00:00Z", "2026-11-09T05:00:09Z", "failed", 1, 0, 0, "x" * 2000)
    check("lane_run row: exact 0016 contract columns, error capped at 1000, passes the guard",
          set(lr) == ALLOW["lane_run"] - {"run_id"} and len(lr["error"]) == 1000
          and spine_client.guard("lane_run", lr) is lr)
    check("summary: counts only — no titles, ids or URLs",
          "huggingface.co" not in json.dumps(summary(r1)) and "Kimi" not in json.dumps(summary(r1)))

    # --- workflow shell lint (bash -n + heredoc pairing on every run block) ----------------------
    check("shell lint: a closed heredoc passes; an unterminated one is flagged",
          shell_script_problems("python3 - <<'EOF'\nprint(1)\nEOF\necho ok") == []
          and shell_script_problems("python3 - <<'EOF'\nprint(1)\necho ok") != [])
    wf = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                      ".github", "workflows", "hf-frontier.yml")
    if os.path.exists(wf):
        blocks = workflow_run_blocks(wf)
        probs = [f"{nm}: {p}" for nm, s in blocks for p in shell_script_problems(s)]
        check(f"shell lint: every run block in hf-frontier.yml ({len(blocks)}) passes"
              + (f" — {probs}" if probs else ""), blocks and not probs)
        text = open(wf, encoding="utf-8").read()
        check("workflow: no ${{ }} expression inside a run block (env only — runnable offline)",
              not any("${{" in s for _, s in blocks))
        check("workflow: Monday 05:00 UTC cron + workflow_dispatch, no HF token",
              'cron: "0 5 * * 1"' in text and "workflow_dispatch" in text and "HF_TOKEN" not in text)

    print(f"selftest: {ok}/{n} hf_frontier cases pass")
    return 0 if ok == n else 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dry-run", action="store_true",
                    help="fetch + build + validate + guard only: no prior-read, no event write, no lane_run")
    ap.add_argument("--asof", help="run date YYYY-MM-DD (default today, UTC); papers = the previous ISO week")
    ap.add_argument("--out", help="write the counts-only summary JSON here")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    asof = date.fromisoformat(a.asof) if a.asof else datetime.now(timezone.utc).date()
    rep = run(asof, dry_run=a.dry_run)
    s = summary(rep)
    if a.out:
        if os.path.dirname(a.out):
            os.makedirs(os.path.dirname(a.out), exist_ok=True)
        with open(a.out, "w", encoding="utf-8") as fh:
            json.dump(s, fh, indent=1)
            fh.write("\n")
    m, p = rep.get("models") or {}, rep.get("papers") or {}
    print(f"hf_frontier: week {rep['week']} (papers {rep['papers_window']}) · mode: {rep['mode']}")
    print(f"  models  seen {m.get('seen', 0)} · kept {m.get('kept', 0)} · dropped derivative "
          f"{m.get('dropped_derivative', 0)} · dropped old {m.get('dropped_old', 0)} · dropped undated "
          f"{m.get('dropped_undated', 0)}")
    print(f"  papers  seen {p.get('seen', 0)} · kept {p.get('kept', 0)} · below {MIN_PAPER_UPVOTES} upvotes "
          f"{p.get('below_threshold', 0)} · duplicates {p.get('duplicates', 0)} · capped {p.get('capped', 0)}")
    print(f"  events  built {len(rep['rows'])} · refused {rep['refused']} · written {rep['written']}"
          + (f" · already present {rep['already_present']}" if rep["already_present"] is not None else ""))
    print(f"  lane_run {'not written (--dry-run)' if a.dry_run else 'written to PROD'} · status {rep['status']}"
          + (f" · error: {rep['error']}" if rep["error"] else ""))
    return 0 if rep["status"] == "success" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
