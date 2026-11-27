#!/usr/bin/env python3
"""council: Claude and Gemini answer the same brief, then answer each other, verbatim (YED-517).

Nothing passes through the orchestrating session. Every turn is written word for word to
`.claude/.state/alt/council-<id>/transcript.md` as it arrives, with the raw JSON beside it and a sha256 per turn in
manifest.json, so Alex reads both voices directly (`tail -f` the transcript while it runs).

  python3 .claude/scripts/council.py start BRIEF.md [--rounds 2] [--claude-model fable] [--gemini-model gemini-4-neon-high]
  python3 .claude/scripts/council.py say RUN_DIR "Alex's message"   (both models answer Alex, and see each other's reply next round)
  python3 .claude/scripts/council.py round RUN_DIR                   (one more exchange: each answers the other's last turn)
  python3 .claude/scripts/council.py verify RUN_DIR                  (re-hash every turn against the manifest)

Round 0: both answer the brief blind. Each later round: each model gets the other's previous turn verbatim and
responds to it, then gives its updated position. Both are asked to speak in their own voice and to disagree where
they disagree. Neither model is a judge of the other's survival.

Privacy: the brief, every Claude turn bound for Gemini, and every Alex message pass the second_opinion gate
(public-only, fail closed). A refused turn stops the council and says why in the transcript. Gemini runs via
`agy` sandboxed in an empty folder; Claude runs via `claude -p` with no tools and no MCP servers in another
empty folder. Both run on subscriptions; nothing here bills per token.
"""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import second_opinion as so  # noqa: E402

FRAME = {
    "claude": "You are Claude, in a two-model council with Gemini (Google). Alex, the operator, reads both of you "
              "verbatim. Speak in your own voice, be concrete, and disagree where you disagree. Do not defer to "
              "Gemini to be polite, and do not dismiss it to protect your own answer.",
    "gemini": "You are Gemini, in a two-model council with Claude (Anthropic). Alex, the operator, reads both of you "
              "verbatim. Speak in your own voice, be concrete, and disagree where you disagree. Do not defer to "
              "Claude to be polite, and do not dismiss it to protect your own answer.",
}
REPLY = ("{other} said, verbatim:\n\n<<<\n{text}\n>>>\n\nRespond to it directly: what it got right that you missed, "
         "where you think it is wrong and why, and what you would change. Then give your updated proposal.")


def now() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class Council:
    def __init__(self, run: str):
        self.run = run
        self.state_path = os.path.join(run, "state.json")
        self.state = json.load(open(self.state_path)) if os.path.exists(self.state_path) else {}

    def save(self):
        json.dump(self.state, open(self.state_path, "w"), indent=1)

    def log(self, md: str):
        with open(os.path.join(self.run, "transcript.md"), "a", encoding="utf-8") as f:
            f.write(md)

    def record(self, speaker: str, text: str, raw: dict, label: str):
        n = len(self.state["turns"])
        raw_path = os.path.join(self.run, "turns", f"{n:02d}-{speaker}.json")
        json.dump(raw, open(raw_path, "w"), ensure_ascii=False, indent=1)
        sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
        self.state["turns"].append({"n": n, "speaker": speaker, "label": label, "at": now(), "sha256": sha,
                                    "raw": os.path.relpath(raw_path, self.run), "text": text})
        self.save()
        name = {"claude": f"Claude ({self.state['claude_model']})", "gemini": f"Gemini ({self.state['gemini_model']})",
                "alex": "Alex"}[speaker]
        self.log(f"\n### {name} · {label} · {now()}\n\n{text}\n")

    # model calls -------------------------------------------------------------
    def gemini(self, prompt: str) -> tuple[str, dict]:
        so.gate("visibility: public\n" + prompt)
        d = so.run_agy(prompt, model=self.state["gemini_model"], conversation=self.state.get("gemini_conv"),
                       timeout_s=900, workdir=os.path.join(self.run, "cwd-gemini"))
        self.state["gemini_conv"] = d.get("conversation_id") or self.state.get("gemini_conv")
        return d.get("response", ""), d

    def claude(self, prompt: str) -> tuple[str, dict]:
        cmd = ["claude", "-p", prompt, "--model", self.state["claude_model"], "--output-format", "json",
               "--tools", "", "--strict-mcp-config", "--append-system-prompt", FRAME["claude"]]
        if self.state.get("claude_session"):
            cmd += ["--resume", self.state["claude_session"]]
        p = subprocess.run(cmd, cwd=os.path.join(self.run, "cwd-claude"), capture_output=True, text=True,
                           timeout=1200)
        try:
            d = json.loads(p.stdout)
        except json.JSONDecodeError:
            raise SystemExit(f"claude -p returned no JSON (exit {p.returncode}): {p.stderr.strip()[:400]}")
        if d.get("is_error"):
            raise SystemExit(f"claude -p error: {json.dumps(d)[:400]}")
        self.state["claude_session"] = d.get("session_id") or self.state.get("claude_session")
        return d.get("result", ""), d

    # steps ---------------------------------------------------------------------
    def last(self, speaker: str) -> str:
        return next(t["text"] for t in reversed(self.state["turns"]) if t["speaker"] == speaker)

    def exchange(self, label: str, claude_prompt: str, gemini_prompt: str):
        try:
            g_text, g_raw = self.gemini(gemini_prompt)
        except so.Refused as e:
            self.log(f"\n> **Stopped:** the prompt for Gemini was refused by the public-only gate ({e}).\n")
            raise
        c_text, c_raw = self.claude(claude_prompt)
        self.record("gemini", g_text, g_raw, label)
        self.record("claude", c_text, c_raw, label)

    def round(self):
        k = sum(1 for t in self.state["turns"] if t["speaker"] == "gemini")
        c_prev, g_prev = self.last("claude"), self.last("gemini")
        self.exchange(f"round {k}",
                      REPLY.format(other="Gemini", text=g_prev),
                      REPLY.format(other="Claude", text=c_prev))


def start(brief: str, rounds: int, claude_model: str, gemini_model: str) -> str:
    text = open(brief, encoding="utf-8").read()
    so.gate(text)
    body = text.split("\n", 1)[1]
    run = os.path.join(so.ALT_DIR, "council-" + dt.datetime.now().strftime("%Y%m%d-%H%M%S"))
    for d in ("turns", "cwd-claude", "cwd-gemini"):
        os.makedirs(os.path.join(run, d), exist_ok=True)
    open(os.path.join(run, "brief.md"), "w", encoding="utf-8").write(text)
    c = Council(run)
    c.state = {"brief": "brief.md", "claude_model": claude_model, "gemini_model": gemini_model, "turns": []}
    c.save()
    c.log(f"# Council transcript\n\nBrief: `brief.md` · Claude: {claude_model} · Gemini: {gemini_model} · "
          f"started {now()}\n\nEvery turn below is verbatim model output. Hashes: manifest.json.\n\n## Brief\n\n"
          f"{body}\n\n---\n")
    print(run, flush=True)
    c.exchange("round 0 (blind)", body, FRAME["gemini"] + "\n\n" + body)
    for _ in range(rounds):
        c.round()
    write_manifest(c)
    return run


def say(run: str, message: str):
    c = Council(run)
    so.gate("visibility: public\n" + message)
    c.record("alex", message, {"from": "alex"}, "message")
    prompt = f"Alex says:\n\n<<<\n{message}\n>>>\n\nAnswer Alex directly."
    c.exchange("reply to Alex", prompt, prompt)
    write_manifest(c)


def write_manifest(c: Council):
    m = [{k: t[k] for k in ("n", "speaker", "label", "at", "sha256", "raw")} for t in c.state["turns"]]
    json.dump(m, open(os.path.join(c.run, "manifest.json"), "w"), indent=1)


def verify(run: str) -> bool:
    c = Council(run)
    ok = True
    for t in c.state["turns"]:
        raw = json.load(open(os.path.join(run, t["raw"])))
        src = raw.get("response") if t["speaker"] == "gemini" else raw.get("result") if t["speaker"] == "claude" \
            else t["text"]
        good = hashlib.sha256((src or "").encode("utf-8")).hexdigest() == t["sha256"] and src == t["text"]
        ok &= good
        print(("ok  " if good else "FAIL"), t["n"], t["speaker"], t["label"])
    return ok


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("start"); s.add_argument("brief"); s.add_argument("--rounds", type=int, default=2)
    s.add_argument("--claude-model", default="fable"); s.add_argument("--gemini-model", default=so.DEFAULT_MODEL)
    y = sub.add_parser("say"); y.add_argument("run"); y.add_argument("message")
    r = sub.add_parser("round"); r.add_argument("run")
    v = sub.add_parser("verify"); v.add_argument("run")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "start":
            run = start(a.brief, a.rounds, a.claude_model, a.gemini_model)
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
