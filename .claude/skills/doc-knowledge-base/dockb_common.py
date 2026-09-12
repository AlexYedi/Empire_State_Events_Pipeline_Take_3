"""YED-118 Document Knowledge Base — shared library.

Two decoupled stores:
  - Blob store: Cloudflare R2 (S3-compatible) — raw epub/PDF originals.
  - Vector index: Supabase pgvector (empire state ai, oicikjyzmxqfomrrqkvf) via REST.

Local embeddings: BAAI/bge-small-en-v1.5 (384-d). Query and ingest MUST use the
same model+version (pinned in EMBED_MODEL). See PRD .claude/references + ChatPRD.
"""
from __future__ import annotations
import hashlib, json, os, re, sys, urllib.request, urllib.error
from functools import lru_cache

# ---- config (pinned) --------------------------------------------------------
EMBED_MODEL = "BAAI/bge-small-en-v1.5"
EMBED_DIM = 384
# bge convention: prepend an instruction to QUERIES only (not passages).
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "
CHUNK_TARGET_TOKENS = 400      # stay under bge's 512 max-seq with headroom
CHUNK_HARD_CAP_TOKENS = 512
SUPABASE_REF = "oicikjyzmxqfomrrqkvf"
SUPABASE_BASE = f"https://{SUPABASE_REF}.supabase.co/rest/v1"
ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))), ".env")  # repo-root/.env (symlink ok)

# ---- env --------------------------------------------------------------------
@lru_cache(maxsize=1)
def env() -> dict:
    e = {}
    path = ENV_PATH if os.path.exists(ENV_PATH) else os.path.expanduser("~/.env")
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                e[k.strip()] = v.strip()
    return e

# ---- document library (local staging; R2 is the archive of record) ------
LIBRARY_SUBDIRS = ("books", "whitepapers", "filings", "other")

def library_dir() -> str:
    d = (env().get("DOC_LIBRARY_DIR") or os.environ.get("DOC_LIBRARY_DIR")
         or "~/Documents/Knowledge Library")
    return os.path.expanduser(d)

def resolve_doc_path(p: str) -> str:
    """Absolute/relative path as given; else resolve a bare filename against the library."""
    cand = os.path.abspath(os.path.expanduser(p))
    if os.path.isfile(cand):
        return cand
    lib = library_dir()
    for sub in ("",) + LIBRARY_SUBDIRS:
        c = os.path.join(lib, sub, p)
        if os.path.isfile(c):
            return c
    raise SystemExit(f"ERROR: not found: {p}\n  tried: {cand}\n"
                     f"  and library {lib}/{{{','.join(LIBRARY_SUBDIRS)}}}/")

# ---- embeddings (lazy singleton) -------------------------------------------
@lru_cache(maxsize=1)
def _model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(EMBED_MODEL)

def embed_passages(texts: list[str]) -> list[list[float]]:
    m = _model()
    vecs = m.encode(texts, normalize_embeddings=True, batch_size=32,
                    show_progress_bar=False)
    return [v.tolist() for v in vecs]

def embed_query(text: str) -> list[float]:
    m = _model()
    v = m.encode([QUERY_PREFIX + text], normalize_embeddings=True,
                 show_progress_bar=False)[0]
    return v.tolist()

def count_tokens(text: str) -> int:
    return len(_model().tokenizer.encode(text, add_special_tokens=False))

# ---- Supabase REST ----------------------------------------------------------
def _supa_headers(extra: dict | None = None) -> dict:
    k = env()["SUPABASE_API_KEY"]
    h = {"apikey": k, "Authorization": f"Bearer {k}", "Content-Type": "application/json"}
    if extra:
        h.update(extra)
    return h

def supa(method: str, path: str, body=None, headers=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(SUPABASE_BASE + path, data=data,
                                 headers=_supa_headers(headers), method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read().decode()
            return r.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Supabase {method} {path} -> {e.code}: {e.read().decode()[:500]}")

def vec_literal(v: list[float]) -> str:
    """pgvector text input for INSERT via PostgREST: '[0.1,0.2,...]'."""
    return "[" + ",".join(f"{x:.6f}" for x in v) + "]"

# ---- R2 (S3-compatible) -----------------------------------------------------
@lru_cache(maxsize=1)
def r2_client():
    import boto3
    from botocore.config import Config
    e = env()
    return boto3.client(
        "s3",
        endpoint_url=f"https://{e['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
        aws_access_key_id=e["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=e["R2_SECRET_ACCESS_KEY"],
        config=Config(signature_version="s3v4"), region_name="auto",
    )

def r2_put(key: str, data: bytes):
    r2_client().put_object(Bucket=env()["R2_BUCKET"], Key=key, Body=data)

# ---- text extraction --------------------------------------------------------
def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

# ---- ligature repair --------------------------------------------------------
# PDF extractors commonly split the fi/fl/ff ligature glyphs, producing
# "prefi ll" / "confi guration". Repair is dictionary-guided so genuine two-word
# phrases ("off the", "tradeoff between", "Muenninghoff et al.") are left alone.
# Measured on Inference Engineering: 175 repairs, 17 correct skips, 0 false joins.
LIG_PAT = re.compile(r"\b([A-Za-z]*(?:ffi|ffl|fi|fl|ff)) ([a-z]{1,12})\b")
_BARE_LIG = {"fi", "fl", "ff", "ffi", "ffl"}          # bare remnants: always rejoin
_RIGHT_STOP = {"et", "al", "etc"}                      # "Muenninghoff et al."
_COMPOUND_LEFT = {                                     # real words web2 lacks
    "tradeoff", "cutoff", "handoff", "takeoff", "payoff", "falloff", "standoff",
    "kickoff", "dropoff", "signoff", "layoff", "backoff", "writeoff", "selloff",
    "roundoff", "spinoff", "playoff", "runoff", "faceoff", "showoff", "tipoff"}

@lru_cache(maxsize=1)
def _dict_words() -> frozenset:
    for path in ("/usr/share/dict/words", "/usr/dict/words"):
        try:
            with open(path) as f:
                return frozenset(w.strip().lower() for w in f)
        except OSError:
            continue
    return frozenset()      # no dictionary -> repair only bare remnants

def repair_ligatures(text: str) -> str:
    words = _dict_words()
    def _sub(m):
        left, right = m.group(1), m.group(2)
        l, r, j = left.lower(), right.lower(), (left + right).lower()
        if r in _RIGHT_STOP:                    return m.group(0)
        if l in _BARE_LIG:                      return left + right
        if not words:                           return m.group(0)
        if j in words:                          return left + right
        if l in words or l in _COMPOUND_LEFT:   return m.group(0)
        return left + right                     # "prefi"+"ll" -> technical term
    return LIG_PAT.sub(_sub, text)

# ---- line-wrap hyphenation (PDF only: "Dif-\nfusion") ----------------------
# A hyphen immediately before a newline is the typesetter wrapping ONE word, so
# the fragments always rejoin; the only question is whether the hyphen survives.
# Same dictionary arbiter as the ligature rule: if the closed form is a word, drop
# the hyphen ("Dif-fusion" -> "Diffusion"); else keep it ("AI-native", "ARM-based").
# Measured on Inference Engineering: 477 wrap-hyphens, 310 closed, 167 kept.
HYPHEN_WRAP = re.compile(r"([A-Za-z]{2,})-\n([a-z]{2,})")

def repair_hyphenation(text: str) -> str:
    words = _dict_words()
    def _sub(m):
        a, b = m.group(1), m.group(2)
        if words and (a + b).lower() in words:
            return a + b                 # wrapped single word
        return f"{a}-{b}"                # genuine compound, newline removed
    return HYPHEN_WRAP.sub(_sub, text)

def _clean(text: str) -> str:
    text = text.replace("\xa0", " ")           # nbsp (epub headings use runs of these)
    text = repair_hyphenation(text)            # before whitespace collapse eats the \n
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return repair_ligatures(text.strip())

_HEAD_MARK = "\x00H\x00"
_NAV_TITLES = {"contents", "sommaire", "table of contents", "index", "toc"}

def extract_epub(path: str) -> tuple[list[dict], dict]:
    """Return (sections, meta), split at h1/h2/h3 so locators are section-precise.

    Chapter-title stub documents (a lone <h1>, e.g. "Chapter 5 Techniques") carry
    their name forward onto the following content document, giving locators like
    "Chapter 5 Techniques > 5.3 Caching". Nav/TOC documents are skipped.
    """
    import ebooklib
    from ebooklib import epub
    from bs4 import BeautifulSoup
    book = epub.read_epub(path)
    t = book.get_metadata("DC", "title")
    a = book.get_metadata("DC", "creator")
    meta = {"title": t[0][0] if t else os.path.basename(path),
            "author": a[0][0] if a else None}

    sections, chapter = [], None
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        props = (item.get_properties() or []) if hasattr(item, "get_properties") else []
        soup = BeautifulSoup(item.get_content(), "html.parser")
        raw = soup.get_text(" ", strip=True)
        h1 = soup.find("h1")
        h1_text = h1.get_text(" ", strip=True).replace("\xa0", " ").strip() if h1 else ""
        if "nav" in props or h1_text.lower() in _NAV_TITLES:
            continue                                   # table of contents
        if h1_text and len(raw) < 80:
            chapter = h1_text                          # chapter-title stub
            continue
        for h in soup.find_all(["h1", "h2", "h3"]):    # mark heading boundaries
            h.replace_with(_HEAD_MARK + h.get_text(" ", strip=True) + _HEAD_MARK)
        parts = soup.get_text("\n").split(_HEAD_MARK)
        blocks = []
        if parts[0].strip():
            blocks.append((None, parts[0]))            # text before the first heading
        for i in range(1, len(parts) - 1, 2):
            blocks.append((parts[i].strip(), parts[i + 1]))
        for head, body in blocks:
            body = _clean(body)
            if len(body) < 40:
                continue
            head = _clean(head) if head else None
            if head and chapter and head.lower() != chapter.lower():
                title = f"{chapter} > {head}"
            else:
                title = head or chapter or "Front Matter"
            sections.append({"title": title[:200], "index": len(sections), "text": body})
    return sections, meta

_LEADER = re.compile(r"\.{5,}")

def _is_front_matter(text: str) -> bool:
    """True for TOC / index pages — dot-leader lines ('Preface......11').

    These chunk into pure navigation noise that ranks in retrieval (a TOC page was
    the #1 hit for a KV-cache query in Phase A). Measured: flags exactly the 5 TOC
    pages of Inference Engineering, no content pages.
    """
    lines = [l for l in text.split("\n") if l.strip()]
    return sum(1 for l in lines if _LEADER.search(l)) >= 3

def extract_pdf(path: str) -> tuple[list[dict], dict]:
    """Best-effort PDF: one section per page (locator = page number)."""
    import pymupdf as fitz
    doc = fitz.open(path)
    meta = {"title": (doc.metadata or {}).get("title") or os.path.basename(path),
            "author": (doc.metadata or {}).get("author")}
    sections = []
    for pno in range(doc.page_count):
        text = _clean(doc.load_page(pno).get_text("text"))
        if len(text) <= 40 or _is_front_matter(text):
            continue
        sections.append({"title": f"p.{pno+1}", "index": pno, "text": text})
    return sections, meta

# ---- chunking (continuous token-window packer, cross-section overlap) -------
# Operates on a continuous stream of line-units tagged with their source
# section/page label, so chunks are uniformly ~CHUNK_TARGET_TOKENS, overlap
# across page boundaries, never exceed the cap, and carry a page/section-range
# locator. Preserves original text (units are original lines).

def _units(sections: list[dict]) -> list[tuple[str, str]]:
    """Flatten sections into (text, label) line-units; hard-split overlong lines."""
    out = []
    for sec in sections:
        label = sec["title"]
        for line in sec["text"].split("\n"):
            line = line.strip()
            if not line:
                continue
            if count_tokens(line) <= CHUNK_HARD_CAP_TOKENS:
                out.append((line, label))
            else:  # a single overlong line (dense table/TOC) -> word-split
                buf = []
                for w in line.split():
                    buf.append(w)
                    if count_tokens(" ".join(buf)) >= CHUNK_TARGET_TOKENS:
                        out.append((" ".join(buf), label)); buf = []
                if buf:
                    out.append((" ".join(buf), label))
    return out

def _locator(labels: list[str]) -> dict:
    first, last = labels[0], labels[-1]
    return {"section": first if first == last else f"{first}–{last}"}

def chunk_sections(sections: list[dict],
                   target: int = CHUNK_TARGET_TOKENS, overlap: int = 60) -> list[dict]:
    """Yield chunks: {content, locator:{section}, token_count}."""
    units = _units(sections)
    toks = [count_tokens(t) for t, _ in units]
    chunks, i, n = [], 0, len(units)
    while i < n:
        cur_tok, j = 0, i
        while j < n and (cur_tok + toks[j] <= target or j == i):
            cur_tok += toks[j]; j += 1
        content = "\n".join(units[k][0] for k in range(i, j))
        chunks.append({"content": content,
                       "locator": _locator([units[k][1] for k in range(i, j)]),
                       "token_count": count_tokens(content)})
        if j >= n:
            break
        # step back so the next chunk overlaps the tail by ~`overlap` tokens
        back, k = 0, j - 1
        while k > i and back < overlap:
            back += toks[k]; k -= 1
        i = max(k + 1, i + 1)
    return chunks
