"""Shared helpers: gh CLI wrapper with on-disk caching, IDoFT name parsing,
and a dependency-free Java method extractor."""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
 
ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / "cache"
CACHE.mkdir(parents=True, exist_ok=True)
 
 
class RateLimited(Exception):
    pass
 
 
def gh_api(endpoint, raw=False, paginate=False):
    """Call `gh api <endpoint>`; cache the result on disk. Returns parsed JSON
    (or text if raw=True). Returns None on 404/403-not-rate-limit (cached as a
    miss so reruns do not retry). Raises RateLimited if the API quota is spent."""
    key = hashlib.sha1(f"{endpoint}|{raw}|{paginate}".encode()).hexdigest()
    f = CACHE / f"{key}.json"
    if f.exists():
        d = json.loads(f.read_text(encoding="utf-8"))
        return d["value"]
 
    cmd = ["gh", "api", endpoint]
    if raw:
        cmd += ["-H", "Accept: application/vnd.github.raw+json"]
    if paginate:
        cmd += ["--paginate", "--slurp"]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        err = p.stderr.lower()
        if "rate limit" in err or "secondary" in err:
            raise RateLimited(p.stderr.strip())
        # 404 (deleted repo / file) and similar: cache as a miss
        f.write_text(json.dumps({"value": None, "error": p.stderr.strip()[:300]}), encoding="utf-8")
        return None
 
    if raw:
        value = p.stdout
    else:
        value = json.loads(p.stdout)
        if paginate:  # --slurp gives a list of pages; flatten list-of-lists
            value = [x for page in value for x in (page if isinstance(page, list) else [page])]
    f.write_text(json.dumps({"value": value}), encoding="utf-8")
    return value
 
 
PR_RE = re.compile(r"github\.com/([^/]+)/([^/]+)/pull/(\d+)")
 
 
def parse_pr_link(url):
    m = PR_RE.search(str(url))
    return (m.group(1), m.group(2), int(m.group(3))) if m else None
 
 
def parse_fqn(fqn):
    """'a.b.Outer$Inner.testX[param]' -> (package_path 'a/b', 'Outer', 'testX').
    Returns None if it cannot be parsed."""
    s = str(fqn).strip()
    s = re.split(r"[\[(]", s, maxsplit=1)[0]  # drop parameterized/descriptive suffix
    parts = s.split(".")
    if len(parts) < 2:
        return None
    method, cls, pkg = parts[-1], parts[-2], parts[:-2]
    cls = cls.split("$")[0]  # nested class -> file is the outer class
    return "/".join(pkg), cls, method
 
 
# ---------- Java method extraction (no parser dependency) ----------
 
def _skip_noncode(src, i):
    """If src[i:] starts a comment/string/char literal, return index after it, else i."""
    if src.startswith("//", i):
        j = src.find("\n", i)
        return len(src) if j == -1 else j
    if src.startswith("/*", i):
        j = src.find("*/", i + 2)
        return len(src) if j == -1 else j + 2
    if src.startswith('"""', i):  # text block
        j = src.find('"""', i + 3)
        return len(src) if j == -1 else j + 3
    if src[i] in "\"'":
        q, j = src[i], i + 1
        while j < len(src) and src[j] != q:
            j += 2 if src[j] == "\\" else 1
        return j + 1
    return i
 
 
def _match(src, i, open_c, close_c):
    """src[i] == open_c; return index of the matching close_c (string/comment aware)."""
    depth, j = 0, i
    while j < len(src):
        k = _skip_noncode(src, j)
        if k != j:
            j = k
            continue
        if src[j] == open_c:
            depth += 1
        elif src[j] == close_c:
            depth -= 1
            if depth == 0:
                return j
        j += 1
    return -1
 
 
def extract_methods(src, name):
    """Return a list of full source texts (annotations + signature + body) of
    every method *declaration* called `name`. More than one means overloads."""
    out = []
    for m in re.finditer(r"\b" + re.escape(name) + r"\s*\(", src):
        start = m.start()
        # declaration needs a return-type identifier right before the name
        before = src[:start].rstrip()
        if not before or not (before[-1].isalnum() or before[-1] in "_>]$"):
            continue
        prev_word = re.findall(r"[\w$]+$", before)
        if prev_word and prev_word[0] in ("return", "new", "else", "throw", "case"):
            continue
        close = _match(src, m.end() - 1, "(", ")")
        if close == -1:
            continue
        k = close + 1
        # skip whitespace / `throws X, Y` until `{` (declaration) or `;` (call/abstract)
        tail = re.match(r"\s*(?:throws\s+[^{;]+)?", src[k:])
        k += tail.end()
        if k >= len(src) or src[k] != "{":
            continue
        end = _match(src, k, "{", "}")
        if end == -1:
            continue
        # walk back to the start of the signature line, then absorb annotation lines
        line_start = src.rfind("\n", 0, start) + 1
        lines_before = src[:line_start].split("\n")
        while len(lines_before) >= 2 and re.fullmatch(r"\s*@[\w.]+(\(.*\))?\s*", lines_before[-2]):
            line_start -= len(lines_before[-2]) + 1
            lines_before.pop()
        out.append(src[line_start:end + 1])
    return out
 
 
def normalize(code):
    """Whitespace/comment-insensitive form, used to tell real changes from noise."""
    code = re.sub(r"//[^\n]*", "", code)
    code = re.sub(r"/\*.*?\*/", "", code, flags=re.S)
    return re.sub(r"\s+", " ", code).strip()