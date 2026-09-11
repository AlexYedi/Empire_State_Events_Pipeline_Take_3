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

def _clean(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def extract_epub(path: str) -> tuple[list[dict], dict]:
    """Return (sections, meta). Each section = {title, index, text}."""
    import ebooklib
    from ebooklib import epub
    from bs4 import BeautifulSoup
    book = epub.read_epub(path)
    meta = {}
    t = book.get_metadata("DC", "title")
    a = book.get_metadata("DC", "creator")
    meta["title"] = t[0][0] if t else os.path.basename(path)
    meta["author"] = a[0][0] if a else None
    sections = []
    for i, item in enumerate(book.get_items_of_type(ebooklib.ITEM_DOCUMENT)):
        soup = BeautifulSoup(item.get_content(), "html.parser")
        # section title = first heading, else the spine item name
        h = soup.find(["h1", "h2", "h3"])
        title = h.get_text(" ", strip=True) if h else (item.get_name() or f"section-{i}")
        text = _clean(soup.get_text("\n"))
        if len(text) > 40:  # skip empty/nav sections
            sections.append({"title": title[:200], "index": len(sections), "text": text})
    return sections, meta

def extract_pdf(path: str) -> tuple[list[dict], dict]:
    """Best-effort PDF: one section per page (locator = page number)."""
    import pymupdf as fitz
    doc = fitz.open(path)
    meta = {"title": (doc.metadata or {}).get("title") or os.path.basename(path),
            "author": (doc.metadata or {}).get("author")}
    sections = []
    for pno in range(doc.page_count):
        text = _clean(doc.load_page(pno).get_text("text"))
        if len(text) > 40:
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
