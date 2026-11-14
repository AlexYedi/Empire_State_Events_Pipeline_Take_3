#!/usr/bin/env python3
"""alert.py — tell Alex when a scheduled mini job fails or the mini's Claude login is about to expire.

Called by run-job.sh at the end of every job:
    alert.py job  <job> <exit-code> <log-path>
    alert.py login                       (checks `claude auth status`; alerts when the login expires within 5 days)
Set ALERT_DRY_RUN=1 to test without creating a Linear issue (the key may also be in the shell environment).

Channel: a Linear issue in EMPIRE-STATE (Linear is the one list, CLAUDE.md §5) when LINEAR_API_KEY is in this
checkout's .env, plus a macOS notification and a line in ~/Library/Logs/esep-runner/ALERTS.txt either way.
At most one alert per (kind, job, local day): a job that fails every hour opens one issue, not 24.

The issue body carries the last lines of the job's own log. Runner logs hold run metadata only (the sweep never
echoes page-derived text; see theme-sweep.sh), so nothing from the open web is forwarded. Stdlib only. Never prints
the key. Never fails the job: every error here is caught and logged.
"""
import json, os, subprocess, sys, urllib.request
from datetime import date, datetime, timezone

TEAM_ID = "816e0384-53f0-4159-a844-c8ee5d4b3067"   # Linear EMPIRE-STATE (YED)
STATE = os.path.expanduser("~/Library/Logs/esep-runner/.alerts")
LEDGER = os.path.expanduser("~/Library/Logs/esep-runner/ALERTS.txt")
LOGIN_WARN_DAYS = 5


def env_key(name):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".env")
    try:
        for line in open(path, encoding="utf-8"):
            k, _, v = line.strip().partition("=")
            if k == name:
                return v.strip().strip('"').strip("'") or None
    except OSError:
        pass
    return os.environ.get(name) or None


def once_today(tag):
    """True the first time `tag` is seen today; records it."""
    os.makedirs(STATE, exist_ok=True)
    marker = os.path.join(STATE, f"{date.today().isoformat()}-{tag}")
    if os.path.exists(marker):
        return False
    open(marker, "w").close()
    return True


def linear_issue(title, body):
    if os.environ.get("ALERT_DRY_RUN"):
        return "dry run; Linear skipped"
    key = env_key("LINEAR_API_KEY")
    if not key:
        return "no LINEAR_API_KEY in .env; local alert only"
    q = ("mutation($i: IssueCreateInput!) { issueCreate(input: $i) { success issue { identifier } } }")
    data = json.dumps({"query": q, "variables": {"i": {
        "teamId": TEAM_ID, "title": title, "description": body, "priority": 2}}}).encode()
    req = urllib.request.Request("https://api.linear.app/graphql", data=data,
                                 headers={"Content-Type": "application/json", "Authorization": key})
    with urllib.request.urlopen(req, timeout=20) as r:
        out = json.load(r)
    iss = (((out.get("data") or {}).get("issueCreate") or {}).get("issue") or {})
    return f"Linear {iss.get('identifier')}" if iss.get("identifier") else f"Linear error: {str(out.get('errors'))[:200]}"


def notify(title, body):
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(f"{stamp}  {title}\n")
    try:
        subprocess.run(["osascript", "-e", f'display notification {json.dumps(body[:200])} with title {json.dumps(title[:80])}'],
                       timeout=10, capture_output=True)
    except Exception:
        pass
    try:
        where = linear_issue(title, body)
    except Exception as e:
        where = f"Linear send failed ({type(e).__name__})"
    print(f"ALERT: {title} -> {where}")


def job_alert(job, rc, log):
    if rc == "0" or (job == "sync" and rc == "255"):   # 255 = laptop asleep; the next hour retries
        return
    if not once_today(f"job-{job}"):
        print(f"ALERT suppressed: {job} already alerted today")
        return
    try:
        tail = "".join(open(log, encoding="utf-8", errors="replace").readlines()[-15:])
    except OSError:
        tail = "(log unreadable)"
    body = (f"The scheduled `{job}` job on esep-mini exited {rc} at {datetime.now(timezone.utc):%Y-%m-%d %H:%MZ}.\n\n"
            f"Log on the mini: `{log}`\n\n```\n{tail}\n```\n\n"
            f"Runbook: `.claude/references/mini-runner.md`. Close this issue once the next run passes.")
    notify(f"Mini runner: {job} failed (exit {rc})", body)


def login_alert():
    try:
        out = subprocess.run(["claude", "auth", "status"], capture_output=True, text=True, timeout=30).stdout
        st = json.loads(out)
    except Exception as e:
        st = {"loggedIn": False, "_err": type(e).__name__}
    exp = st.get("loginExpiresAt")
    if st.get("loggedIn") and exp:
        days = (datetime.fromisoformat(exp.replace("Z", "+00:00")) - datetime.now(timezone.utc)).total_seconds() / 86400
        if days > LOGIN_WARN_DAYS:
            return
        msg = f"expires in {days:.1f} days ({exp[:10]})"
    else:
        msg = "is logged out" + (f" ({st['_err']})" if st.get("_err") else "")
    if not once_today("login"):
        return
    notify(f"Mini runner: Claude login {msg}",
           f"The Claude Code login on esep-mini {msg}. Scheduled model jobs (sweep, smoke) fail without it.\n\n"
           "Fix: Screen Share into the mini, run `claude` in Terminal and log in (or `/login`), then "
           "`claude auth status` to confirm the new expiry.")


if __name__ == "__main__":
    try:
        if len(sys.argv) >= 5 and sys.argv[1] == "job":
            job_alert(sys.argv[2], sys.argv[3], sys.argv[4])
        elif len(sys.argv) >= 2 and sys.argv[1] == "login":
            login_alert()
        else:
            print(__doc__.split("\n\n")[1]); sys.exit(64)
    except Exception as e:   # an alert must never fail the job
        print(f"ALERT error ({type(e).__name__}); job result unchanged")
