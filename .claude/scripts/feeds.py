#!/usr/bin/env python3
"""Feed layer, code half (S-02, YED-251) — pure stages for company/topic news feeds.

Stages, all pure and offline-testable:
  discover(website_html)      -> [feed_url]   link rel=alternate, then common paths
  parse(feed_xml)             -> [item]       RSS 2.0, Atom, YouTube (Atom + yt namespace)
  dedupe(items, seen_keys)    -> [item]       stable key = sha256 of the canonical URL
  render_digest(items, cos)   -> markdown     Friday digest, grouped by company, newest first

Network fetching sits behind fetch(url, timeout=8) and is never exercised by the
selftest — the live run belongs to a Claude Code session with Alex (lane F+C).
No writes anywhere: no tables, no migrations, no graph/Notion/HubSpot calls. The
feed_sources / feed_items DDL waits for ADR-12 and Alex. Public feeds and official
endpoints only — never LinkedIn or X scraping.

An item is a plain dict: {title, url, published (ISO-8601 UTC or None), summary,
feed (source feed URL), kind ("rss"|"atom"|"youtube")}.
"""
import hashlib
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser

ATOM = "{http://www.w3.org/2005/Atom}"
YT = "{http://www.youtube.com/xml/2015}"
MEDIA = "{http://search.yahoo.com/mrss/}"

# Checked in order when the page advertises no <link rel="alternate"> feed.
COMMON_FEED_PATHS = ["/feed", "/feed.xml", "/rss.xml", "/atom.xml", "/index.xml"]
FEED_TYPES = ("application/rss+xml", "application/atom+xml", "application/feed+json",
              "application/json+feed")
TRACKING_PARAMS = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
                   "gclid", "fbclid", "ref_src"}


# ---------------------------------------------------------------- discovery

class _FeedLinkParser(HTMLParser):
    """Collect hrefs of <link rel=alternate type=...> tags, in document order."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag != "link":
            return
        a = dict(attrs)
        rels = (a.get("rel") or "").lower().split()
        if "alternate" not in rels:
            return
        if (a.get("type") or "").lower() not in FEED_TYPES:
            return
        href = (a.get("href") or "").strip()
        if href:
            self.hrefs.append(href)


def discover(website_html: str, base_url: str | None = None) -> list[str]:
    """Feed URLs advertised by a page: <link rel=alternate> first, else common paths.

    Relative hrefs resolve against base_url when given. Pure: no fetching.
    """
    parser = _FeedLinkParser()
    try:
        parser.feed(website_html)
    except Exception as e:  # malformed HTML still deserves the common-path fallback
        print(f"feeds: discover: HTML unreadable ({e}); falling back to common paths",
              file=sys.stderr)
    urls: list[str] = []
    for href in parser.hrefs:
        urls.append(urllib.parse.urljoin(base_url, href) if base_url else href)
    if not urls:
        for path in COMMON_FEED_PATHS:
            urls.append(urllib.parse.urljoin(base_url, path) if base_url else path)
    return list(dict.fromkeys(urls))  # dedupe, keep order


# ---------------------------------------------------------------- parsing

def _published(*raw: str | None) -> str | None:
    """Normalize the first parseable date among raw candidates to ISO-8601 UTC."""
    for value in raw:
        if not value:
            continue
        value = value.strip()
        for parser in (parsedate_to_datetime, _iso):
            try:
                dt = parser(value)
            except (ValueError, TypeError):
                continue
            if dt is None:
                continue
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return None


def _iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _text(node: ET.Element | None) -> str:
    return (node.text or "").strip() if node is not None and node.text else ""


def _atom_entry(entry: ET.Element, kind: str) -> dict:
    link = ""
    for ln in entry.findall(f"{ATOM}link"):
        if ln.get("rel") in (None, "alternate"):
            link = (ln.get("href") or "").strip()
            if link:
                break
    summary = _text(entry.find(f"{ATOM}summary")) or _text(entry.find(f"{ATOM}content"))
    if kind == "youtube":
        desc = entry.find(f"{MEDIA}description")
        summary = _text(desc) or summary
    return {
        "title": _text(entry.find(f"{ATOM}title")),
        "url": link,
        "published": _published(_text(entry.find(f"{ATOM}published")),
                                _text(entry.find(f"{ATOM}updated"))),
        "summary": summary,
        "feed": "",  # filled by assign_feeds
        "kind": kind,
    }


def _rss_item(item: ET.Element) -> dict:
    return {
        "title": _text(item.find("title")),
        "url": (_text(item.find("link"))
                or _text(item.find("guid"))).strip(),
        "published": _published(_text(item.find("pubDate"))),
        "summary": _text(item.find("description")),
        "feed": "",
        "kind": "rss",
    }


def parse(feed_xml: str) -> list[dict]:
    """Parse an RSS 2.0, Atom or YouTube feed document into items, in feed order.

    Raises ValueError on XML that does not parse at all — never swallowed.
    """
    try:
        root = ET.fromstring(feed_xml)
    except ET.ParseError as e:
        raise ValueError(f"feeds: feed XML does not parse: {e}") from e
    if root.tag == "rss":
        return [_rss_item(i) for i in root.iter("item")]
    if root.tag == f"{ATOM}feed":
        kind = "youtube" if root.find(f".//{YT}videoId") is not None else "atom"
        return [_atom_entry(e, kind) for e in root.findall(f"{ATOM}entry")]
    raise ValueError(f"feeds: unrecognized feed root <{root.tag}> — not RSS 2.0 or Atom")


def assign_feeds(items: list[dict], feed_url: str) -> list[dict]:
    """Stamp the source feed URL onto items (parse() cannot know it)."""
    for item in items:
        item["feed"] = feed_url
    return items


# ---------------------------------------------------------------- dedupe

def canonical_url(url: str) -> str:
    """Canonical form for identity: lowercase scheme/host, no fragment, no default
    port, tracking params dropped, remaining params sorted, no trailing slash."""
    url = url.strip()
    parts = urllib.parse.urlsplit(url)
    host = (parts.hostname or "").lower()
    port = parts.port
    default = {"http": 80, "https": 443}.get(parts.scheme.lower())
    if port is not None and port != default:
        host = f"{host}:{port}"
    query = sorted((k, v) for k, v in
                    urllib.parse.parse_qsl(parts.query, keep_blank_values=True)
                    if k.lower() not in TRACKING_PARAMS)
    path = parts.path or "/"
    path = path.rstrip("/") or "/"
    return urllib.parse.urlunsplit((parts.scheme.lower(), host, path,
                                    urllib.parse.urlencode(query), ""))


def item_key(item: dict) -> str:
    """Stable identity of an item: sha256 hex of its canonical URL."""
    return hashlib.sha256(canonical_url(item["url"]).encode()).hexdigest()


def dedupe(items: list[dict], seen_keys: set[str]) -> list[dict]:
    """Items whose key is not in seen_keys, first occurrence wins, order kept.

    Does not mutate seen_keys — the caller adds item_key(i) for what it processed.
    """
    out, batch = [], set()
    for item in items:
        key = item_key(item)
        if key in seen_keys or key in batch:
            continue
        batch.add(key)
        out.append(item)
    return out


# ---------------------------------------------------------------- digest

def render_digest(items: list[dict], companies: dict[str, list[str]]) -> str:
    """Markdown digest: one section per company, newest first, source links.

    companies maps company name -> the feed URLs that belong to it; items whose
    feed is not listed land in "Unassigned". Pure formatting, no LLM calls.
    """
    if not items:
        return "No new items.\n"
    by_feed = {feed: name for name, feeds in companies.items() for feed in feeds}
    grouped: dict[str, list[dict]] = {}
    for item in items:
        grouped.setdefault(by_feed.get(item.get("feed", ""), "Unassigned"), []).append(item)

    def _stamp(item: dict) -> str:
        return item["published"] or "date unknown"

    lines = [f"# Feed digest — {len(items)} new item{'s' if len(items) != 1 else ''}", ""]
    for company in sorted(grouped):
        lines.append(f"## {company}")
        lines.append("")
        for item in sorted(grouped[company], key=_stamp, reverse=True):
            title = item["title"] or "(untitled)"
            lines.append(f"- [{title}]({item['url']}) — {_stamp(item)}")
            if item.get("summary"):
                lines.append(f"  {item['summary']}")
        lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


# ---------------------------------------------------------------- fetching

def fetch(url: str, timeout: int = 8) -> str:
    """The ONLY network step, for the live run — never called from the selftest.

    Reads at most 2 MiB; non-2xx or timeout raises (never swallowed).
    """
    request = urllib.request.Request(url, headers={"User-Agent": "empire-feed-layer/0.1"})
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
        if response.status != 200:
            raise RuntimeError(f"feeds: fetch {url}: HTTP {response.status}")
        return response.read(2 * 1024 * 1024).decode("utf-8", errors="replace")


# ---------------------------------------------------------------- selftest

def selftest() -> int:
    """Offline: inline XML/HTML fixtures only. fetch() must never run here."""
    ok = 0

    def check(label: str, good: bool) -> None:
        nonlocal ok
        ok += good
        print(f"  {'✓' if good else '✗'} {label}")

    # --- discover
    page = """<html><head>
      <link rel="alternate" type="application/rss+xml" title="b" href="/blog/feed.xml">
      <link rel="alternate" type="application/atom+xml" href="https://ex.com/atom.xml">
      <link rel="stylesheet" href="/css.css">
    </head></html>"""
    found = discover(page, "https://example.com")
    check("discover: link tags beat common paths, in order, resolved",
          found == ["https://example.com/blog/feed.xml", "https://ex.com/atom.xml"])
    check("discover: no links -> common paths against base",
          discover("<html><head></head></html>", "https://example.com")
          == [f"https://example.com{p}" for p in COMMON_FEED_PATHS])
    check("discover: no links, no base -> relative common paths",
          discover("") == COMMON_FEED_PATHS)

    # --- parse: RSS 2.0
    rss = """<rss version="2.0"><channel><title>Blog</title>
      <item><title>Post &amp; One</title><link>https://ex.com/p1?utm_source=x</link>
        <pubDate>Wed, 29 Oct 2026 10:00:00 GMT</pubDate>
        <description><![CDATA[Body <b>one</b>]]></description></item>
      <item><title>Post Two</title><link>https://ex.com/p2</link></item>
    </channel></rss>"""
    items = parse(rss)
    check("parse: rss item count", len(items) == 2)
    check("parse: rss entity decode + CDATA summary",
          items[0]["title"] == "Post & One" and items[0]["summary"] == "Body <b>one</b>")
    check("parse: rss RFC-822 date -> ISO UTC",
          items[0]["published"] == "2026-10-29T10:00:00Z")
    check("parse: rss missing pubDate -> None", items[1]["published"] is None)
    check("parse: rss kind", all(i["kind"] == "rss" for i in items))

    # --- parse: Atom
    atom = """<feed xmlns="http://www.w3.org/2005/Atom">
      <entry><title>Entry One</title>
        <link rel="alternate" href="https://ex.com/a1"/>
        <published>2026-10-28T09:30:00Z</published>
        <summary>S one</summary></entry>
      <entry><title>Entry Two</title>
        <link href="https://ex.com/a2"/>
        <updated>2026-10-29T08:00:00+02:00</updated></entry>
    </feed>"""
    atom_items = parse(atom)
    check("parse: atom entries, rel=alternate then bare link",
          [i["url"] for i in atom_items] == ["https://ex.com/a1", "https://ex.com/a2"])
    check("parse: atom updated-with-offset -> ISO UTC",
          atom_items[1]["published"] == "2026-10-29T06:00:00Z")
    check("parse: atom missing summary -> empty",
          atom_items[1]["summary"] == "")

    # --- parse: YouTube
    yt = """<feed xmlns="http://www.w3.org/2005/Atom"
         xmlns:yt="http://www.youtube.com/xml/2015"
         xmlns:media="http://search.yahoo.com/mrss/">
      <entry><yt:videoId>abc123</yt:videoId><title>Build log</title>
        <link rel="alternate" href="https://youtube.com/watch?v=abc123"/>
        <published>2026-10-27T12:00:00Z</published>
        <media:description>Walkthrough of the pipeline</media:description></entry>
    </feed>"""
    yt_items = parse(yt)
    check("parse: youtube kind + media:description",
          len(yt_items) == 1 and yt_items[0]["kind"] == "youtube"
          and yt_items[0]["summary"] == "Walkthrough of the pipeline")

    # --- parse: malformed
    try:
        parse("<rss><channel>")
        bad_parse = False
    except ValueError:
        bad_parse = True
    check("parse: malformed XML raises ValueError (never swallowed)", bad_parse)

    # --- canonical_url / dedupe
    check("canonical: tracking params, fragment, trailing slash, host case",
          canonical_url("HTTPS://Ex.com/P/?utm_source=x&b=2&a=1#top")
          == "https://ex.com/P?a=1&b=2")
    check("canonical: default port dropped, root keeps its slash",
          canonical_url("https://ex.com:443") == "https://ex.com/")
    i1 = {"title": "t", "url": "https://ex.com/p1?utm_source=x", "feed": "f"}
    i2 = {"title": "t", "url": "https://ex.com/p1", "feed": "f"}
    i3 = {"title": "t", "url": "https://ex.com/p3", "feed": "f"}
    check("dedupe: same canonical url across tracking variants -> once",
          dedupe([i1, i2, i3], set()) == [i1, i3])
    seen = {item_key(i1), item_key(i3)}
    check("dedupe: seen keys filtered, order kept",
          dedupe([i3, i1, i2], seen) == [])
    check("item_key: sha256 of canonical url",
          item_key(i1) == hashlib.sha256(b"https://ex.com/p1").hexdigest())

    # --- render_digest
    companies = {"Acme": ["https://ex.com/feed"], "Beta": ["https://beta.example/feed"]}
    a = {"title": "Old Acme", "url": "https://ex.com/1",
         "published": "2026-10-27T00:00:00Z", "summary": "", "feed": "https://ex.com/feed"}
    b = {"title": "New Acme", "url": "https://ex.com/2",
         "published": "2026-10-29T00:00:00Z", "summary": "fresh", "feed": "https://ex.com/feed"}
    c = {"title": "Beta post", "url": "https://beta.example/9",
         "published": None, "summary": "", "feed": "https://beta.example/feed"}
    d = {"title": "Orphan", "url": "https://orphan.example/1",
         "published": "2026-10-28T00:00:00Z", "summary": "", "feed": "https://orphan.example/feed"}
    md = render_digest([a, b, c, d], companies)
    check("digest: grouped by company, newest first",
          md.index("## Acme") < md.index("New Acme") < md.index("Old Acme") < md.index("## Beta"))
    check("digest: source links and summaries",
          "[New Acme](https://ex.com/2)" in md and "\n  fresh" in md)
    check("digest: unassigned feed lands in its own section",
          "## Unassigned" in md and md.index("## Beta") < md.index("## Unassigned"))
    check("digest: missing date renders as unknown",
          "date unknown" in md)
    check("digest: empty input -> explicit empty state",
          render_digest([], companies) == "No new items.\n")

    # --- fetch isolation: the selftest never performs network I/O
    check("fetch: exists behind one function, docstring bans selftest use",
          fetch.__doc__ is not None and "selftest" in fetch.__doc__)

    print(f"selftest: {ok}/24 passed")
    return 0 if ok == 24 else 1


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return selftest()
    print(__doc__.strip())
    print("\nThis module's live run (fetch + assign_feeds + a writing step) is the")
    print("session half of S-02 and belongs to Claude Code with Alex — no CLI yet.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
