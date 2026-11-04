#!/usr/bin/env python3
"""Regression selftest for the .gitleaks.toml allowlist (YED-304).

The allowlist must be VALUE-scoped: sha256 digests of public *.example URLs
(feeds.item_key) under supabase/fixtures/ pass, while a planted credential in
the same directory is still flagged. Both halves are proven in a throwaway git
repo scanned with gitleaks in git mode — the same mode CI's secret-scan
workflow uses.

History note (2026-11-04): the paths-only exact-file form used briefly in PR
#270 (368cc0e) exempts the WHOLE file, so a real credential pasted into an
exempted fixture would pass the scanner. This selftest pins the correct
behavior: if anyone flips the config back to paths-only, this test fails.

Requires the gitleaks binary (CI: 8.30.1, installed by secret-scan.yml).
Resolve it via GITLEAKS_BIN or PATH; if absent the test FAILS with setup
instructions rather than skipping silently.

Run:  GITLEAKS_BIN=/tmp/gitleaks python3 .claude/scripts/test_gitleaks_allowlist.py
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG = REPO_ROOT / ".gitleaks.toml"

# The sentinel token is built at runtime so this file's source never contains a
# literal sk_live_ string — the range scanner flags literals (CI failure at ce59680).
PLANTED_TOKEN = "sk_live_" + hashlib.sha256(b"allowlist-selftest").hexdigest()[:32]
DIGEST = hashlib.sha256("https://veris.example/blog/atlas-2".encode()).hexdigest()


def find_gitleaks() -> str:
    candidate = os.environ.get("GITLEAKS_BIN") or shutil.which("gitleaks")
    if not candidate:
        sys.exit(
            "FAIL: gitleaks binary not found. Set GITLEAKS_BIN=/path/to/gitleaks "
            "(CI installs 8.30.1 to /tmp/gitleaks) or put gitleaks on PATH."
        )
    return candidate


def run_git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), *args], check=True,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


def scan(gitleaks: str, report: Path, repo: Path) -> list[dict]:
    """Scan the scratch repo's full history; return gitleaks findings as JSON."""
    subprocess.run(
        [gitleaks, "git", "--no-banner", "--report-format", "json",
         "--report-path", str(report), str(repo)],
        check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    if not report.exists():  # no leaks found -> gitleaks writes no report file
        return []
    parsed = json.loads(report.read_text())
    return parsed.get("leaks", []) if isinstance(parsed, dict) else parsed


def build_scratch_repo(base: Path, with_token: bool) -> Path:
    """Mirror Alex's probe matrix on #272: a digest fixture, optionally a planted
    token, in a single-commit scratch repo. The clean-tree case is a repo that
    never contained the token — git mode scans history, so removing a file is not
    the same as never having committed it."""
    repo = base / ("probe-token" if with_token else "probe-clean")
    (repo / "supabase" / "fixtures").mkdir(parents=True)
    shutil.copy(CONFIG, repo / ".gitleaks.toml")
    (repo / "supabase" / "fixtures" / "digest.json").write_text(
        json.dumps({"source_key": DIGEST}) + "\n"
    )
    if with_token:
        (repo / "supabase" / "fixtures" / "probe.json").write_text(
            json.dumps({"api_key": PLANTED_TOKEN}) + "\n"
        )
    run_git(repo, "init", "-q")
    # CI runners have no git identity; the probe repo needs one to commit.
    run_git(repo, "config", "user.name", "gitleaks-selftest")
    run_git(repo, "config", "user.email", "selftest@example.invalid")
    run_git(repo, "add", "-A")
    run_git(repo, "commit", "-qm", "probe: allowlist selftest scratch repo")
    return repo


def main() -> int:
    gitleaks = find_gitleaks()
    failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix="gitleaks-allowlist-probe-") as tmp:
        base = Path(tmp)
        report = base / "report.json"  # outside the probe repos on purpose

        planted = scan(gitleaks, report, build_scratch_repo(base, with_token=True))
        planted_secrets = {f.get("Secret") for f in planted}
        if PLANTED_TOKEN in planted_secrets:
            print("PASS  planted sk_live_ token in supabase/fixtures/ is flagged")
        else:
            failures.append(
                f"planted token was NOT flagged (findings: {sorted(planted_secrets)}) — "
                "the allowlist is exempting whole files or paths unconditionally"
            )
        if DIGEST not in planted_secrets:
            print("PASS  sha256 digest of a public *.example URL is exempt")
        else:
            failures.append("digest was flagged — value-scoping too narrow")

        clean = scan(gitleaks, report, build_scratch_repo(base, with_token=False))
        if not clean:
            print("PASS  clean tree (digest fixture only) scans with zero leaks")
        else:
            failures.append(f"clean tree produced findings: {clean}")

    if failures:
        for failure in failures:
            print(f"FAIL  {failure}")
        return 1
    print("OK: 3/3 gitleaks allowlist cases pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
