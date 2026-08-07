#!/usr/bin/env python3
"""
Generate the standalone Build-Arcs artifact HTML from the CANONICAL data (empire-state-hub's
build-arcs.json). This is the anti-drift half of the single-source rule: the hub page imports
build-arcs.json directly, and this script regenerates the shareable Artifact from the SAME file —
so the two surfaces can never disagree. Edit build-arcs.json, run this, republish. Never hand-edit
arc copy in the HTML.

Design identity (kept from the hand-authored v1): "instrument readout as monograph" — cool slate
neutrals, a signal-cobalt accent, a masthead canvas plotting the engine's own decay curve, and the
"V1 limits" row flagged amber so intellectual honesty is a visible structural device. Foundation
arcs render as "◆ Foundation" anchors; the arcs built on them are numbered and indented.

Usage:
    python3 .claude/scripts/gen_build_arcs_artifact.py            # write to scratchpad, then republish
    python3 .claude/scripts/gen_build_arcs_artifact.py --out /path/build-arcs.html
    python3 .claude/scripts/gen_build_arcs_artifact.py --data /path/build-arcs.json

No network, no secrets — pure data-in, HTML-out. Republish the emitted file to keep the same URL.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TAKE3 = os.path.abspath(os.path.join(HERE, "..", ".."))
DEFAULT_DATA = os.path.abspath(os.path.join(TAKE3, "..", "empire-state-hub", "src", "data", "build-arcs.json"))
# Stable, non-session default (was a hardcoded past scratchpad path). To republish to the SAME
# Artifact URL, pass --out pointing at this conversation's scratchpad file, then re-run the Artifact tool.
DEFAULT_OUT = os.path.join(TAKE3, ".claude", "artifacts", "build-arcs.html")

# The template. Data is injected at the __DATA__ marker (NOT an f-string — CSS uses literal braces).
TEMPLATE = r"""<title>Build Arcs — Empire State</title>

<style>
  :root {
    --bg: #EBEDF1; --surface: #F6F7F9; --panel: #FFFFFF; --fg: #131820;
    --muted: #566173; --border: #D5DAE1; --accent: #1F5FE0; --accent-2: #B45F1E;
    --accent-soft: rgba(31,95,224,0.09); --amber-soft: rgba(180,95,30,0.10);
    --glow: rgba(31,95,224,0.16); --grid: rgba(19,24,32,0.05);
    --serif: "Iowan Old Style","Charter","Palatino Linotype",Palatino,Georgia,ui-serif,serif;
    --sans: ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI","Helvetica Neue",Arial,sans-serif;
    --mono: ui-monospace,"SF Mono","JetBrains Mono","Menlo","Consolas",monospace;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #0B0E13; --surface: #131924; --panel: #0F141C; --fg: #E6EAF1;
      --muted: #8B95A8; --border: #222B39; --accent: #5E8CFF; --accent-2: #E0913F;
      --accent-soft: rgba(94,140,255,0.11); --amber-soft: rgba(224,145,63,0.11);
      --glow: rgba(94,140,255,0.22); --grid: rgba(230,234,241,0.05);
    }
  }
  :root[data-theme="light"] {
    --bg: #EBEDF1; --surface: #F6F7F9; --panel: #FFFFFF; --fg: #131820;
    --muted: #566173; --border: #D5DAE1; --accent: #1F5FE0; --accent-2: #B45F1E;
    --accent-soft: rgba(31,95,224,0.09); --amber-soft: rgba(180,95,30,0.10);
    --glow: rgba(31,95,224,0.16); --grid: rgba(19,24,32,0.05);
  }
  :root[data-theme="dark"] {
    --bg: #0B0E13; --surface: #131924; --panel: #0F141C; --fg: #E6EAF1;
    --muted: #8B95A8; --border: #222B39; --accent: #5E8CFF; --accent-2: #E0913F;
    --accent-soft: rgba(94,140,255,0.11); --amber-soft: rgba(224,145,63,0.11);
    --glow: rgba(94,140,255,0.22); --grid: rgba(230,234,241,0.05);
  }
  * { box-sizing: border-box; }
  body { margin: 0; background: var(--bg); color: var(--fg); font-family: var(--sans);
    -webkit-font-smoothing: antialiased; line-height: 1.5; }
  .wrap { max-width: 860px; margin: 0 auto; padding: 0 24px 96px; }
  .mast { position: relative; padding: 72px 0 40px; overflow: hidden; }
  .mast canvas { position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; opacity: .9; }
  .mast-inner { position: relative; z-index: 1; }
  .eyebrow { font-family: var(--mono); font-size: .72rem; letter-spacing: .22em;
    text-transform: uppercase; color: var(--accent); margin: 0 0 18px; }
  h1 { font-family: var(--serif); font-weight: 600; font-size: clamp(2.5rem,7vw,4.4rem);
    line-height: 1.02; letter-spacing: -.015em; margin: 0; text-wrap: balance; }
  h1 .thin { font-style: italic; font-weight: 500; color: var(--muted); }
  .lede { max-width: 60ch; margin: 22px 0 0; font-size: 1.09rem; line-height: 1.6; color: var(--fg); }
  .lede .em { color: var(--accent); font-style: italic; }
  .legend { display: flex; flex-wrap: wrap; gap: 8px; margin: 30px 0 8px; align-items: center; }
  .chip { display: inline-flex; align-items: baseline; gap: 8px; font-family: var(--mono);
    font-size: .72rem; letter-spacing: .04em; padding: 6px 11px; border: 1px solid var(--border);
    border-radius: 999px; background: var(--surface); color: var(--fg); text-decoration: none;
    transition: border-color .18s, color .18s; }
  .chip:hover, .chip:focus-visible { border-color: var(--accent); color: var(--accent); outline: none; }
  .chip .n { color: var(--muted); }
  .chip .tick { width: 7px; height: 7px; border-radius: 2px; background: var(--accent); align-self: center; }
  .meta { font-family: var(--mono); font-size: .72rem; color: var(--muted); letter-spacing: .04em; margin-left: auto; }
  .theme { margin-top: 68px; scroll-margin-top: 24px; }
  .theme-head { display: flex; align-items: baseline; gap: 16px; padding-bottom: 14px; border-bottom: 1px solid var(--border); }
  .theme-idx { font-family: var(--mono); font-size: .72rem; color: var(--accent); letter-spacing: .14em; }
  .theme-head h2 { font-family: var(--serif); font-weight: 600; font-size: clamp(1.55rem,3.5vw,2.1rem);
    margin: 0; letter-spacing: -.01em; }
  .theme-blurb { margin: 12px 0 0; color: var(--muted); font-size: .98rem; max-width: 62ch; }
  .built { margin-top: 34px; border-left: 1px solid var(--border); padding-left: 22px; }
  .built-label { font-family: var(--mono); font-size: .68rem; text-transform: uppercase;
    letter-spacing: .18em; color: var(--muted); margin: 0 0 4px; }
  .arc { margin-top: 44px; scroll-margin-top: 24px; }
  .arc-idx { font-family: var(--mono); font-size: .8rem; font-weight: 600; color: var(--accent);
    letter-spacing: .06em; position: relative; padding-left: 16px; }
  .arc-idx::before { content: ""; position: absolute; left: 0; top: .42em; width: 8px; height: 8px;
    border-radius: 2px; background: var(--accent-2); }
  .arc-idx.foundation { padding-left: 0; }
  .arc-idx.foundation::before { content: none; }
  .arc h3 { font-family: var(--serif); font-weight: 600; font-size: clamp(1.3rem,3vw,1.7rem);
    margin: 0; letter-spacing: -.01em; line-height: 1.15; }
  .arc.is-foundation h3 { font-size: clamp(1.5rem,3.4vw,2rem); }
  .arc-tag { font-family: var(--serif); font-style: italic; color: var(--muted); font-size: 1.02rem; margin: 6px 0 0; }
  .facets { margin: 22px 0 0; border-left: 2px solid var(--border); padding-left: 0; }
  .facet { display: grid; grid-template-columns: 170px 1fr; gap: 4px 26px; padding: 14px 0 14px 22px;
    border-bottom: 1px solid color-mix(in srgb, var(--border) 55%, transparent);
    margin-left: -2px; border-left: 2px solid transparent; }
  .facet:last-child { border-bottom: none; }
  .facet dt { font-family: var(--mono); font-size: .68rem; text-transform: uppercase;
    letter-spacing: .11em; color: var(--muted); padding-top: 2px; }
  .facet dd { margin: 0; font-size: .955rem; line-height: 1.58; color: var(--fg); max-width: 60ch; }
  .facet.limit { background: var(--amber-soft); border-left-color: var(--accent-2); border-radius: 0 4px 4px 0; }
  .facet.limit dt { color: var(--accent-2); }
  .through { margin-top: 72px; background: var(--surface); border: 1px solid var(--border);
    border-radius: 10px; padding: 30px 32px; position: relative; overflow: hidden; }
  .through::before { content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 3px;
    background: linear-gradient(var(--accent), var(--accent-2)); }
  .through .eyebrow { margin-bottom: 12px; }
  .through p { margin: 0; font-family: var(--serif); font-size: 1.15rem; line-height: 1.55; }
  footer { margin-top: 52px; padding-top: 22px; border-top: 1px solid var(--border);
    font-family: var(--mono); font-size: .72rem; letter-spacing: .05em; color: var(--muted);
    display: flex; justify-content: space-between; flex-wrap: wrap; gap: 10px; }
  .reveal { opacity: 0; transform: translateY(14px); }
  .reveal.in { opacity: 1; transform: none; transition: opacity .6s ease, transform .6s ease; }
  @media (max-width: 620px) {
    .facet { grid-template-columns: 1fr; gap: 4px; }
    .facet dt { padding-top: 0; }
    .meta { margin-left: 0; width: 100%; }
  }
  @media (prefers-reduced-motion: reduce) { .reveal { opacity: 1; transform: none; transition: none; } }
</style>

<div class="wrap">
  <header class="mast">
    <canvas id="decay" aria-hidden="true"></canvas>
    <div class="mast-inner">
      <p class="eyebrow">Empire State · Build-in-public</p>
      <h1>Build&nbsp;Arcs<span class="thin"> — the work, in arcs.</span></h1>
      <p class="lede" id="lede"></p>
      <nav class="legend" id="legend" aria-label="Themes"></nav>
      <div class="legend"><span class="meta" id="counts"></span></div>
    </div>
  </header>
  <main id="body"></main>
  <section class="through reveal">
    <p class="eyebrow">The through-line</p>
    <p id="through"></p>
  </section>
  <footer>
    <span>Empire State Events Pipeline — a build-in-public artifact</span>
    <span id="asof"></span>
  </footer>
</div>

<script>
  const DATA = __DATA__;
  const THEMES = DATA.themes, ARCS = DATA.arcs;
  const FACETS = [["what","What it is"],["why","Why it exists"],["value","The value"],
    ["bestPractices","Best practices"],["v1Limits","V1 limits"],["future","Where it goes"],["enterprise","Enterprise tie-in"]];
  const esc = (s) => (s||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");

  document.getElementById("lede").innerHTML = esc(DATA.intro).replace("sprints","<span class='em'>sprints</span>");
  document.getElementById("through").textContent = DATA.throughLine;
  document.getElementById("asof").textContent = "As of Aug 2026";
  document.getElementById("counts").textContent = ARCS.length + " arcs · " + THEMES.length + " themes · one operator";

  const legend = document.getElementById("legend");
  THEMES.forEach((t) => {
    const n = ARCS.filter((a) => a.theme === t.id).length;
    const a = document.createElement("a");
    a.className = "chip"; a.href = "#theme-" + t.id;
    a.innerHTML = '<span class="tick"></span>' + esc(t.label) + ' <span class="n">' + n + '</span>';
    legend.appendChild(a);
  });

  function facetHTML(arc) {
    let h = '<dl class="facets">';
    FACETS.forEach(([k, label]) => {
      h += '<div class="facet' + (k === "v1Limits" ? " limit" : "") + '"><dt>' + esc(label) +
           '</dt><dd>' + esc(arc[k]) + '</dd></div>';
    });
    return h + '</dl>';
  }
  function arcHTML(arc, kicker, isFoundation) {
    return '<article class="arc' + (isFoundation ? " is-foundation" : "") + '" id="' + arc.id + '">' +
      '<div class="arc-idx' + (isFoundation ? " foundation" : "") + '">' + esc(kicker) + ' · ' + esc(arc.tagline) + '</div>' +
      '<h3>' + esc(arc.name) + '</h3><p class="arc-tag">' + esc(arc.tagline) + '</p>' + facetHTML(arc) + '</article>';
  }

  const body = document.getElementById("body");
  let child = 0;
  THEMES.forEach((t, ti) => {
    const arcs = ARCS.filter((a) => a.theme === t.id);
    if (!arcs.length) return;
    const foundations = arcs.filter((a) => a.foundation);
    const built = arcs.filter((a) => !a.foundation);
    const sec = document.createElement("section");
    sec.className = "theme reveal"; sec.id = "theme-" + t.id;
    let html = '<div class="theme-head"><span class="theme-idx">' + String(ti + 1).padStart(2, "0") +
      '</span><h2>' + esc(t.label) + '</h2></div><p class="theme-blurb">' + esc(t.blurb) + '</p>';
    foundations.forEach((a) => { html += arcHTML(a, "◆ Foundation", true); });
    if (built.length) {
      html += foundations.length ? '<div class="built"><p class="built-label">Built on it</p>' : '<div>';
      built.forEach((a) => { child += 1; html += arcHTML(a, "Arc " + String(child).padStart(2, "0"), false); });
      html += '</div>';
    }
    sec.innerHTML = html;
    body.appendChild(sec);
  });

  const io = new IntersectionObserver((entries) => {
    entries.forEach((e) => { if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); } });
  }, { rootMargin: "0px 0px -8% 0px" });
  document.querySelectorAll(".reveal").forEach((el) => io.observe(el));

  // masthead decay-curve signature: r(t) = 0.5^(t / half-life) — the engine's own math
  const cv = document.getElementById("decay"), ctx = cv.getContext("2d");
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  function paint(progress) {
    const dpr = Math.min(devicePixelRatio || 1, 2), w = cv.clientWidth, h = cv.clientHeight;
    cv.width = w * dpr; cv.height = h * dpr; ctx.setTransform(dpr, 0, 0, dpr, 0, 0); ctx.clearRect(0, 0, w, h);
    const css = getComputedStyle(document.documentElement);
    const accent = css.getPropertyValue("--accent").trim(), grid = css.getPropertyValue("--grid").trim();
    ctx.strokeStyle = grid; ctx.lineWidth = 1;
    for (let gx = 0; gx <= w; gx += 64) { ctx.beginPath(); ctx.moveTo(gx, 0); ctx.lineTo(gx, h); ctx.stroke(); }
    const halfLives = [0.18, 0.34, 0.62], alphas = [0.10, 0.16, 0.26];
    halfLives.forEach((hl, i) => {
      ctx.beginPath();
      const end = Math.floor(w * progress);
      for (let x = 0; x <= end; x++) {
        const tt = x / w, r = Math.pow(0.5, tt / hl), y = h - 14 - r * (h - 40);
        x === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      }
      ctx.strokeStyle = accent; ctx.globalAlpha = alphas[i]; ctx.lineWidth = 1.6; ctx.stroke();
      if (i === 2 && progress >= 1) {
        const r0 = Math.pow(0.5, 1 / hl);
        ctx.globalAlpha = 0.5; ctx.fillStyle = accent;
        ctx.beginPath(); ctx.arc(w, h - 14 - r0 * (h - 40), 3, 0, Math.PI * 2); ctx.fill();
      }
      ctx.globalAlpha = 1;
    });
  }
  if (reduce) paint(1);
  else { let start = null; (function step(ts){ if(start===null)start=ts;
    const p = Math.min((ts-start)/1200,1); paint(1-Math.pow(1-p,3)); if(p<1) requestAnimationFrame(step); })(); }
  let rt; addEventListener("resize", () => { clearTimeout(rt); rt = setTimeout(() => paint(1), 120); });
  new MutationObserver(() => paint(1)).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
</script>
"""


def main():
    args = sys.argv[1:]

    def argval(flag, default):
        # guard against a flag given with no following value (avoids an IndexError)
        if flag in args:
            i = args.index(flag)
            if i + 1 < len(args):
                return args[i + 1]
            sys.exit(f"{flag} requires a value")
        return default

    data_path = argval("--data", DEFAULT_DATA)
    out = argval("--out", DEFAULT_OUT)
    with open(data_path) as f:
        data = json.load(f)
    html = TEMPLATE.replace("__DATA__", json.dumps(data, ensure_ascii=False))
    out_dir = os.path.dirname(out)
    if out_dir:  # bare filename (no dir component) → makedirs("") would crash
        os.makedirs(out_dir, exist_ok=True)
    with open(out, "w") as f:
        f.write(html)
    print(f"✅ generated artifact from {os.path.relpath(data_path, TAKE3) if data_path.startswith(TAKE3) else data_path}")
    print(f"   {len(data['arcs'])} arcs · {len(data['themes'])} themes → {out}")
    print("   Next: republish this file to the existing Artifact URL to keep the same link.")


if __name__ == "__main__":
    main()
