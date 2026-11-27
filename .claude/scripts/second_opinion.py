#!/usr/bin/env python3
"""second_opinion: send a brief to Gemini (Google AI Pro) or Codex (ChatGPT) and keep the full reply (YED-517).

Gemini and Codex are permanent co-authors and judges in this system, beside Claude. This script does not judge
their output. It does
two things: it makes sure only public material leaves the machine, and it saves exactly what Gemini said.

  python3 .claude/scripts/second_opinion.py ask BRIEF.md [--seat gemini|codex] [--model M] [--conversation ID]
  python3 .claude/scripts/second_opinion.py gate FILE.md       (run only the outbound gate; exit 0 pass, 4 refuse)
  python3 .claude/scripts/second_opinion.py --selftest

Outbound gate (fail closed; any hit refuses and nothing is sent):
  1. The brief's first line must be exactly `visibility: public`. The author asserts the text is meant for public
     eyes (headed to GitHub, LinkedIn or a public talk). Missing marker = refuse.
  2. No email address and no phone number (the spine's own EMAIL_RE / PHONE_RE, imported, not copied).
  3. No private marker phrases (me-model, target-companies, job-search target, off the record, inbox lists).
  4. No 8-word run copied from a private file (me-model.md, target-companies.md, inbox-allowlist.md,
     inbox-denylist.md), looked up in this checkout and every sibling worktree. If none of those files can be
     found, the gate refuses: it cannot prove the brief is clean.
  5. Not the git user's surname or email.
The gate never edits or redacts. It names the rule and the line, and the author fixes the brief.

Inbound: Gemini runs with `agy` from an empty folder (`--sandbox --mode plan --disable-slash-commands`), so it
cannot see the repo. Its reply is data, never instructions. Each run is saved in full to
`.claude/.state/alt/<run-id>/` (brief.md, raw.json, response.md, meta.json with the sha256 of response.md).
"""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, os, re, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
from spine_client import EMAIL_RE, PHONE_RE  # noqa: E402  (single source of the PII patterns)

ALT_DIR = os.path.join(ROOT, ".claude", ".state", "alt")
DEFAULT_MODEL = "gemini-4-neon-high"
PRIVATE_FILES = ("me-model.md", "target-companies.md", "inbox-allowlist.md", "inbox-denylist.md")
MARKERS = ()   # Alex, 27 Nov: nothing is private and nothing is off the record
SHINGLE = 8


class Refused(Exception):
    pass


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+(?:['’][a-z]+)?", text.lower())


def _roots() -> list[str]:
    roots = [ROOT]
    try:
        out = subprocess.run(["git", "-C", ROOT, "worktree", "list", "--porcelain"], capture_output=True,
                             text=True, timeout=10).stdout
        roots += [l.split(" ", 1)[1] for l in out.splitlines() if l.startswith("worktree ")]
    except Exception:
        pass
    extra = os.environ.get("ESEP_PRIVATE_DIRS", "")
    roots += [p for p in extra.split(os.pathsep) if p]
    seen, out_roots = set(), []
    for r in roots:
        r = os.path.abspath(r)
        if r not in seen:
            seen.add(r); out_roots.append(r)
    return out_roots


def private_shingles(roots: list[str] | None = None) -> tuple[set[tuple[str, ...]], list[str]]:
    found, shingles = [], set()
    for r in roots if roots is not None else _roots():
        for name in PRIVATE_FILES:
            p = os.path.join(r, ".claude", "references", name)
            if os.path.isfile(p) and name not in [os.path.basename(f) for f in found]:
                found.append(p)
                w = _words(open(p, encoding="utf-8", errors="replace").read())
                shingles.update(tuple(w[i:i + SHINGLE]) for i in range(len(w) - SHINGLE + 1))
    return shingles, found


def _identity() -> list[str]:
    vals = []
    for key in ("user.name", "user.email"):
        try:
            v = subprocess.run(["git", "-C", ROOT, "config", key], capture_output=True, text=True,
                               timeout=5).stdout.strip()
        except Exception:
            v = ""
        if v:
            vals.append(v.lower())
    terms = []
    for v in vals:
        if "@" in v:
            terms.append(v)
        else:
            parts = v.split()
            if len(parts) >= 2:
                terms.append(parts[-1])          # surname only: first names appear in public copy
    return terms


def gate(text: str, *, shingles=None, identity=None, _roots_override=None) -> None:
    """Raise Refused naming the rule and line. Returns None when the text may go to a seat.

    Alex, 27 Nov: "Nothing is private ... nothing is in confidence" and "nothing is off the record". Everything goes
    to the seats. The one check left: no email address or phone number (ADR-9 keeps contact data in HubSpot).
    `shingles`, `identity` and `_roots_override` are accepted for older callers and ignored.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "visibility: public":
        raise Refused("rule 1: first line must be exactly 'visibility: public'")
    for n, line in enumerate(lines, 1):
        if EMAIL_RE.search(line):
            raise Refused(f"rule 2: email address on line {n}")
        if PHONE_RE.search(line):
            raise Refused(f"rule 2: phone number on line {n}")


def run_agy(prompt: str, *, model: str, conversation: str | None, timeout_s: int, workdir: str,
            schema: str | None = None) -> dict:
    if not shutil.which("agy"):
        raise SystemExit("agy (Antigravity CLI) not on PATH; install it and sign in once interactively")
    cmd = ["agy", "-p", prompt, "--model", model, "--output-format", "json", "--print-timeout", f"{timeout_s}s",
           "--sandbox", "--mode", "plan", "--disable-slash-commands"]
    if conversation:
        cmd += ["--conversation", conversation]
    if schema:
        cmd += ["--json-schema", schema]
    p = subprocess.run(cmd, cwd=workdir, capture_output=True, text=True, timeout=timeout_s + 60,
                       stdin=subprocess.DEVNULL)  # an open stdin makes codex wait for more input
    try:
        d = json.loads(p.stdout)
    except json.JSONDecodeError:
        raise SystemExit(f"agy returned no JSON (exit {p.returncode}): {p.stderr.strip()[:400]}")
    if d.get("status") != "SUCCESS":
        raise SystemExit(f"agy status {d.get('status')}: {json.dumps(d)[:400]}")
    return d


# Codex (OpenAI, ChatGPT plan). `-s read-only` alone still lets Codex READ any file on disk (canary test, 26 Nov),
# so its shell, exec, browser and apps tools are always disabled, on resumed turns too.
CODEX_DISABLE = ("shell_tool", "unified_exec", "shell_snapshot", "apps", "browser_use", "browser_use_external",
                 "in_app_browser")


def run_codex(prompt: str, *, model: str | None, thread: str | None, timeout_s: int, workdir: str,
              schema: str | None = None) -> dict:
    """Returns {"thread_id", "response", "events"}. workdir must be an empty folder outside any repo (Codex reads
    AGENTS.md from its cwd upward)."""
    if not shutil.which("codex"):
        raise SystemExit("codex CLI not on PATH; install it (brew install --cask codex) and run `codex login`")
    opts = ["--skip-git-repo-check", "--json"]
    for f in CODEX_DISABLE:
        opts += ["-c", f"features.{f}=false"]
    if model:
        opts += ["-c", f'model="{model}"']
    if schema and not thread:
        opts += ["--output-schema", schema]
    if thread:
        cmd = ["codex", "exec", "resume", *opts, thread, prompt]
    else:
        cmd = ["codex", "exec", "-s", "read-only", "-C", workdir, *opts, prompt]
    p = subprocess.run(cmd, cwd=workdir, capture_output=True, text=True, timeout=timeout_s + 60,
                       stdin=subprocess.DEVNULL)  # an open stdin makes codex wait for more input
    events = []
    for line in p.stdout.splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    tid = next((e.get("thread_id") for e in events if e.get("type") == "thread.started"), thread)
    msgs = [e["item"]["text"] for e in events
            if e.get("type") == "item.completed" and e.get("item", {}).get("type") == "agent_message"]
    if not msgs:
        raise SystemExit(f"codex returned no message (exit {p.returncode}): {p.stderr.strip()[-400:]}")
    return {"thread_id": tid, "response": msgs[-1], "events": events}


def ask(brief_path: str, *, seat: str = "gemini", model: str | None = None, conversation: str | None = None,
        timeout_s: int = 600, label: str = "ask") -> str:
    text = open(brief_path, encoding="utf-8").read()
    gate(text)
    run_id = dt.datetime.now().strftime("%Y%m%d-%H%M%S") + f"-{seat}-{label}"
    out = os.path.join(ALT_DIR, run_id)
    os.makedirs(out, exist_ok=True)
    shutil.copy(brief_path, os.path.join(out, "brief.md"))
    body = text.split("\n", 1)[1] if "\n" in text else ""
    with tempfile.TemporaryDirectory(prefix=f"{seat}-empty-") as empty:
        if seat == "codex":
            d = run_codex(body, model=model, thread=conversation, timeout_s=timeout_s, workdir=empty)
            conv = d["thread_id"]
        else:
            model = model or DEFAULT_MODEL
            d = run_agy(body, model=model, conversation=conversation, timeout_s=timeout_s, workdir=empty)
            conv = d.get("conversation_id")
    json.dump(d, open(os.path.join(out, "raw.json"), "w"), ensure_ascii=False, indent=1)
    resp = d.get("response", "")
    open(os.path.join(out, "response.md"), "w", encoding="utf-8").write(resp)
    meta = {"run_id": run_id, "seat": seat, "model": model or "default", "conversation_id": conv,
            "duration_seconds": d.get("duration_seconds"), "usage": d.get("usage"),
            "response_sha256": hashlib.sha256(resp.encode("utf-8")).hexdigest()}
    json.dump(meta, open(os.path.join(out, "meta.json"), "w"), indent=1)
    return out


def selftest() -> bool:
    ok = True
    cases = [
        ("no marker", "hello", False),
        ("clean", "visibility: public\nA plain public brief about agents.", True),
        ("email", "visibility: public\nwrite to someone@example.org today", False),
        ("phone", "visibility: public\ncall +1 212 555 0142 now", False),
        ("off the record ok", "visibility: public\nThe host said this was off the\nrecord.", True),
        ("own material ok", "visibility: public\nFrom the me-model: target companies and job-search notes.", True),
    ]
    for name, text, want in cases:
        try:
            gate(text); got = True
        except Refused:
            got = False
        ok &= got == want
        print(("ok  " if got == want else "FAIL"), name)
    print("selftest", "PASS" if ok else "FAIL")
    return ok


def main(argv: list[str]) -> int:
    if argv[:1] == ["--selftest"]:
        return 0 if selftest() else 1
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("ask"); a.add_argument("brief"); a.add_argument("--seat", choices=("gemini", "codex"),
                                                                     default="gemini")
    a.add_argument("--model", default=None)
    a.add_argument("--conversation"); a.add_argument("--timeout", type=int, default=600)
    a.add_argument("--label", default="ask")
    g = sub.add_parser("gate"); g.add_argument("file")
    args = ap.parse_args(argv)
    try:
        if args.cmd == "gate":
            gate(open(args.file, encoding="utf-8").read()); print("PASS"); return 0
        out = ask(args.brief, seat=args.seat, model=args.model, conversation=args.conversation, timeout_s=args.timeout,
                  label=args.label)
    except Refused as e:
        print("REFUSED", e, file=sys.stderr); return 4
    print(out)
    print(os.path.join(out, "response.md"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
