"""Controlled perturbations of a single Java test method, for causal-consistency
experiments on ML flaky-test classifiers.

Input is the method source that extract_pairs.py writes to pre.java / post.java. The
transformations are pure functions of that string: nothing here loads a model, touches the
network or modifies existing scripts. Every attempt (successful, inapplicable or invalid)
is returned as a `Variant` record so a complete manifest can be written.

Experimental suites
-------------------
  suite         fix_kind   what it does                                       expected
  ------------  ---------  -------------------------------------------------  ---------------
  invariance    none       behaviour-preserving edits (rename, whitespace,    unchanged
                           comments, dead code)
  fake_fix      fake       inserts fix-looking, side-effect-free code that    unchanged
                           never touches the suspected cause
  token_probe   none       adds category vocabulary in a COMMENT only         unchanged
  real_fix      real_fix   removes a statically-verified unordered-           confidence_drop
                           collection source (reversal)
  real_cause    real_cause introduces a cause: Linked* -> Hash* (sensitivity) confidence_rise
                           or removal of synchronized blocks in
                           multithreaded tests (experimental)
  specificity   none       edits collections that never feed order-sensitive   unchanged
                           code while the observed unordered cause is kept

"unchanged" means: the classifier should not move. A prediction change is evidence of
sensitivity to a surface feature; it is NOT evidence of (or against) causal understanding.

Safety model
------------
There is no Java parser dependency (tree-sitter / JavaParser are not installed in the
project environment); `javalex` tokenizes exactly and recognises declarations with
conservative token patterns. Whenever a construct is not understood the transformation
is REFUSED with an explicit reason instead of producing possibly-invalid code. Each
produced variant is additionally re-lexed and a token-level post-condition is checked
(e.g. "identical code tokens", "pure insertion", "only the recorded sites changed").
Compilation is checked separately by javacheck.py (optional, differential).
"""
import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Callable, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from javalex import (KEYWORDS, Unsupported, analyze_method, collect_decls, line_col,
                     nested_class_ranges, parse_type, skip_annotation)

TRANSFORM_VERSION = "2"

# FlakyLens class ids; the category a snippet "targets".
CAT = {"async wait": 0, "concurrency": 1, "time": 2,
       "unordered collections": 3, "test order dependency": 4}
PROBE_CATS = list(CAT) + ["non-flaky"]


@dataclass
class Variant:
    name: str
    suite: str
    expected: str                 # unchanged | confidence_drop | confidence_rise
    target_category: str          # FlakyLens category the edit is aimed at ("" if none)
    code: Optional[str]           # modified source; None when the transformation did not apply
    fix_kind: str = "none"        # none | fake | real_fix | real_cause
    test_id: str = ""
    base: str = ""                # pre | post
    status: str = "ok"            # ok | inapplicable | invalid
    reason: str = ""
    changes: list = field(default_factory=list)
    tokens_introduced: list = field(default_factory=list)
    tokens_already_present: list = field(default_factory=list)
    mechanism_evidence: list = field(default_factory=list)
    notes: list = field(default_factory=list)
    post_check: str = ""
    original_sha1: str = ""
    variant_sha1: str = ""
    seed: str = ""                # all transformations are deterministic; no RNG is used
    compile_checked: bool = False
    compile_ok: Optional[bool] = None
    compile_mode: str = ""
    compile_detail: str = ""
    validated_by: str = "automatic_structural"
    manual_review: str = "not_done"
    transform_version: str = TRANSFORM_VERSION


@dataclass
class Out:
    code: Optional[str] = None
    reason: str = ""
    changes: list = field(default_factory=list)
    tokens: list = field(default_factory=list)
    already: list = field(default_factory=list)
    notes: list = field(default_factory=list)
    evidence: list = field(default_factory=list)
    post: str = ""
    allowed: set = field(default_factory=set)      # ct indices a "replace"/"deletion" may touch
    mapping: dict = field(default_factory=dict)     # for "rename"


@dataclass
class Transform:
    name: str
    suite: str
    fix_kind: str
    expected: str
    target: str
    fn: Callable
    doc: str
    experimental: bool = False


class Ctx:
    def __init__(self, src):
        self.src = src
        self.m = analyze_method(src)
        self.ct = self.m.ct
        self.ids = {t.text for t in self.ct if t.kind == "ident"}
        self.nl = "\r\n" if "\r\n" in src else "\n"
        self.lo, self.hi = self.m.body_open + 1, self.m.body_close


def sha1(s):
    return hashlib.sha1(s.encode("utf-8", "replace")).hexdigest()[:12]


# ------------------------------------------------------------------ text helpers
def body_span(code):
    """(offset of the body '{', offset of its matching '}'), or None."""
    try:
        m = analyze_method(code)
    except Unsupported:
        return None
    return m.ct[m.body_open].start, m.ct[m.body_close].start


def well_formed(code):
    try:
        analyze_method(code)
    except Unsupported:
        return False
    return True


def _line_indent(src, off):
    ls = src.rfind("\n", 0, off) + 1
    return re.match(r"[ \t]*", src[ls:]).group(0)


def _body_indent(ctx):
    bo = ctx.ct[ctx.m.body_open]
    mm = re.match(r"[ \t]*\r?\n(?:[ \t]*\r?\n)*([ \t]+)\S", ctx.src[bo.end:])
    return mm.group(1) if mm else _line_indent(ctx.src, bo.start) + "    "


def apply_edits(src, edits):
    """edits: iterable of (start, end, replacement); must not overlap."""
    for s, e, r in sorted(edits, key=lambda x: x[0], reverse=True):
        src = src[:s] + r + src[e:]
    return src


def insert_at_start(ctx, lines):
    src, bo = ctx.src, ctx.ct[ctx.m.body_open]
    ind = _body_indent(ctx)
    rest = src[bo.end:]
    block = "".join(ctx.nl + ind + ln for ln in lines)
    if not re.match(r"[ \t]*\r?\n", rest):       # inline body: keep a // comment from swallowing code
        block += ctx.nl + ind
    return src[:bo.end] + block + rest


def insert_at_end(ctx, lines):
    src, cb = ctx.src, ctx.ct[ctx.m.body_close]
    ind = _body_indent(ctx)
    ls = src.rfind("\n", 0, cb.start) + 1
    block = "".join(ind + ln + ctx.nl for ln in lines)
    if src[ls:cb.start].strip() == "":
        return src[:ls] + block + src[ls:]
    brace_ind = _line_indent(src, cb.start)
    return src[:cb.start] + ctx.nl + block + brace_ind + src[cb.start:]


def fresh_name(ctx, base, taken=()):
    if base not in ctx.ids and base not in taken:
        return base
    i = 0
    while f"{base}{i}" in ctx.ids or f"{base}{i}" in taken:
        i += 1
    return f"{base}{i}"


def _last_statement_start(ctx):
    """ct index of the first token of the body's last top-level statement (or None)."""
    ct, m = ctx.ct, ctx.m
    start, j, pending = None, ctx.lo, True
    while j < ctx.hi:
        if pending:
            start, pending = j, False
        t = ct[j].text
        if t in ("(", "[", "{") and j in m.fwd:
            j = m.fwd[j] + 1
            if t == "{" and not (j < ctx.hi and ct[j].text in ("else", "catch", "finally", "while")):
                pending = True
            continue
        if t == ";":
            pending = True
        j += 1
    return start if start is not None and start < ctx.hi else None


def _end_insertion_unsafe(ctx):
    s = _last_statement_start(ctx)
    if s is None:
        return None
    ct = ctx.ct
    first = ct[s].text
    if first in ("return", "throw", "break", "continue", "yield"):
        return f"body ends with '{first}': code inserted after it would be unreachable"
    if first == "while" and ct[s + 1].text == "(" and ct[s + 2].text == "true" and ct[s + 3].text == ")":
        return "body ends with an infinite loop"
    if first == "for" and ct[s + 1].text == "(" and ct[s + 2].text == ";" and ct[s + 3].text == ";":
        return "body ends with an infinite loop"
    return None


# ------------------------------------------------------------- mechanism evidence
EVIDENCE = {
    "unordered collections": {"HashMap", "HashSet", "keySet", "entrySet", "getDeclaredFields",
                              "getDeclaredMethods", "Hashtable"},
    "async wait": {"sleep", "wait", "await", "Future", "CompletableFuture", "Awaitility",
                   "TimeUnit", "timeout", "join"},
    "concurrency": {"Thread", "Runnable", "ExecutorService", "Executors", "Executor", "synchronized",
                    "AtomicInteger", "AtomicLong", "ConcurrentHashMap", "CountDownLatch",
                    "parallelStream", "parallel", "ReentrantLock", "ForkJoinPool", "Callable"},
    "time": {"currentTimeMillis", "nanoTime", "Date", "Calendar", "Instant", "LocalDate",
             "LocalDateTime", "ZonedDateTime", "Clock", "TimeZone", "SimpleDateFormat", "now"},
    "test order dependency": set(),   # shared state across tests is not visible in one method
}


def mechanism_evidence(ctx, cat):
    """Heuristic, code-token-only indicators that the method plausibly involves `cat`."""
    ids = {t.text for t in ctx.ct[ctx.lo:ctx.hi] if t.kind == "ident"}
    return sorted(ids & EVIDENCE.get(cat, set()))


# ------------------------------------------------------------- invariance family
def _scope_end(ctx, d, enc_paren, enc_brace):
    """ct index where declaration `d` goes out of scope, or None if it cannot be determined."""
    ct, m = ctx.ct, ctx.m
    if d.kind in ("local", "lambda", "pattern", "param_like"):
        b = enc_brace[d.idx]
        return m.fwd[b] if b != -1 else m.body_close
    op = enc_paren[d.idx]
    s = m.fwd[op] + 1
    if ct[s].text == "{":
        return m.fwd[s]
    if d.kind == "catch" or ct[s].text in {"for", "if", "while", "do", "try", "switch", "synchronized", "else"}:
        return None
    j = s
    while j < ctx.hi:
        if ct[j].text in ("(", "[", "{") and j in m.fwd:
            j = m.fwd[j] + 1
            continue
        if ct[j].text == ";":
            return j
        j += 1
    return None


def t_rename_locals(ctx):
    """Rename local variables to v0, v1, ... Names that cannot be renamed provably safely
    are left alone and listed in `notes` with the reason."""
    ct, m, lo, hi = ctx.ct, ctx.m, ctx.lo, ctx.hi
    for i in range(lo, hi):
        if ct[i].text == "case":
            k = parse_type(ct, i + 1, hi)
            if k != -1 and k < hi and ct[k].kind == "ident" and ct[k].text not in KEYWORDS:
                raise Unsupported("switch pattern matching (case Type name) is not supported")
    decls, enc_paren, enc_brace = collect_decls(ct, lo, hi, m.fwd, m.back)
    nested = nested_class_ranges(ct, lo, hi, m.fwd)

    def in_nested(i):
        return any(a < i < b for a, b in nested)

    excluded = {}
    shadow = {d.name for d in decls if in_nested(d.idx)}
    for a, b in nested:
        for i in range(a + 1, b):
            if (ct[i].text == "(" and i in m.fwd and ct[i - 1].kind == "ident"
                    and ct[i - 1].text not in KEYWORDS and ct[i - 2].text != "new"
                    and m.fwd[i] + 1 < len(ct) and ct[m.fwd[i] + 1].text in ("{", "throws")):
                shadow.add(ct[i - 1].text)
    by_name = {}
    for d in decls:
        if not in_nested(d.idx):
            by_name.setdefault(d.name, []).append(d)
    cand = {}
    for name, ds in by_name.items():
        if name in m.params:
            excluded[name] = "same name as a method parameter"
        elif name in shadow:
            excluded[name] = "re-declared or shadowed inside an anonymous/local class"
        elif not (name[0].islower() or name[0] == "_"):
            excluded[name] = "does not look like a local variable name"
        else:
            cand[name] = ds
    scopes = {}
    for name, ds in list(cand.items()):
        ends = []
        for d in ds:
            e = _scope_end(ctx, d, enc_paren, enc_brace)
            if e is None:
                excluded[name] = "declared in a statement whose extent cannot be determined (unbraced compound body)"
                break
            ends.append((d.idx, e))
        else:
            scopes[name] = ends
    cand = {n: d for n, d in cand.items() if n in scopes}

    ann_ranges = []
    for i in range(lo, hi):
        if ct[i].text == "@" and ct[i + 1].text != "interface":
            e = skip_annotation(ct, i, m.fwd)
            if ct[e - 1].text == ")":
                ann_ranges.append((m.back[e - 1], e - 1))
    decl_idx = {d.idx for ds in cand.values() for d in ds}
    occ = {}
    for i in range(lo, hi):
        t = ct[i]
        if t.kind != "ident" or t.text not in cand or t.text in excluded:
            continue
        name = t.text
        if i in decl_idx:
            occ.setdefault(name, []).append(i)
            continue
        prev, nxt = ct[i - 1].text, ct[i + 1].text
        if prev in (".", "::", "@", "new", "break", "continue") or nxt == "(":
            continue
        if nxt == ":" and prev in (";", "{", "}"):
            continue
        if prev == "case":
            excluded[name] = "also used as a case label"
            continue
        if any(a < i < b for a, b in ann_ranges):
            if nxt == "=" and prev in ("(", ","):
                continue
            excluded[name] = "referenced inside an annotation"
            continue
        if not any(di < i <= se for di, se in scopes[name]):
            excluded[name] = "used outside every scope that declares it (probably a field)"
            continue
        occ.setdefault(name, []).append(i)
    renamable = [n for n in sorted(cand, key=lambda n: cand[n][0].idx) if n not in excluded]
    if not renamable:
        why = "; ".join(f"{n}: {r}" for n, r in sorted(excluded.items())) or "no local variables declared"
        raise Unsupported(f"no safely renamable locals ({why})")
    mapping, taken = {}, set()
    for n in renamable:
        k = 0
        while f"v{k}" in ctx.ids or f"v{k}" in taken:
            k += 1
        mapping[n] = f"v{k}"
        taken.add(mapping[n])
    edits, changes = [], []
    for n in renamable:
        for i in occ[n]:
            edits.append((ct[i].start, ct[i].end, mapping[n]))
        line, _ = line_col(ctx.src, ct[cand[n][0].idx].start)
        changes.append({"kind": "rename", "old": n, "new": mapping[n], "declared_line": line,
                        "occurrences": len(occ[n])})
    notes = [f"not renamed: {n} ({r})" for n, r in sorted(excluded.items())]
    return Out(apply_edits(ctx.src, edits), changes=changes, notes=notes, post="rename", mapping=mapping)


def _protected_line_starts(ctx):
    """Offsets of lines that start inside a text block (their leading whitespace is content)."""
    prot = set()
    for t in ctx.m.toks:
        if t.kind == "textblock":
            for mm in re.finditer(r"\n", ctx.src[t.start:t.end]):
                prot.add(t.start + mm.end())
    return prot


def _reindent(ctx, leading):
    prot, out, pos = _protected_line_starts(ctx), [], 0
    for line in ctx.src.split("\n"):
        new = line
        if pos not in prot:
            mm = re.match(r" +", line)
            if mm:
                n = len(mm.group(0))
                new = leading(n) + line[n:]
        out.append(new)
        pos += len(line) + 1
    return "\n".join(out)


def t_reindent_tabs(ctx):
    out = _reindent(ctx, lambda n: "\t" * (n // 4) + " " * (n % 4))
    return Out(out, post="same_tokens") if out != ctx.src else Out(reason="no 4-space indentation to convert")


def t_reindent_2space(ctx):
    out = _reindent(ctx, lambda n: " " * (n // 4 * 2 + n % 4))
    return Out(out, post="same_tokens") if out != ctx.src else Out(reason="no 4-space indentation to convert")


def t_neutral_comment(ctx):
    return Out(insert_at_start(ctx, ["// reviewed"]), tokens=["reviewed"], post="same_tokens")


def t_trailing_comment(ctx):
    ct, src = ctx.ct, ctx.src
    j = ctx.lo
    while j < ctx.hi:
        if ct[j].text in ("(", "[", "{") and j in ctx.m.fwd:
            j = ctx.m.fwd[j] + 1
            continue
        if ct[j].text == ";":
            le = src.find("\n", ct[j].end)
            le = len(src) if le == -1 else le
            if src[ct[j].end:le].strip() == "":
                return Out(src[:ct[j].end] + " // ok" + src[ct[j].end:], tokens=["ok"], post="same_tokens")
        j += 1
    return Out(reason="no top-level statement ends its line")


def t_strip_comments(ctx):
    src = ctx.src
    comments = [t for t in ctx.m.toks if t.kind == "comment"]
    if not comments:
        return Out(reason="no comments to remove")
    edits = []
    for t in comments:
        ls = src.rfind("\n", 0, t.start) + 1
        le = src.find("\n", t.end)
        le = len(src) if le == -1 else le
        before, after = src[ls:t.start], src[t.end:le]
        if before.strip() == "" and after.strip() == "":
            edits.append((ls, min(le + 1, len(src)), ""))
        elif t.text.startswith("//"):
            edits.append((t.start - (len(before) - len(before.rstrip(" \t"))), t.end, ""))
        else:   # keep tokens separated: `a-/**/-b` must not become `a--b`
            prev_ws = t.start == 0 or src[t.start - 1].isspace()
            next_ws = t.end >= len(src) or src[t.end].isspace()
            edits.append((t.start, t.end, "" if prev_ws or next_ws else " "))
    return Out(apply_edits(src, edits), notes=[f"removed {len(comments)} comment(s)"], post="same_tokens")


def t_dead_code(ctx):
    name = fresh_name(ctx, "unusedCounter")
    line = f"int {name} = 0;"
    return Out(insert_at_start(ctx, [line]), changes=[{"kind": "insert", "where": "start", "code": [line]}],
               post="insertion")


# --------------------------------------------------------- token probes (comments only)
COMMENT_WORDS = {
    "async wait": "// wait for async result, poll until ready, sleep, timeout",
    "concurrency": "// thread safe, synchronized access, race condition, lock",
    "time": "// uses current time, timezone, date, clock",
    "unordered collections": "// iteration order of HashMap or HashSet, sorted output",
    "test order dependency": "// shared static state, depends on test execution order",
    "non-flaky": "// deterministic result, stable output, fixed seed, no flakiness",
}


def t_comment_words(cat, where):
    def fn(ctx):
        comment = COMMENT_WORDS[cat]
        if comment in ctx.src:
            return Out(reason="identical probe comment already present")
        words = [w.lower() for w in re.findall(r"[A-Za-z]+", comment)]
        low = ctx.src.lower()
        already = [w for w in words if re.search(r"\b" + re.escape(w) + r"\b", low)]
        if where == "start":
            code = insert_at_start(ctx, [comment])
        else:
            ind = re.match(r"[ \t]*", ctx.src).group(0)
            code = ind + comment + ctx.nl + ctx.src
        return Out(code, tokens=words, already=already, post="same_tokens",
                   evidence=mechanism_evidence(ctx, cat),
                   notes=["comment-only insertion; no executable code is touched"])
    return fn


# ------------------------------------------------ fake fixes: fix vocabulary, no effect
def _fake_lines(cat, ctx):
    if cat == "time":
        n = fresh_name(ctx, "fixedClock")
        return [f"java.time.Clock {n} = java.time.Clock.fixed(java.time.Instant.EPOCH, java.time.ZoneOffset.UTC);"]
    return {
        "unordered collections": ["java.util.Collections.sort(new java.util.ArrayList<String>());",
                                  "new java.util.LinkedHashMap<String, String>().size();"],
        "test order dependency": ["new java.util.HashMap<String, String>().clear();",
                                  "java.util.Collections.emptyMap().isEmpty();"],
        "concurrency": ["synchronized (new Object()) { }",
                        "new java.util.concurrent.locks.ReentrantLock().isLocked();"],
        "async wait": ["new java.util.concurrent.CountDownLatch(0).getCount();"],
    }[cat]


def t_fake_fix(cat, where):
    def fn(ctx):
        if "java" in ctx.ids:
            raise Unsupported("an identifier named 'java' would shadow the fully-qualified names")
        if where == "end":
            why = _end_insertion_unsafe(ctx)
            if why:
                return Out(reason=why)
        lines = _fake_lines(cat, ctx)
        code = insert_at_start(ctx, lines) if where == "start" else insert_at_end(ctx, lines)
        return Out(code, post="insertion",
                   tokens=sorted({w for ln in lines for w in re.findall(r"[A-Za-z]+", ln)}),
                   changes=[{"kind": "insert", "where": where, "code": lines}],
                   evidence=mechanism_evidence(ctx, cat),
                   notes=["inserted statements only use fully-qualified types and fresh names; "
                          "they never reference an existing identifier"])
    return fn


# ------------------------------------------------ real causes / fixes: unordered collections
HASH_TO_LINKED = {"HashMap": "LinkedHashMap", "HashSet": "LinkedHashSet"}
LINKED_TO_HASH = {v: k for k, v in HASH_TO_LINKED.items()}
COMPAT_DECLARED = {"Map", "HashMap", "AbstractMap", "Collection", "Set", "HashSet", "AbstractSet",
                   "AbstractCollection", "Iterable", "Object", "var"}
ORDER_METHODS = {"keySet", "entrySet", "values", "iterator", "stream", "parallelStream", "forEach",
                 "toArray", "toString", "spliterator", "listIterator"}
ORDER_NEUTRAL = {"put", "get", "containsKey", "containsValue", "contains", "add", "remove", "size",
                 "isEmpty", "clear", "getOrDefault", "putIfAbsent", "computeIfAbsent", "merge"}
SERIAL_CALLS = {"toJson", "writeValueAsString", "valueOf", "toString", "join", "asList", "copyOf",
                "println", "print", "printf", "format", "append", "serialize", "dump", "dumps",
                "ArrayList", "LinkedList", "Vector", "ArrayDeque"}


def _enclosing_callee(ctx, i):
    ct = ctx.ct
    depth, j = 0, i - 1
    while j >= ctx.lo:
        t = ct[j].text
        if t in (")", "]", "}"):
            depth += 1
        elif t in ("(", "[", "{"):
            if depth == 0:
                if t != "(":
                    return None
                k = j - 1
                if ct[k].text == ">":
                    d = 0
                    while k >= ctx.lo:
                        d += ct[k].text == ">"
                        d -= ct[k].text == "<"
                        if d == 0:
                            break
                        k -= 1
                    k -= 1
                return ct[k].text if ct[k].kind == "ident" else None
            depth -= 1
        j -= 1
    return None


def _observation(ctx, name, skip):
    """Classify every use of variable `name` (declarations in `skip` are ignored): strong
    order-sensitive evidence, order-neutral calls, and 'escapes' (anything else, which we
    cannot judge)."""
    ct = ctx.ct
    strong, neutral, escapes = [], 0, 0
    for i in range(ctx.lo, ctx.hi):
        t = ct[i]
        if t.kind != "ident" or t.text != name or i in skip:
            continue
        prev, nxt = ct[i - 1].text, ct[i + 1].text
        if prev == "." or nxt == "(":
            continue
        if nxt == "." and i + 2 < ctx.hi and ct[i + 2].kind == "ident":
            meth = ct[i + 2].text
            if meth in ORDER_METHODS:
                strong.append(f"call:{meth}")
            elif meth in ORDER_NEUTRAL:
                neutral += 1
            else:
                escapes += 1
            continue
        if prev == ":" and nxt == ")":
            strong.append("for-each")
            continue
        if "+" in (prev, nxt) and (ct[i - 2].kind in ("string", "textblock") or ct[i + 2].kind in ("string", "textblock")):
            strong.append("string-concat")
            continue
        if prev in ("(", ",") and nxt in (")", ","):
            callee = _enclosing_callee(ctx, i)
            if callee in SERIAL_CALLS:
                strong.append(f"arg-of:{callee}")
                continue
        escapes += 1
    return strong, neutral, escapes


def find_collection_sites(ctx, names):
    """Every `new [java.util.]<name>` instantiation in the body, with variable, declared type,
    order-observation evidence and compatibility for a hash<->linked swap."""
    ct, lo, hi, m = ctx.ct, ctx.lo, ctx.hi, ctx.m
    decls, _, _ = collect_decls(ct, lo, hi, m.fwd, m.back)
    by_idx = {d.idx: d for d in decls}
    sites = []
    for i in range(lo, hi):
        if ct[i].text != "new":
            continue
        j = i + 1
        if ct[j].text == "java" and ct[j + 1].text == "." and ct[j + 2].text == "util" and ct[j + 3].text == ".":
            j += 4
        if ct[j].kind != "ident" or ct[j].text not in names:
            continue
        s = {"idx": j, "from": ct[j].text, "to": names[ct[j].text], "var": None, "declared_type": None,
             "observed": False, "evidence": [], "escapes": 0, "neutral": 0, "usable": False, "skip": ""}
        s["line"], s["col"] = line_col(ctx.src, ct[j].start)
        s["offset"] = ct[j].start
        if ct[i - 1].text == "=" and ct[i - 2].kind == "ident" and ct[i - 2].text not in KEYWORDS:
            v = i - 2
            s["var"] = ct[v].text
            d = by_idx.get(v) or next((x for x in reversed(decls)
                                       if x.name == s["var"] and x.idx < v and x.type_start >= 0), None)
            if ct[v - 1].text == "." and d is None:
                s["skip"] = "assigned to a field; declared type unknown"
            elif d is None or d.type_start < 0:
                s["skip"] = "declaration of the target variable not found in the method"
            else:
                toks = ct[d.type_start:d.type_end]
                if any(t.text == "[" for t in toks):
                    s["skip"] = "array-typed variable"
                else:
                    base = []
                    for t in toks:
                        if t.text in ("<", "["):
                            break
                        if t.kind == "ident" and t.text != "final":
                            base.append(t.text)
                    s["declared_type"] = base[-1] if base else None
                    if s["declared_type"] not in COMPAT_DECLARED:
                        s["skip"] = f"declared type {s['declared_type']} is not compatible with the replacement"
            if not s["skip"]:
                strong, neutral, esc = _observation(ctx, s["var"], {v} | {x.idx for x in decls if x.name == s["var"]})
                s.update(evidence=sorted(set(strong)), observed=bool(strong), neutral=neutral, escapes=esc,
                         usable=True)
        else:
            s["skip"] = "instantiation is not assigned to a variable (inline argument or return value)"
        sites.append(s)
    return sites


def _site_changes(sites):
    return [{"kind": "replace_type", "line": s["line"], "col": s["col"], "offset": s["offset"],
             "from": s["from"], "to": s["to"], "variable": s["var"], "declared_type": s["declared_type"],
             "order_evidence": s["evidence"]} for s in sites]


def _swap(ctx, sites, notes):
    edits = [(ctx.ct[s["idx"]].start, ctx.ct[s["idx"]].end, s["to"]) for s in sites]
    return Out(apply_edits(ctx.src, edits), changes=_site_changes(sites), post="replace",
               allowed={s["idx"] for s in sites}, notes=notes,
               evidence=sorted({e for s in sites for e in s["evidence"]}))


def _skipped_notes(sites):
    return [f"not changed: line {s['line']} {s['from']}: "
            f"{s['skip'] or 'no order-sensitive use of the variable found'}" for s in sites]


def t_real_fix_unordered(ctx):
    sites = find_collection_sites(ctx, HASH_TO_LINKED)
    if not sites:
        return Out(reason="no HashMap/HashSet instantiation in the method")
    chosen = [s for s in sites if s["usable"] and s["observed"]]
    if not chosen:
        return Out(reason="HashMap/HashSet present but never observed in an order-sensitive way "
                          "(iteration, toString, serialization, string concatenation)",
                   notes=_skipped_notes(sites))
    rest = [s for s in sites if s not in chosen]
    return _swap(ctx, chosen, _skipped_notes(rest) +
                 ["static heuristic only: LinkedHash* fixes iteration order, not an order-dependent insertion sequence"])


def t_real_cause_unordered(ctx):
    sites = find_collection_sites(ctx, LINKED_TO_HASH)
    if not sites:
        return Out(reason="no LinkedHashMap/LinkedHashSet instantiation in the method")
    chosen = [s for s in sites if s["usable"] and s["observed"]]
    if not chosen:
        return Out(reason="LinkedHashMap/LinkedHashSet present but never observed in an order-sensitive way "
                          "(or declared with an incompatible type)", notes=_skipped_notes(sites))
    rest = [s for s in sites if s not in chosen]
    return _swap(ctx, chosen, _skipped_notes(rest) +
                 ["static heuristic only: whether this exposes real flakiness depends on how the order is asserted"])


def t_specificity_unordered(ctx):
    sites = find_collection_sites(ctx, HASH_TO_LINKED)
    cause = [s for s in sites if s["usable"] and s["observed"]]
    unrelated = [s for s in sites if s["usable"] and not s["observed"] and s["escapes"] == 0]
    if not cause:
        return Out(reason="no verified order-observed HashMap/HashSet (suspected cause) to preserve",
                   notes=_skipped_notes(sites))
    if not unrelated:
        return Out(reason="no collection that is provably unrelated to the cause (only used through "
                          "order-neutral calls such as put/get/contains/size)", notes=_skipped_notes(sites))
    out = _swap(ctx, unrelated, [f"cause preserved at line {s['line']} ({s['from']}, variable {s['var']})"
                                 for s in cause])
    out.evidence = sorted({e for s in cause for e in s["evidence"]})
    return out


THREAD_EVIDENCE = {"Thread", "Runnable", "ExecutorService", "Executors", "Executor", "parallelStream",
                   "parallel", "CompletableFuture", "ForkJoinPool", "Callable", "Timer"}


def t_real_cause_concurrency(ctx):
    ct, m = ctx.ct, ctx.m
    threads = sorted({t.text for t in ct[ctx.lo:ctx.hi] if t.kind == "ident"} & THREAD_EVIDENCE)
    edits, changes, removed = [], [], set()
    for i in range(ctx.lo, ctx.hi):
        if ct[i].text != "synchronized" or ct[i + 1].text != "(" or ct[i - 1].text not in (";", "{", "}"):
            continue
        c = m.fwd[i + 1]
        inner = ct[i + 2:c]
        if not inner or not all(t.kind == "ident" or t.text == "." for t in inner) or ct[c + 1].text != "{":
            continue
        edits.append((ct[i].start, ct[c + 1].start, ""))
        removed.update(range(i, c + 1))
        line, col = line_col(ctx.src, ct[i].start)
        changes.append({"kind": "remove_synchronized", "line": line, "col": col,
                        "monitor": "".join(t.text for t in inner)})
    if not edits:
        return Out(reason="no synchronized(<simple monitor>) { ... } block in the method")
    if not threads:
        return Out(reason="synchronized block present but no evidence of multithreading in the method "
                          "(removing it would not introduce a race)")
    return Out(apply_edits(ctx.src, edits), changes=changes, post="deletion", allowed=removed,
               evidence=threads, notes=["experimental: the data race is only plausible, not verified by execution"])


# ----------------------------------------------------------------- registry
def _registry():
    R = []

    def add(*a, **k):
        R.append(Transform(*a, **k))
    add("rename_locals", "invariance", "none", "unchanged", "", t_rename_locals,
        "scope-checked renaming of local variables to v0, v1, ...")
    add("reindent_tabs", "invariance", "none", "unchanged", "", t_reindent_tabs,
        "4-space indentation -> tabs (text blocks untouched)")
    add("reindent_2space", "invariance", "none", "unchanged", "", t_reindent_2space,
        "4-space indentation -> 2 spaces (text blocks untouched)")
    add("neutral_comment", "invariance", "none", "unchanged", "", t_neutral_comment,
        "adds '// reviewed' at the start of the body")
    add("trailing_comment", "invariance", "none", "unchanged", "", t_trailing_comment,
        "appends '// ok' to the first complete statement line")
    add("strip_comments", "invariance", "none", "unchanged", "", t_strip_comments,
        "removes every comment, keeping token separation")
    add("dead_code", "invariance", "none", "unchanged", "", t_dead_code,
        "adds an unused int local with a collision-free name")
    for cat in PROBE_CATS:
        slug = cat.replace(" ", "_").replace("-", "_")
        add(f"comment_words_{slug}", "token_probe", "none", "unchanged", cat, t_comment_words(cat, "start"),
            f"'{cat}' vocabulary in a comment at the start of the body")
        add(f"comment_words_{slug}_header", "token_probe", "none", "unchanged", cat,
            t_comment_words(cat, "header"), f"'{cat}' vocabulary in a comment above the method")
    for cat in CAT:
        slug = cat.replace(" ", "_")
        for where in ("start", "end"):
            add(f"fake_fix_{slug}_{where}", "fake_fix", "fake", "unchanged", cat, t_fake_fix(cat, where),
                f"no-op '{cat}' fix-vocabulary statements inserted at the {where} of the body")
    add("real_fix_unordered", "real_fix", "real_fix", "confidence_drop", "unordered collections",
        t_real_fix_unordered, "HashMap/HashSet -> LinkedHashMap/LinkedHashSet at order-observed sites only")
    add("real_cause_unordered", "real_cause", "real_cause", "confidence_rise", "unordered collections",
        t_real_cause_unordered, "LinkedHashMap/Set -> HashMap/Set at order-observed sites only")
    add("specificity_unordered_unrelated", "specificity", "none", "unchanged", "unordered collections",
        t_specificity_unordered,
        "Hash->Linked on collections never order-observed, while an order-observed Hash* cause is kept")
    add("real_cause_concurrency_unsync", "real_cause", "real_cause", "confidence_rise", "concurrency",
        t_real_cause_concurrency, "removes synchronized(monitor) blocks in tests that spawn threads",
        experimental=True)
    return R


REGISTRY = _registry()
BY_NAME = {t.name: t for t in REGISTRY}


# ------------------------------------------------------------ post-conditions
def _texts(ct):
    return [t.text for t in ct]


def _diff_idx(o, v):
    return [i for i, (a, b) in enumerate(zip(o, v)) if a != b]


def check_post(out, orig_ct, var_ct):
    """Token-level proof obligation for each transformation family -> (ok, description)."""
    o, v = _texts(orig_ct), _texts(var_ct)
    kind = out.post
    if kind == "same_tokens":
        return o == v, "identical code tokens"
    if kind == "insertion":
        if len(v) <= len(o):
            return False, "variant has no extra tokens"
        a = 0
        while a < len(o) and o[a] == v[a]:
            a += 1
        b = 0
        while b < len(o) - a and o[-1 - b] == v[-1 - b]:
            b += 1
        return a + b >= len(o), "pure insertion of one contiguous token run"
    if kind == "deletion":
        keep = [t for i, t in enumerate(o) if i not in out.allowed]
        return keep == v, "only the recorded tokens were removed"
    if kind == "replace":
        if len(o) != len(v):
            return False, "token count changed"
        diff = _diff_idx(o, v)
        return set(diff) == out.allowed, "only the recorded sites changed"
    if kind == "rename":
        if len(o) != len(v):
            return False, "token count changed"
        return all(o[i] in out.mapping and v[i] == out.mapping[o[i]] for i in _diff_idx(o, v)), \
            "only identifiers in the rename mapping changed"
    return True, "no post-condition"


# --------------------------------------------------------------- driver
def attempt_variants(code, suites=None, test_id="", base="", include_experimental=True):
    """One Variant record per registered transformation (successful or not). Deterministic."""
    records = []
    osha = sha1(code)
    selected = [t for t in REGISTRY if (not suites or t.suite in suites)
                and (include_experimental or not t.experimental)]
    try:
        ctx, src_error = Ctx(code), ""
    except Unsupported as e:
        ctx, src_error = None, str(e)
    for tr in selected:
        v = Variant(tr.name, tr.suite, tr.expected, tr.target, None, tr.fix_kind, test_id, base,
                    original_sha1=osha)
        if tr.experimental:
            v.notes.append("experimental transformation")
        records.append(v)
        if ctx is None:
            v.status, v.reason = "inapplicable", f"source not supported: {src_error}"
            continue
        try:
            out = tr.fn(ctx)
        except Unsupported as e:
            out = Out(reason=str(e))
        v.notes += out.notes
        v.mechanism_evidence = out.evidence
        if out.code is None:
            v.status, v.reason = "inapplicable", out.reason
            continue
        if out.code == code:
            v.status, v.reason = "inapplicable", "transformation produced no change"
            continue
        v.code, v.changes, v.tokens_introduced, v.tokens_already_present = out.code, out.changes, out.tokens, out.already
        v.variant_sha1, v.post_check = sha1(out.code), out.post
        try:
            vctx = analyze_method(out.code)
        except Unsupported as e:
            v.status, v.reason = "invalid", f"variant is not a well-formed method: {e}"
            continue
        ok, what = check_post(out, ctx.ct, vctx.ct)
        if not ok:
            v.status, v.reason = "invalid", f"post-condition failed ({what})"
            continue
        v.status = "ok"
    return records


def generate_variants(code, suites=None, include_experimental=True):
    """Only the successful variants (compatibility helper)."""
    return [v for v in attempt_variants(code, suites, include_experimental=include_experimental)
            if v.status == "ok"]


def apply_transform(name, code):
    """Run one named transformation; returns its Variant record."""
    for v in attempt_variants(code):
        if v.name == name:
            return v
    raise KeyError(name)


# ------------------------------------------------------------------- CLI
MANIFEST_COLS = ["test_id", "base", "variant_id", "name", "suite", "fix_kind", "target_category", "expected",
                 "status", "reason", "compile_checked", "compile_ok", "compile_mode", "compile_detail",
                 "validated_by", "manual_review", "post_check", "tokens_introduced", "tokens_already_present",
                 "mechanism_evidence", "changes", "notes", "original_sha1", "variant_sha1", "original_path",
                 "variant_path", "seed", "transform_version"]


def _load_pairs(pairs_dir):
    for d in sorted(Path(pairs_dir).iterdir()):
        if d.is_dir():
            meta = {}
            if (d / "meta.json").exists():
                meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
            yield d, meta


def main(argv=None):
    import pandas as pd
    ap = argparse.ArgumentParser(description="Generate controlled variants of every pair's pre.java "
                                 "(and optionally post.java). Writes variants.csv (consumable by "
                                 "score_variants.py), manifest.csv (EVERY attempt, including failures) "
                                 "and the variant .java files.")
    ap.add_argument("--pairs-dir", default="data/pairs")
    ap.add_argument("--out", default="data/results/variants.csv")
    ap.add_argument("--manifest", default="data/results/manifest.csv")
    ap.add_argument("--java-dir", default="data/results/variants", help="where variant .java files are written")
    ap.add_argument("--also-post", action="store_true", help="perturb post.java too")
    ap.add_argument("--suites", nargs="*", default=None)
    ap.add_argument("--no-experimental", action="store_true", help="skip transformations flagged experimental")
    ap.add_argument("--compile-check", action="store_true",
                    help="javac differential compile check (needs javac on PATH); variants that add "
                         "compile errors are marked invalid")
    ap.add_argument("--list", action="store_true", help="list the registered transformations and exit")
    a = ap.parse_args(argv)
    if a.list:
        for t in REGISTRY:
            print(f"{t.name:40s} {t.suite:12s} {t.fix_kind:10s} {t.expected:16s} {t.target or '-':22s} "
                  f"{'[experimental] ' if t.experimental else ''}{t.doc}")
        return 0

    rows, mrows = [], []
    java_dir = Path(a.java_dir)
    for d, meta in _load_pairs(a.pairs_dir):
        for base in (("pre", "post") if a.also_post else ("pre",)):
            f = d / f"{base}.java"
            if not f.exists():
                continue
            src = f.read_text(encoding="utf-8")
            common = dict(id=d.name, base=base, project=meta.get("project", ""),
                          idoft_category=meta.get("category", ""))
            rows.append(dict(common, variant=base, variant_id=f"{d.name}:{base}", suite="original",
                             fix_kind="none", expected="", target_category="", code=src))
            recs = attempt_variants(src, a.suites, d.name, base, not a.no_experimental)
            if a.compile_check:
                from javacheck import check_variants
                res = check_variants(src, {r.name: r.code for r in recs if r.code is not None})
                for r in recs:
                    if r.name in res:
                        r.compile_checked, r.compile_ok, r.compile_mode, r.compile_detail = res[r.name]
                        r.validated_by = "automatic_structural+javac_differential"
                        if r.compile_ok is False and r.status == "ok":
                            r.status, r.reason = "invalid", "variant introduces compile errors"
            for r in recs:
                vid = f"{d.name}:{base}:{r.name}"
                vpath = ""
                if r.code is not None:
                    p = java_dir / d.name / f"{base}__{r.name}.java"
                    p.parent.mkdir(parents=True, exist_ok=True)
                    p.write_text(r.code, encoding="utf-8", newline="")
                    vpath = str(p)
                m = asdict(r)
                m.update(variant_id=vid, original_path=str(f), variant_path=vpath)
                for k in ("tokens_introduced", "tokens_already_present", "mechanism_evidence", "changes", "notes"):
                    m[k] = json.dumps(m[k], ensure_ascii=False)
                mrows.append({c: m[c] for c in MANIFEST_COLS})
                if r.status == "ok":
                    rows.append(dict(common, variant=f"{base}:{r.name}", variant_id=vid, suite=r.suite,
                                     fix_kind=r.fix_kind, expected=r.expected, target_category=r.target_category,
                                     code=r.code))
    df, mf = pd.DataFrame(rows), pd.DataFrame(mrows, columns=MANIFEST_COLS)
    for p in (a.out, a.manifest):
        Path(p).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(a.out, index=False, encoding="utf-8")
    mf.to_csv(a.manifest, index=False, encoding="utf-8")
    print(f"wrote {len(df)} rows ({df['id'].nunique()} tests) to {a.out}")
    print(f"wrote manifest of {len(mf)} attempted transformations to {a.manifest}")
    if len(mf):
        print(mf.groupby(["suite", "status"]).size().unstack(fill_value=0).to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())
