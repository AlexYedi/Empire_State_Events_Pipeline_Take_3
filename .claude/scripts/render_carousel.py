#!/usr/bin/env python3
"""Render a carousel HTML file to an upload-ready 4:5 PDF and verify it (YED-259).

The deterministic half of carousel work, so a render can't "look done" and still be wrong:
  1. overflow check — loads the page in headless Chrome with a small probe script and reports, per
     slide, any element that spills past the 1080x1350 frame or any slide whose content overflows;
  2. PDF render — headless Chrome --print-to-pdf (method in content-patterns/visual-briefs.md);
  3. verify — page count equals the number of .slide elements and every page is 810x1013 pt;
  4. preview — optional PNG of the stacked slides for a visual check.

Prints a JSON report; exit 0 only if every check passes.

Usage: render_carousel.py <in.html> [--out out.pdf] [--png preview.png]
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("html")
    ap.add_argument("--out")
    ap.add_argument("--png")
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
    m = re.search(r'<meta name="render-probe" content="([^"]*)"', dom)
    probe = json.loads(m.group(1).replace("&quot;", '"').replace("&amp;", "&")) if m else {"slides": None, "problems": ["probe did not run"]}
    report["slides"] = probe["slides"]
    report["overflow"] = probe["problems"]

    # 2. render the original file
    r = run(bin_, ["--print-to-pdf=" + out, "file://" + src])
    if not os.path.exists(out):
        report["error"] = "PDF not written: " + (r.stderr or "")[-300:]
        print(json.dumps(report, indent=1))
        return 1

    # 3. verify pages and size
    pdf = open(out, "rb").read()
    pages = len(re.findall(rb"/Type\s*/Page[^s]", pdf))
    boxes = set(re.findall(rb"/MediaBox\s*\[\s*0\s+0\s+([\d.]+)\s+([\d.]+)\s*\]", pdf))
    report["pdf_pages"] = pages
    report["page_sizes_pt"] = sorted({f"{float(w):.0f}x{float(h):.0f}" for w, h in boxes})
    size_ok = report["page_sizes_pt"] == ["810x1013"]
    count_ok = probe["slides"] is not None and pages == probe["slides"]

    # 4. optional stacked preview
    if a.png and probe["slides"]:
        h = probe["slides"] * 1350
        run(bin_, ["--screenshot=" + os.path.abspath(a.png), f"--window-size=1080,{h}", "file://" + src])
        report["preview_png"] = os.path.abspath(a.png)

    report["checks"] = {"no_overflow": not probe["problems"], "page_count_matches_slides": count_ok, "pages_are_4x5": size_ok}
    report["ok"] = all(report["checks"].values())
    print(json.dumps(report, indent=1))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
