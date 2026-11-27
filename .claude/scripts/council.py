#!/usr/bin/env python3
"""council: Claude, Gemini and Codex answer the same brief, then answer each other, verbatim (YED-517).

Nothing passes through the orchestrating session. Every turn is written word for word to
`.claude/.state/alt/council-<id>/transcript.md` as it arrives, with the raw JSON beside it and a sha256 per turn in
manifest.json, so Alex reads every voice directly (`tail -f` the transcript while it runs).

  python3 .claude/scripts/council.py start BRIEF.md [--rounds 2] [--seats gemini,claude,codex]
                                     [--claude-model fable] [--gemini-model gemini-4-neon-high] [--codex-model M]
  python3 .claude/scripts/council.py say RUN_DIR "Alex's message"   (every seat answers Alex)
  python3 .claude/scripts/council.py round RUN_DIR                   (one more exchange: each answers the others' last turns)
  python3 .claude/scripts/council.py verify RUN_DIR                  (re-hash every turn against the manifest)

Round 0: every seat answers the brief blind. Each later round: each model gets every other seat's previous turn
verbatim and responds to it, then gives its updated position. Each is asked to speak in its own voice and
to disagree where it disagrees. No seat judges another's survival.

Privacy: the brief, every prompt bound for a non-Anthropic model (it carries the other seats' text), and every Alex
message pass the second_opinion gate (public-only, fail closed). A refused turn stops the council and says why in
the transcript. No seat can read local files (canary-tested 26 Nov):
  * Gemini: `agy` headless, sandboxed, empty folder; file reads are auto-denied (recorded as denied_actions).
  * Codex: `codex exec`, read-only sandbox, empty folder, with the shell, exec, browser and apps tools DISABLED.
    Its read-only sandbox alone still lets it read any file on disk, so the disables are mandatory.
  * Claude: `claude -p` with no tools and no MCP servers.
All three run on subscriptions (Google AI Pro, ChatGPT, Claude); nothing here bills per token.
"""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import second_opinion as so  # noqa: E402

SEATS = ("gemini", "claude", "codex")
PEERS = {"claude": "Claude (Anthropic)", "gemini": "Gemini (Google)", "codex": "Codex (OpenAI)"}
CODEX_DISABLE = ("shell_tool", "unified_exec", "shell_snapshot", "apps", "browser_use", "browser_use_external",
                 "in_app_browser")
REPLY = ("The other council members said, verbatim:\n\n{blocks}\n\nRespond to each directly: what they got right "
         "that you missed, where you think they are wrong and why, and what you would change. Then give your updated "
         "proposal.")


def frame(seat: str, seats: list[str]) -> str:
    others = " and ".join(PEERS[x] for x in seats if x != seat)
    return (f"You are {PEERS[seat]}, in a council with {others}. Alex, the operator, reads every one of you "
            "verbatim. Speak in your own voice, be concrete, and disagree where you disagree. Do not defer to the "
            "others to be polite, and do not dismiss them to protect your own answer.")


def now() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class Council:
    def __init__(self, run: str):
        self.run = run
        self.state_path = os.path.join(run, "state.json")
        self.state = json.load(open(self.state_path)) if os.path.exists(self.state_path) else {}

    @property
    def seats(self) -> list[str]:
        return self.state.get("seats", ["gemini", "claude"])

    def save(self):
        json.dump(self.state, open(self.state_path, "w"), indent=1)

    def log(self, md: str):
        with open(os.path.join(self.run, "transcript.md"), "a", encoding="utf-8") as f:
            f.write(md)

    def cwd(self, seat: str) -> str:
        """An empty folder OUTSIDE any repo. Claude Code reads every CLAUDE.md above its cwd and Codex reads
        AGENTS.md the same way, so a folder inside this repo hands them repo context the brief never gave
        (found 26 Nov: the council's Claude quoted the repo CLAUDE.md). Persisted so resumed sessions match."""
        d = self.state.setdefault("cwds", {}).get(seat)
        if not d or not os.path.isdir(d):
            d = tempfile.mkdtemp(prefix=f"council-{seat}-")
            self.state["cwds"][seat] = d
            self.save()
        return d

    def name(self, speaker: str) -> str:
        if speaker == "alex":
            return "Alex"
        model = self.state.get(f"{speaker}_model") or "default"
        return f"{PEERS[speaker].split(' ')[0]} ({model})"

    def record(self, speaker: str, text: str, raw, label: str):
        n = len(self.state["turns"])
        raw_path = os.path.join(self.run, "turns", f"{n:02d}-{speaker}.json")
        json.dump(raw, open(raw_path, "w"), ensure_ascii=False, indent=1)
        sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
        self.state["turns"].append({"n": n, "speaker": speaker, "label": label, "at": now(), "sha256": sha,
                                    "raw": os.path.relpath(raw_path, self.run), "text": text})
        self.save()
        self.log(f"\n### {self.name(speaker)} · {label} · {now()}\n\n{text}\n")

    # model calls -------------------------------------------------------------
    def call(self, seat: str, prompt: str):
        if seat != "claude":                       # leaves Anthropic: public-only gate on the exact prompt
            so.gate("visibility: public\n" + prompt)
        return getattr(self, "_" + seat)(prompt)

    def _gemini(self, prompt: str):
        d = so.run_agy(prompt, model=self.state["gemini_model"], conversation=self.state.get("gemini_conv"),
                       timeout_s=900, workdir=self.cwd("gemini"))
        self.state["gemini_conv"] = d.get("conversation_id") or self.state.get("gemini_conv")
        return d.get("response", ""), d

    def _claude(self, prompt: str):
        cmd = ["claude", "-p", prompt, "--model", self.state["claude_model"], "--output-format", "json",
               "--tools", "", "--strict-mcp-config", "--append-system-prompt", frame("claude", self.seats)]
        if self.state.get("claude_session"):
            cmd += ["--resume", self.state["claude_session"]]
        p = subprocess.run(cmd, cwd=self.cwd("claude"), capture_output=True, text=True,
                           timeout=1200)
        try:
            d = json.loads(p.stdout)
        except json.JSONDecodeError:
            raise SystemExit(f"claude -p returned no JSON (exit {p.returncode}): {p.stderr.strip()[:400]}")
        if d.get("is_error"):
            raise SystemExit(f"claude -p error: {json.dumps(d)[:400]}")
        self.state["claude_session"] = d.get("session_id") or self.state.get("claude_session")
        return d.get("result", ""), d

    def _codex(self, prompt: str):
        cwd = self.cwd("codex")
        opts = ["--skip-git-repo-check", "--json"]
        for f in CODEX_DISABLE:
            opts += ["-c", f"features.{f}=false"]
        if self.state.get("codex_model"):
            opts += ["-c", f'model="{self.state["codex_model"]}"']
        if self.state.get("codex_thread"):
            cmd = ["codex", "exec", "resume", *opts, self.state["codex_thread"], prompt]
        else:
            cmd = ["codex", "exec", "-s", "read-only", "-C", cwd, *opts, prompt]
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=1200)
        events = []
        for line in p.stdout.splitlines():
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                pass
        for e in events:
            if e.get("type") == "thread.started":
                self.state["codex_thread"] = e.get("thread_id")
        msgs = [e["item"]["text"] for e in events
                if e.get("type") == "item.completed" and e.get("item", {}).get("type") == "agent_message"]
        if not msgs:
            raise SystemExit(f"codex returned no message (exit {p.returncode}): {p.stderr.strip()[-400:]}")
        return msgs[-1], {"events": events, "result": msgs[-1]}

    # steps ---------------------------------------------------------------------
    def last(self, speaker: str) -> str:
        return next(t["text"] for t in reversed(self.state["turns"]) if t["speaker"] == speaker)

    def exchange(self, label: str, prompts: dict):
        out = {}
        for seat in self.seats:                    # every call finishes before anything is written: same footing
            try:
                out[seat] = self.call(seat, prompts[seat])
            except so.Refused as e:
                self.log(f"\n> **Stopped:** the prompt for {PEERS[seat]} was refused by the public-only gate ({e}).\n")
                raise
        for seat in self.seats:
            self.record(seat, out[seat][0], out[seat][1], label)
        self.save()

    def round(self):
        k = sum(1 for t in self.state["turns"] if t["speaker"] == self.seats[0])
        prev = {s: self.last(s) for s in self.seats}
        prompts = {}
        for seat in self.seats:
            blocks = "\n\n".join(f"{PEERS[o]}:\n<<<\n{prev[o]}\n>>>" for o in self.seats if o != seat)
            prompts[seat] = REPLY.format(blocks=blocks)
        self.exchange(f"round {k}", prompts)


def start(brief: str, rounds: int, seats: list[str], models: dict) -> str:
    text = open(brief, encoding="utf-8").read()
    so.gate(text)
    body = text.split("\n", 1)[1]
    run = os.path.join(so.ALT_DIR, "council-" + dt.datetime.now().strftime("%Y%m%d-%H%M%S"))
    os.makedirs(os.path.join(run, "turns"), exist_ok=True)
    open(os.path.join(run, "brief.md"), "w", encoding="utf-8").write(text)
    c = Council(run)
    c.state = {"brief": "brief.md", "seats": seats, "turns": [], **{f"{k}_model": v for k, v in models.items()}}
    c.save()
    c.log(f"# Council transcript\n\nBrief: `brief.md` · seats: {', '.join(c.name(s) for s in seats)} · started "
          f"{now()}\n\nEvery turn below is verbatim model output. Hashes: manifest.json.\n\n## Brief\n\n{body}\n\n---\n")
    print(run, flush=True)
    c.exchange("round 0 (blind)", {s: (body if s == "claude" else frame(s, seats) + "\n\n" + body) for s in seats})
    for _ in range(rounds):
        c.round()
    write_manifest(c)
    return run


def say(run: str, message: str):
    c = Council(run)
    so.gate("visibility: public\n" + message)
    c.record("alex", message, {"from": "alex"}, "message")
    prompt = f"Alex says:\n\n<<<\n{message}\n>>>\n\nAnswer Alex directly."
    c.exchange("reply to Alex", {s: prompt for s in c.seats})
    write_manifest(c)


def write_manifest(c: Council):
    m = [{k: t[k] for k in ("n", "speaker", "label", "at", "sha256", "raw")} for t in c.state["turns"]]
    json.dump(m, open(os.path.join(c.run, "manifest.json"), "w"), indent=1)


def verify(run: str) -> bool:
    c = Council(run)
    ok = True
    for t in c.state["turns"]:
        raw = json.load(open(os.path.join(run, t["raw"])))
        src = {"gemini": raw.get("response"), "claude": raw.get("result"), "codex": raw.get("result")}.get(
            t["speaker"], t["text"])
        good = hashlib.sha256((src or "").encode("utf-8")).hexdigest() == t["sha256"] and src == t["text"]
        ok &= good
        print(("ok  " if good else "FAIL"), t["n"], t["speaker"], t["label"])
    return ok


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("start"); s.add_argument("brief"); s.add_argument("--rounds", type=int, default=2)
    s.add_argument("--seats", default=",".join(SEATS))
    s.add_argument("--claude-model", default="fable"); s.add_argument("--gemini-model", default=so.DEFAULT_MODEL)
    s.add_argument("--codex-model", default=None)
    y = sub.add_parser("say"); y.add_argument("run"); y.add_argument("message")
    r = sub.add_parser("round"); r.add_argument("run")
    v = sub.add_parser("verify"); v.add_argument("run")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "start":
            seats = [x.strip() for x in a.seats.split(",") if x.strip()]
            bad = [x for x in seats if x not in SEATS]
            if bad or len(seats) < 2:
                raise SystemExit(f"--seats needs 2+ of {SEATS}; got {seats}")
            models = {"claude": a.claude_model, "gemini": a.gemini_model, "codex": a.codex_model}
            run = start(a.brief, a.rounds, seats, {k: v for k, v in models.items() if k in seats})
            print(os.path.join(run, "transcript.md"))
        elif a.cmd == "say":
            say(a.run, a.message)
        elif a.cmd == "round":
            c = Council(a.run); c.round(); write_manifest(c)
        else:
            return 0 if verify(a.run) else 1
    except so.Refused as e:
        print("REFUSED", e, file=sys.stderr); return 4
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
