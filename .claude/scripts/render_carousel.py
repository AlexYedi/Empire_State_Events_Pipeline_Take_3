#!/usr/bin/env python3
"""Render a carousel HTML file to an upload-ready 4:5 PDF and verify it (YED-259).

The deterministic half of carousel work, so a render can't "look done" and still be wrong:
  1. overflow check — loads the page in headless Chrome with a small probe script and reports, per
     slide, any element that spills past the 1080x1350 frame or any slide whose content overflows;
  2. PDF render — headless Chrome --print-to-pdf (method in content-patterns/visual-briefs.md);
  3. verify — page count equals the number of .slide elements and every page is 810x1013 pt;
  4. preview — optional PNG of the stacked slides for a visual check;
  5. --x — also export each slide as a 1:1 PNG for X (E-05): X has no PDF carousels.

Prints a JSON report; exit 0 only if every check passes.

Usage: render_carousel.py <in.html> [--out out.pdf] [--png preview.png] [--x]
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile

PROBE = """
<script>
window.addEventListener('load', () => {
  const out = [];
  document.querySelectorAll('.slide').forEach((s, i) => {
    const r = s.getBoundingClientRect();
    if (s.scrollHeight > s.clientHeight + 1 || s.scrollWidth > s.clientWidth + 1)
      out.push({slide: i + 1, issue: 'content overflows slide', over_px: Math.max(s.scrollHeight - s.clientHeight, s.scrollWidth - s.clientWidth)});
    s.querySelectorAll('*').forEach(el => {
      const e = el.getBoundingClientRect();
      if (e.width === 0 || e.height === 0) return;
      const over = Math.max(e.right - r.right, e.bottom - r.bottom, r.left - e.left, r.top - e.top);
      if (over > 2) out.push({slide: i + 1, issue: 'element outside frame', el: el.tagName.toLowerCase() + (el.className ? '.' + String(el.className).split(' ')[0] : ''), over_px: Math.round(over), text: (el.textContent || '').trim().slice(0, 60)});
    });
  });
  const m = document.createElement('meta'); m.name = 'render-probe';
  m.content = JSON.stringify({slides: document.querySelectorAll('.slide').length, problems: out.slice(0, 40)});
  document.head.appendChild(m);
});
</script>
"""


def chrome():
    for p in ("/Applications/Tech Stack/Google Chrome.app/Contents/MacOS/Google Chrome",
              "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"):
        if os.path.exists(p):
            return p
    try:
        app = subprocess.run(["mdfind", "kMDItemCFBundleIdentifier == 'com.google.Chrome'"],
                             capture_output=True, text=True, timeout=10).stdout.split("\n")[0].strip()
        if app:
            return os.path.join(app, "Contents/MacOS/Google Chrome")
    except (OSError, subprocess.SubprocessError):
        pass
    return None


def run(bin_, args, timeout=90):
    return subprocess.run([bin_, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                           "--virtual-time-budget=3000", *args], capture_output=True, text=True, timeout=timeout)


# ---- pure checks (E-07 item 5): everything verifiable without Chrome ----
def pdf_page_count(pdf: bytes) -> int:
    """/Type /Page objects, excluding /Pages."""
    return len(re.findall(rb"/Type\s*/Page[^s]", pdf))


def pdf_page_sizes_pt(pdf: bytes) -> list:
    """Deduplicated MediaBox sizes, formatted like '810x1013'."""
    boxes = re.findall(rb"/MediaBox\s*\[\s*0\s+0\s+([\d.]+)\s+([\d.]+)\s*\]", pdf)
    return sorted({f"{float(w):.0f}x{float(h):.0f}" for w, h in boxes})


def parse_probe(dom: str) -> dict:
    m = re.search(r'<meta name="render-probe" content="([^"]*)"', dom)
    return json.loads(m.group(1).replace("&quot;", '"').replace("&amp;", "&")) if m \
        else {"slides": None, "problems": ["probe did not run"]}


def pdf_verify(probe: dict, pdf: bytes) -> dict:
    """The three render checks: no overflow findings, page count matches the .slide count,
    every page is the 4:5 810x1013pt box."""
    pages = pdf_page_count(pdf)
    sizes = pdf_page_sizes_pt(pdf)
    return {"pdf_pages": pages, "page_sizes_pt": sizes,
            "checks": {"no_overflow": not probe["problems"],
                       "page_count_matches_slides": probe["slides"] is not None and pages == probe["slides"],
                       "pages_are_4x5": sizes == ["810x1013"]}}


# ---- X export (E-05): X has no PDF carousels, so each slide exports as a 1:1 PNG ----
X_SQUARE_PX = 1080


def x_export_geometry(slide_w: int, slide_h: int, out: int = X_SQUARE_PX) -> dict:
    """Pure 1:1 sizing maths for --x. The slide (rendered 1080x1350, 4:5) fits inside a
    square canvas with letterbox — never cropped. Returns the Chrome viewport, the uniform
    scale, the on-canvas rendered size, and the letterbox offset."""
    scale = min(out / slide_w, out / slide_h)
    w, h = round(slide_w * scale), round(slide_h * scale)
    return {"viewport": [out, out], "scale": scale, "rendered": [w, h],
            "offset": [round((out - w) / 2), round((out - h) / 2)]}


def x_export_js(index: int, geom: dict) -> str:
    """The per-slide export script: hide every other .slide, scale and letterbox the target
    one per the geometry. Injected before </body>; runs on load."""
    return """
<script>
window.addEventListener('load', () => {
  const slides = Array.from(document.querySelectorAll('.slide'));
  const s = slides[%d];
  if (!s) return;
  document.body.style.margin = '0';
  document.body.style.overflow = 'hidden';
  document.body.style.background = '#000';
  slides.forEach(el => { if (el !== s) el.style.display = 'none'; });
  s.style.position = 'fixed';
  s.style.left = '%dpx';
  s.style.top = '%dpx';
  s.style.transformOrigin = 'top left';
  s.style.transform = 'scale(%s)';
});
</script>
""" % (index, geom["offset"][0], geom["offset"][1], geom["scale"])


def selftest():
    """--selftest: the pure checks only — page count, 4:5 aspect maths, the overflow-findings
    gate, and probe-meta parsing — on inline synthetic fixtures. No Chrome, no network, no writes."""
    checks = []

    def ck(name, cond):
        checks.append((name, bool(cond)))

    pages3 = (b"/Type /Catalog\n"
              b"/Type /Pages\n"
              b"/Type /Page /MediaBox [0 0 810 1013]\n"
              b"/Type /Page /MediaBox [0 0 810 1013.0]\n"
              b"/Type /Page /MediaBox [0 0 810.0 1013]\n")
    ok_probe = {"slides": 3, "problems": []}
    ck("page count: counts /Page objects, not /Pages",
       pdf_page_count(pages3) == 3 and pdf_page_count(b"/Type /Pages") == 0)
    ck("4:5 maths: dedupes float-formatted MediaBoxes to the one expected size",
       pdf_page_sizes_pt(pages3) == ["810x1013"])
    ck("verify: three pages, three slides, no findings -> all checks pass",
       pdf_verify(ok_probe, pages3)["checks"] == {"no_overflow": True,
                                                  "page_count_matches_slides": True,
                                                  "pages_are_4x5": True})

    wrong_size = b"/Type /Page /MediaBox [0 0 810 1012]\n"
    ck("4:5 maths: a non-4:5 page size fails pages_are_4x5",
       pdf_verify(ok_probe, wrong_size)["checks"]["pages_are_4x5"] is False
       and pdf_page_sizes_pt(wrong_size) == ["810x1012"])
    short_pdf = b"/Type /Page /MediaBox [0 0 810 1013]\n"
    ck("page count: fewer pages than slides fails the count check",
       pdf_verify({"slides": 2, "problems": []}, short_pdf)["checks"]["page_count_matches_slides"] is False)
    ck("page count: a probe that never ran (slides None) fails the count check",
       pdf_verify({"slides": None, "problems": []}, short_pdf)["checks"]["page_count_matches_slides"] is False)
    ck("overflow: any probe finding trips no_overflow",
       pdf_verify({"slides": 1, "problems": [{"slide": 1, "issue": "content overflows slide", "over_px": 12}]},
                  short_pdf)["checks"]["no_overflow"] is False)

    dom = '<html><head><meta name="render-probe" content="{&quot;slides&quot;: 3, ' \
          '&quot;problems&quot;: [{&quot;slide&quot;: 2, &quot;issue&quot;: &quot;element outside frame&quot;, &quot;over_px&quot;: 5}]}"></head></html>'
    parsed = parse_probe(dom)
    ck("probe parse: HTML-escaped probe meta round-trips to the probe dict",
       parsed["slides"] == 3 and parsed["problems"][0]["over_px"] == 5)
    ck("probe parse: a missing probe degrades to slides None + a finding",
       parse_probe("<html></html>") == {"slides": None, "problems": ["probe did not run"]})

    # X export maths (E-05): a 4:5 slide letterboxed into a 1:1 PNG, never cropped
    geom = x_export_geometry(1080, 1350)
    ck("x export: a 1080x1350 slide scales to 864x1080 centered on a 1080x1080 canvas",
       geom == {"viewport": [1080, 1080], "scale": 0.8, "rendered": [864, 1080], "offset": [108, 0]})
    ck("x export: the rendered area fits the canvas with the slide's aspect preserved",
       geom["rendered"][0] <= X_SQUARE_PX and geom["rendered"][1] <= X_SQUARE_PX
       and geom["rendered"][0] / geom["rendered"][1] == 1080 / 1350)
    sq = x_export_geometry(1350, 1350)
    ck("x export: an already-square slide gets zero letterbox offset",
       sq["rendered"] == [1080, 1080] and sq["offset"] == [0, 0] and sq["scale"] == 0.8)
    js = x_export_js(2, geom)
    ck("x export: the per-slide script targets slide 3, scales and letterboxes it",
       "slides[2]" in js and "scale(0.8)" in js and "left = '108px'" in js and "top = '0px'" in js)

    fails = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  {'✓' if ok else '✗'} {n}")
    print(f"selftest: {len(checks) - len(fails)}/{len(checks)} render-carousel cases pass")
    return 0 if not fails else 1


def main():
    if "--selftest" in sys.argv:
        return selftest()
    ap = argparse.ArgumentParser()
    ap.add_argument("html")
    ap.add_argument("--out")
    ap.add_argument("--png")
    ap.add_argument("--x", action="store_true",
                    help="also export each slide as a 1:1 PNG for X (E-05)")
    a = ap.parse_args()
    src = os.path.abspath(a.html)
    out = os.path.abspath(a.out or re.sub(r"\.html?$", "", src) + ".pdf")
    report = {"html": src, "pdf": out, "ok": False}
    bin_ = chrome()
    if not bin_:
        report["error"] = "Chrome not found; fall back to the Artifact + Cmd-P path in visual-briefs.md"
        print(json.dumps(report, indent=1))
        return 1

    # 1. overflow probe on a temp copy in the same folder (keeps relative image paths working)
    html = open(src, encoding="utf-8").read()
    probed = html.replace("</body>", PROBE + "</body>") if "</body>" in html else html + PROBE
    fd, tmp = tempfile.mkstemp(suffix=".html", dir=os.path.dirname(src), prefix=".probe-")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(probed)
    try:
        dom = run(bin_, ["--window-size=1080,1350", "--dump-dom", "file://" + tmp]).stdout
    finally:
        os.remove(tmp)
    probe = parse_probe(dom)
    report["slides"] = probe["slides"]
    report["overflow"] = probe["problems"]

    # 2. render the original file
    r = run(bin_, ["--print-to-pdf=" + out, "file://" + src])
    if not os.path.exists(out):
        report["error"] = "PDF not written: " + (r.stderr or "")[-300:]
        print(json.dumps(report, indent=1))
        return 1

    # 3. verify pages and size (pure checks)
    pdf = open(out, "rb").read()
    report.update(pdf_verify(probe, pdf))

    # 4. optional stacked preview
    if a.png and probe["slides"]:
        h = probe["slides"] * 1350
        run(bin_, ["--screenshot=" + os.path.abspath(a.png), f"--window-size=1080,{h}", "file://" + src])
        report["preview_png"] = os.path.abspath(a.png)

    # 5. X export (E-05): one 1:1 PNG per slide — X has no PDF carousels
    if a.x and probe["slides"]:
        geom = x_export_geometry(1080, 1350)
        base = re.sub(r"\.pdf$", "", out)
        pngs = []
        for i in range(probe["slides"]):
            target = f"{base}-x-{i + 1:02d}.png"
            html_i = html.replace("</body>", x_export_js(i, geom) + "</body>") if "</body>" in html \
                else html + x_export_js(i, geom)
            fd, tmp_i = tempfile.mkstemp(suffix=".html", dir=os.path.dirname(src), prefix=f".x-export-{i + 1:02d}-")
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(html_i)
            try:
                run(bin_, [f"--screenshot={target}", "--hide-scrollbars",
                           f"--window-size={geom['viewport'][0]},{geom['viewport'][1]}", "file://" + tmp_i])
            finally:
                os.remove(tmp_i)
            if not os.path.exists(target):
                report.setdefault("x_export_errors", []).append(f"PNG not written: {target}")
                continue
            pngs.append(target)
        report["x_pngs"] = pngs

    report["ok"] = all(report["checks"].values())
    print(json.dumps(report, indent=1))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
