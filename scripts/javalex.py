"""Dependency-free Java lexer plus the small amount of structural analysis that the
perturbation framework needs (method body, parameters, local declarations, nested class
bodies, bracket matching).

This is deliberately NOT a Java parser. It tokenizes exactly (comments, string/char
literals with escapes, text blocks) and recognises declarations with conservative token
patterns. Anything it cannot classify with confidence is reported (via `Unsupported` or
an explicit "unsafe" marker) so callers can refuse a transformation instead of guessing.
"""
import re
from dataclasses import dataclass


class LexError(ValueError):
    pass


class Unsupported(Exception):
    """Raised when the source uses a construct the analysis cannot handle safely."""


@dataclass(frozen=True)
class Tok:
    kind: str      # ws | comment | string | textblock | char | ident | number | punct
    text: str
    start: int
    end: int


KEYWORDS = frozenset("""abstract assert boolean break byte case catch char class const continue
default do double else enum extends final finally float for goto if implements import instanceof
int interface long native new package private protected public return short static strictfp
super switch synchronized this throw throws transient try void volatile while true false null
""".split())
PRIMS = frozenset("int long double float boolean char byte short".split())

_NUM = re.compile(
    r"(?:0[xX][0-9a-fA-F_]+(?:\.[0-9a-fA-F_]*)?(?:[pP][+-]?\d+)?|0[bB][01_]+|"
    r"(?:\d[\d_]*(?:\.[\d_]*)?|\.\d[\d_]*)(?:[eE][+-]?\d+)?)[lLfFdD]?")
_MULTI = ("...", "->", "::", "++", "--", "&&", "||", "==", "!=", "<=", ">=",
          "+=", "-=", "*=", "/=", "%=", "&=", "|=", "^=")


def _is_id_start(c):
    return c.isalpha() or c in "_$"


def _is_id_part(c):
    return c.isalnum() or c in "_$"


def tokenize(src):
    """Exact tokenization (concatenating every token's text reproduces `src`)."""
    toks, i, n = [], 0, len(src)
    while i < n:
        c = src[i]
        if c.isspace():
            j = i
            while j < n and src[j].isspace():
                j += 1
            toks.append(Tok("ws", src[i:j], i, j))
        elif src.startswith("//", i):
            j = src.find("\n", i)
            j = n if j == -1 else j
            if j > i and src[j - 1] == "\r":
                j -= 1
            toks.append(Tok("comment", src[i:j], i, j))
        elif src.startswith("/*", i):
            j = src.find("*/", i + 2)
            if j == -1:
                raise LexError(f"unterminated block comment at {i}")
            toks.append(Tok("comment", src[i:j + 2], i, j + 2))
            j += 2
        elif src.startswith('"""', i):
            j = i + 3
            while True:
                if j >= n:
                    raise LexError(f"unterminated text block at {i}")
                if src[j] == "\\":
                    j += 2
                elif src.startswith('"""', j):
                    j += 3
                    break
                else:
                    j += 1
            toks.append(Tok("textblock", src[i:j], i, j))
        elif c in "\"'":
            j = i + 1
            while True:
                if j >= n or src[j] == "\n":
                    raise LexError(f"unterminated literal at {i}")
                if src[j] == "\\":
                    j += 2
                elif src[j] == c:
                    j += 1
                    break
                else:
                    j += 1
            toks.append(Tok("string" if c == '"' else "char", src[i:j], i, j))
        elif _is_id_start(c):
            j = i + 1
            while j < n and _is_id_part(src[j]):
                j += 1
            toks.append(Tok("ident", src[i:j], i, j))
        elif c.isdigit() or (c == "." and i + 1 < n and src[i + 1].isdigit()):
            m = _NUM.match(src, i)
            j = m.end()
            toks.append(Tok("number", src[i:j], i, j))
        else:
            for op in _MULTI:
                if src.startswith(op, i):
                    j = i + len(op)
                    break
            else:
                j = i + 1
            toks.append(Tok("punct", src[i:j], i, j))
        i = j
    return toks


def code_tokens(toks):
    return [t for t in toks if t.kind not in ("ws", "comment")]


def bracket_maps(ct):
    """(open->close, close->open) for (), [], {} over code tokens; raises Unsupported if unbalanced."""
    pairs = {")": "(", "]": "[", "}": "{"}
    stack, fwd, back = [], {}, {}
    for i, t in enumerate(ct):
        if t.kind != "punct":
            continue
        if t.text in "([{":
            stack.append(i)
        elif t.text in pairs:
            if not stack or ct[stack[-1]].text != pairs[t.text]:
                raise Unsupported("unbalanced brackets")
            o = stack.pop()
            fwd[o], back[i] = i, o
    if stack:
        raise Unsupported("unbalanced brackets")
    return fwd, back


def line_col(src, offset):
    line = src.count("\n", 0, offset) + 1
    col = offset - (src.rfind("\n", 0, offset) + 1) + 1
    return line, col


# ---------------------------------------------------------------- type / declaration patterns
def skip_angle(ct, j, hi):
    """ct[j] == '<'. Index after the matching '>' if the contents look like type arguments."""
    depth = 0
    while j < hi:
        t = ct[j]
        if t.text == "<":
            depth += 1
        elif t.text == ">":
            depth -= 1
            if depth == 0:
                return j + 1
        elif not (t.kind == "ident" or t.text in {",", ".", "?", "&", "[", "]"}):
            return -1
        j += 1
    return -1


def parse_type(ct, i, hi):
    """Index just past a type starting at ct[i] (primitive, qualified, generic, array) or -1."""
    if i >= hi or ct[i].kind != "ident":
        return -1
    t = ct[i].text
    if t in PRIMS:
        j = i + 1
    elif t in KEYWORDS:
        return -1
    else:
        j = i + 1
        while True:
            if j < hi and ct[j].text == "<":
                k = skip_angle(ct, j, hi)
                if k == -1:
                    return -1
                j = k
            if (j + 1 < hi and ct[j].text == "." and ct[j + 1].kind == "ident"
                    and ct[j + 1].text not in KEYWORDS):
                j += 2
                continue
            break
    while j + 1 < hi and ct[j].text == "[" and ct[j + 1].text == "]":
        j += 2
    return j


def skip_annotation(ct, i, fwd):
    """ct[i] == '@'. Index just after the annotation (name and optional argument list)."""
    j = i + 1
    while j < len(ct) and ct[j].kind == "ident":
        j += 1
        if j < len(ct) and ct[j].text == ".":
            j += 1
        else:
            break
    if j < len(ct) and ct[j].text == "(" and j in fwd:
        j = fwd[j] + 1
    return j


@dataclass
class Decl:
    name: str
    idx: int          # index of the name token in `ct`
    kind: str         # local | for | try | catch | lambda | pattern | param_like
    type_start: int = -1
    type_end: int = -1


STMT_PREV = frozenset({";", "{", "}", "(", ",", ":"})
_FOLLOW = frozenset({"=", ";", ",", ":", "["})


def _match_decl(ct, i, hi, fwd):
    j = i
    while j < hi:
        if ct[j].text == "final":
            j += 1
        elif ct[j].text == "@" and j + 1 < hi and ct[j + 1].text != "interface":
            j = skip_annotation(ct, j, fwd)
        else:
            break
    k = parse_type(ct, j, hi)
    if k == -1 or k + 1 >= hi:
        return None
    nm = ct[k]
    if nm.kind == "ident" and nm.text not in KEYWORDS and ct[k + 1].text in _FOLLOW:
        return j, k, k   # type_start, type_end(exclusive == name idx), name idx
    return None


def collect_decls(ct, lo, hi, fwd, back):
    """Variable-like declarations whose name token lies in ct[lo:hi]. Includes fields and
    parameters of nested classes; callers decide what to do with those."""
    found = {}

    def add(d):
        found.setdefault(d.idx, d)

    enc_paren, enc_brace, st, bst = {}, {}, [], []
    for i in range(lo, hi):
        enc_paren[i] = st[-1] if st and ct[st[-1]].text == "(" else -1
        enc_brace[i] = bst[-1] if bst else -1
        if ct[i].kind == "punct":
            if ct[i].text in "([{":
                st.append(i)
                if ct[i].text == "{":
                    bst.append(i)
            elif ct[i].text in ")]}":
                o = st.pop()
                if ct[o].text == "{":
                    bst.pop()

    def kind_at(name_idx):
        op = enc_paren.get(name_idx, -1)
        if op > 0:
            head = ct[op - 1].text
            return head if head in ("for", "try", "catch") else "param_like"
        return "local"

    for i in range(lo, hi):
        if ct[i - 1].text not in STMT_PREV:
            continue
        m = _match_decl(ct, i, hi, fwd)
        if not m:
            continue
        ts, te, ni = m
        add(Decl(ct[ni].text, ni, kind_at(ni), ts, te))
        if ct[ni + 1].text in ("=", ",", "["):
            j = ni + 1
            while j < hi:
                t = ct[j].text
                if t in ("(", "[", "{") and j in fwd:
                    j = fwd[j] + 1
                    continue
                if t in (";", ")", "}"):
                    break
                if (t == "," and j + 2 < hi and ct[j + 1].kind == "ident"
                        and ct[j + 1].text not in KEYWORDS and ct[j + 2].text in _FOLLOW | {")"}):
                    add(Decl(ct[j + 1].text, j + 1, kind_at(j + 1), ts, te))
                j += 1

    for i in range(lo, hi):
        t = ct[i]
        if t.text == "->" and i > lo:
            p = ct[i - 1]
            if p.kind == "ident" and p.text not in KEYWORDS:
                add(Decl(p.text, i - 1, "lambda"))
            elif p.text == ")" and (i - 1) in back:
                o = back[i - 1]
                depth, last = 0, None
                for j in range(o + 1, i - 1):
                    tj = ct[j]
                    if tj.text in "(<[{":
                        depth += 1
                    elif tj.text in ")>]}":
                        depth -= 1
                    elif tj.text == "," and depth == 0:
                        if last is not None:
                            add(Decl(ct[last].text, last, "lambda"))
                        last = None
                    elif depth == 0 and tj.kind == "ident" and tj.text not in KEYWORDS:
                        last = j
                if last is not None:
                    add(Decl(ct[last].text, last, "lambda"))
        elif t.text == "catch" and i + 1 < hi and ct[i + 1].text == "(" and (i + 1) in fwd:
            c = fwd[i + 1]
            if ct[c - 1].kind == "ident":
                add(Decl(ct[c - 1].text, c - 1, "catch"))
        elif t.text == "instanceof":
            j = i + 1
            while j < hi and ct[j].text == "final":
                j += 1
            k = parse_type(ct, j, hi)
            if k != -1 and k < hi and ct[k].kind == "ident" and ct[k].text not in KEYWORDS:
                add(Decl(ct[k].text, k, "pattern", j, k))
    return sorted(found.values(), key=lambda d: d.idx), enc_paren, enc_brace


def nested_class_ranges(ct, lo, hi, fwd):
    """Token-index ranges (open, close) of anonymous-class and local-class bodies."""
    out = []
    for i in range(lo, hi):
        t = ct[i].text
        if t == "new":
            k = parse_type(ct, i + 1, hi)
            if k != -1 and k < hi and ct[k].text == "(" and k in fwd:
                c = fwd[k]
                if c + 1 < hi and ct[c + 1].text == "{" and (c + 1) in fwd:
                    out.append((c + 1, fwd[c + 1]))
        elif t in ("class", "interface", "enum") or (
                t == "record" and i + 2 < hi and ct[i + 1].kind == "ident" and ct[i + 2].text in "(<"):
            j = i + 1
            while j < hi and ct[j].text != "{":
                if ct[j].text == "(" and j in fwd:
                    j = fwd[j]
                j += 1
            if j < hi and j in fwd:
                out.append((j, fwd[j]))
    return out


# ---------------------------------------------------------------- method structure
@dataclass
class Method:
    src: str
    toks: list
    ct: list
    fwd: dict
    back: dict
    name: str
    params_open: int
    params_close: int
    body_open: int      # indices into ct
    body_close: int
    params: list
    throws: list


def analyze_method(src):
    """Single-method snippet -> Method. Raises Unsupported with a human-readable reason."""
    if not src or not src.strip():
        raise Unsupported("empty source")
    try:
        toks = tokenize(src)
    except LexError as e:
        raise Unsupported(f"lex error: {e}")
    ct = code_tokens(toks)
    fwd, back = bracket_maps(ct)
    i, n = 0, len(ct)
    while i < n:
        if ct[i].text == "@":
            i = skip_annotation(ct, i, fwd)
        elif ct[i].text == "(":
            break
        elif ct[i].text in "{;":
            raise Unsupported("no parameter list before body")
        else:
            i += 1
    if i >= n or i == 0 or ct[i - 1].kind != "ident":
        raise Unsupported("no method signature found")
    po, pc = i, fwd[i]
    name = ct[po - 1].text
    j = pc + 1
    throws = []
    if j < n and ct[j].text == "throws":
        j += 1
        while j < n and ct[j].text != "{":
            if ct[j].kind == "ident":
                throws.append(ct[j].text)
            if ct[j].text == ";":
                break
            j += 1
    if j >= n or ct[j].text != "{":
        raise Unsupported("method has no body")
    bo, bc = j, fwd[j]
    if bc != n - 1:
        raise Unsupported("code after the method body (not a single-method snippet)")
    params, depth, last = [], 0, None
    for k in range(po + 1, pc):
        t = ct[k]
        if t.text in "(<[{":
            depth += 1
        elif t.text in ")>]}":
            depth -= 1
        elif t.text == "," and depth == 0:
            if last:
                params.append(last)
            last = None
        elif depth == 0 and t.kind == "ident" and t.text not in KEYWORDS:
            last = t.text
    if last:
        params.append(last)
    return Method(src, toks, ct, fwd, back, name, po, pc, bo, bc, params, throws)
