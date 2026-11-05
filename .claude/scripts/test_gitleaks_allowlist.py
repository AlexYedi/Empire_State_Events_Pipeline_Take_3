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


# Review round 2 killing cases (2026-11-05): each entry pins a finding the allowlist
# must still produce. The sentinel-prefix token shares the historical cd0a50f value
# prefix but differs after it — built from a different seed so no literal matches.
SENTINEL_PREFIX_TOKEN = ("sk_live_" + hashlib.sha256(b"test").hexdigest()[:8]  # == 9f86d081, built at runtime — no literal in this file (generic-api-key flagged the hardcoded prefix)
                         + hashlib.sha256(b"outside-selftest").hexdigest()[:24])
OTHER_TOKEN = "sk_live_" + hashlib.sha256(b"different-key-in-selftest").hexdigest()[:32]


def build_scratch_repo(base: Path, name: str, files: dict[str, str]) -> Path:
    """Single-commit scratch repo with the shared config + the given files — every
    allowlist claim is proven per-case, git mode only (dir mode skips path-matched
    files before content evaluation)."""
    repo = base / name
    for rel, content in files.items():
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    shutil.copy(CONFIG, repo / ".gitleaks.toml")
    run_git(repo, "init", "-q")
    # CI runners have no git identity; the probe repo needs one to commit.
    run_git(repo, "config", "user.name", "gitleaks-selftest")
    run_git(repo, "config", "user.email", "selftest@example.invalid")
    run_git(repo, "add", "-A")
    run_git(repo, "commit", "-qm", f"probe: {name}")
    return repo


def main() -> int:
    gitleaks = find_gitleaks()
    failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix="gitleaks-allowlist-probe-") as tmp:
        base = Path(tmp)
        report = base / "report.json"  # outside the probe repos on purpose
        fixture_digest = json.dumps({"source_key": DIGEST}) + "\n"

        def findings(name: str, files: dict[str, str]) -> set[str]:
            leaks = scan(gitleaks, report, build_scratch_repo(base, name, files))
            return {f.get("Secret") for f in leaks}

        # 1. planted token INSIDE the exempted path must still flag (value-scoping)
        planted = findings("probe-token", {
            "supabase/fixtures/digest.json": fixture_digest,
            "supabase/fixtures/probe.json": json.dumps({"api_key": PLANTED_TOKEN}) + "\n",
        })
        print("PASS  planted sk_live_ token in supabase/fixtures/ is flagged"
              if PLANTED_TOKEN in planted else "FAIL  planted token was NOT flagged")
        if PLANTED_TOKEN not in planted:
            failures.append("planted token NOT flagged — allowlist exempts whole files")

        # 2. digest of a public *.example URL in the exempted path passes
        print("PASS  sha256 digest of a public *.example URL is exempt"
              if DIGEST not in planted else "FAIL  digest was flagged")
        if DIGEST in planted:
            failures.append("digest flagged — value-scoping too narrow")

        # 3. clean tree: zero findings
        clean = findings("probe-clean", {"supabase/fixtures/digest.json": fixture_digest})
        print("PASS  clean tree (digest fixture only) scans with zero leaks"
              if not clean else f"FAIL  clean tree findings: {clean}")
        if clean:
            failures.append(f"clean tree produced findings: {clean}")

        # 4. (round 2) 64-hex OUTSIDE supabase/fixtures/ must flag
        outside = findings("probe-hex-outside", {"digest_root.json": fixture_digest})
        print("PASS  64-hex outside supabase/fixtures/ is flagged"
              if DIGEST in outside else "FAIL  64-hex outside fixtures was NOT flagged")
        if DIGEST not in outside:
            failures.append("64-hex outside fixtures NOT flagged — path too broad")

        # 5. (round 2) sentinel-PREFIX sk_live outside the selftest path must flag
        prefix_outside = findings("probe-prefix-outside", {
            "probe_other.py": f'KEY = "{SENTINEL_PREFIX_TOKEN}"\n',
        })
        print("PASS  9f86d081-prefixed sk_live outside the selftest path is flagged"
              if SENTINEL_PREFIX_TOKEN in prefix_outside
              else "FAIL  sentinel-prefix token outside the selftest path was NOT flagged")
        if SENTINEL_PREFIX_TOKEN not in prefix_outside:
            failures.append("sentinel-prefix token outside the selftest path NOT flagged")

        # 6. (round 2) a DIFFERENT sk_live in the selftest path must flag
        in_path = findings("probe-other-token-selftest-path", {
            ".claude/scripts/test_gitleaks_allowlist.py":
                f'PLANTED = "{OTHER_TOKEN}"\n',
        })
        print("PASS  a different sk_live in the selftest path is flagged"
              if OTHER_TOKEN in in_path else "FAIL  different sk_live in selftest path NOT flagged")
        if OTHER_TOKEN not in in_path:
            failures.append("different sk_live in the selftest path NOT flagged — "
                            "the sentinel entry is wider than one value")

        # 7-11 (round 3): anchoring pins — the sentinel entry exempts ONLY the exact
        # bare-prefix form and the prefix+24hex form; anything longer or otherwise
        # different in that file still flags. Digest anchoring is pinned the same way.
        bare = "sk_live_" + hashlib.sha256(b"test").hexdigest()[:8]           # 16-char form (e161a70)
        full = bare + hashlib.sha256(b"cd0a50f-sentinel").hexdigest()[:24]    # prefix+24hex (cd0a50f)
        overlong = bare + hashlib.sha256(b"overlong").hexdigest()[:25]        # 25 hex tail — not exempt
        in_path = lambda tag, content: findings(tag, {
            ".claude/scripts/test_gitleaks_allowlist.py": content})

        r_full = in_path("probe-sentinel-full", f'X = "{full}"\n')
        print("PASS  full sentinel (prefix+24hex) in the selftest path is exempt"
              if full not in r_full and not r_full else "FAIL  full sentinel was flagged")
        if r_full:
            failures.append("full sentinel flagged — anchored exemption broken")

        r_bare = in_path("probe-sentinel-bare", f'X = "{bare}"\n')
        print("PASS  bare 16-char sentinel form in the selftest path is exempt"
              if not r_bare else "FAIL  bare 16-char form was flagged")
        if r_bare:
            failures.append("bare 16-char sentinel flagged — anchored exemption broken")

        r_over = in_path("probe-sentinel-overlong", f'X = "{overlong}"\n')
        print("PASS  a sentinel-PREFIX secret with a longer tail is still flagged"
              if overlong not in r_over and r_over else "FAIL  overlong sentinel was NOT flagged")
        if not r_over:
            failures.append("overlong sentinel NOT flagged — entry behaves unanchored")

        # 10 (round 3): config pin — the regexes must STAY anchored. (A scan-based pin
        # for longer hex is impossible by construction: gitleaks' generic-api-key rule
        # only captures well-shaped secrets, so a 65-hex string produces no finding
        # with or without the allowlist — the anchored regex is the exposure boundary,
        # and this pin makes un-anchoring a test failure.)
        cfg = CONFIG.read_text()
        anchored = ("^sk_live_9f86d081$" in cfg
                    and "^sk_live_9f86d081[0-9a-f]{24}$" in cfg
                    and "^[0-9a-f]{64}$" in cfg
                    and "sk_live_9f86d081([0-9a-f]{24})?" not in cfg)
        print("PASS  allowlist regexes are anchored in .gitleaks.toml"
              if anchored else "FAIL  allowlist regexes lost their anchors")
        if not anchored:
            failures.append("allowlist regexes are not anchored — entry was widened")

    if failures:
        for failure in failures:
            print(f"FAIL  {failure}")
        return 1
    print("OK: 10/10 gitleaks allowlist cases pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
