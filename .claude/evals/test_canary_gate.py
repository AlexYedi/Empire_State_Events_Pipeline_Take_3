import json,os,sys,tempfile,datetime,shutil
sys.path.insert(0,'.claude/evals'); import calibration_stats as cal
ok=n=0
def ck(name,cond):
    global ok,n; n+=1; ok+=bool(cond); print(("  ✓ " if cond else "  ✗ ")+name)
# A SECOND healthy voting seat, so a demotion is observable: with only one, the last-voting-seat guard
# (YED-212) correctly holds it, which would mask every canary rule under test.
HEALTHY={"id":"anchor","seat_name":"anchor","provider":"anthropic","status":"voting","since":"2026-01-01"}
SEATS={"seats":[{"id":"openai","seat_name":"openai","provider":"openai","status":"voting","since":"2026-01-01","model":"gpt-5.4-mini"},HEALTHY]}
def gate_with(canary):
    d=tempfile.mkdtemp()
    cal.SEATS_FILE=os.path.join(d,"seats.json"); json.dump(SEATS,open(cal.SEATS_FILE,"w"))
    cal.CANARY_STATE=os.path.join(d,"state.json")
    if canary is not None: json.dump(canary,open(cal.CANARY_STATE,"w"))
    g=cal.gate([],3.0)["openai"]; shutil.rmtree(d); return g
now=datetime.datetime.now(datetime.timezone.utc)
iso=lambda dt: dt.strftime("%Y-%m-%dT%H:%M:%SZ")
g=gate_with(None); ck("no canary state: reported 'never run', NOT demoted (would demote everything on day 1)", g["effective"]=="voting" and g["canary"]["status"]=="never run")
g=gate_with({"openai":{"status":"pass","last_run":iso(now),"consecutive_failures":0,"model_resolved":"gpt-5.4-mini-2026"}})
ck("green canary today: stays voting", g["effective"]=="voting" and not g["demoted_because"])
g=gate_with({"openai":{"status":"fail","last_run":iso(now),"consecutive_failures":1,"model_resolved":"gpt-5.4-mini-2026"}})
ck("ONE failure: not yet demoted (one bad day is not a trend)", g["effective"]=="voting")
g=gate_with({"openai":{"status":"fail","last_run":iso(now),"consecutive_failures":2,"model_resolved":"gpt-5.4-mini-2026"}})
ck("TWO consecutive failures: demoted a rung", g["effective"]=="advisory" and any("consecutive canary" in w for w in g["demoted_because"]))
g=gate_with({"openai":{"status":"pass","last_run":iso(now),"consecutive_failures":0,"model_resolved":"gpt-4.1-2025"}})
ck("model swapped since the last green canary: demoted until re-run", g["effective"]=="advisory" and any("model changed" in w for w in g["demoted_because"]))
g=gate_with({"openai":{"status":"pass","last_run":iso(now-datetime.timedelta(days=30)),"consecutive_failures":0,"model_resolved":"gpt-5.4-mini-2026"}})
ck("30-day-old canary on a VOTING seat: demoted as stale", g["effective"]=="advisory" and any("old" in w for w in g["demoted_because"]))
S2={"seats":[dict(SEATS["seats"][0],status="shadow"),HEALTHY]}
d=tempfile.mkdtemp(); cal.SEATS_FILE=os.path.join(d,"seats.json"); json.dump(S2,open(cal.SEATS_FILE,"w"))
cal.CANARY_STATE=os.path.join(d,"state.json"); json.dump({"openai":{"status":"pass","last_run":iso(now-datetime.timedelta(days=30)),"consecutive_failures":0,"model_resolved":"gpt-5.4-mini-2026"}},open(cal.CANARY_STATE,"w"))
g=cal.gate([],3.0)["openai"]; shutil.rmtree(d)
ck("stale canary on a SHADOW seat: not demoted (staleness only binds a voting seat)", not any("old" in w for w in g["demoted_because"]))

# --- last-voting-seat guard (Alex's ruling 2026-09-21) ---
ONLY={"seats":[{"id":"openai","seat_name":"openai","provider":"openai","status":"voting","since":"2026-01-01","model":"gpt-5.4-mini"}]}
d=tempfile.mkdtemp(); cal.SEATS_FILE=os.path.join(d,"seats.json"); json.dump(ONLY,open(cal.SEATS_FILE,"w"))
cal.CANARY_STATE=os.path.join(d,"state.json")
json.dump({"openai":{"status":"fail","last_run":iso(now),"consecutive_failures":2,"model_resolved":"gpt-5.4-mini-2026"}},open(cal.CANARY_STATE,"w"))
g=cal.gate([],3.0)["openai"]; shutil.rmtree(d)
ck("last voting seat: demotion RECORDED but NOT applied", g["effective"]=="voting" and g.get("last_voting_seat_held") is True)
ck("last voting seat: the reason is preserved for Alex to confirm", bool(g.get("demotion_pending_confirmation")))
print(f"{ok}/{n} canary-gate cases pass"); sys.exit(0 if ok==n else 1)
