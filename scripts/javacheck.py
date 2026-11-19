"""Differential javac check for single-method snippets.

A test method cannot be compiled on its own (it references project classes, fields and test
frameworks). Instead we wrap the original and every variant in a stub class with common JDK
imports and JUnit stubs, compile them all in ONE javac run, and compare the diagnostics:

  * original compiles cleanly         -> mode "full":         a variant must compile cleanly too
  * original has (unresolved-symbol)  -> mode "differential": a variant must not add any diagnostic
    errors                                                    that the original did not already have

Limitations (stated in the README): differential mode is a lower bound on validity. javac is
told to continue to the flow-analysis phase (-XDshould-stop.ifError=FLOW) so errors such as
unreachable code are still reported, but diagnostics that depend on resolving project types
are masked when those types are missing. A passing check is therefore evidence of syntactic
and basic type validity, not of behavioural equivalence.
"""
import re
import shutil
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

JUNIT_STUBS = {
    "org/junit/Test.java": "package org.junit; public @interface Test { "
                           "Class<? extends Throwable>[] expected() default {}; long timeout() default 0L; }",
    "org/junit/Before.java": "package org.junit; public @interface Before {}",
    "org/junit/After.java": "package org.junit; public @interface After {}",
    "org/junit/Ignore.java": "package org.junit; public @interface Ignore { String value() default \"\"; }",
    "org/junit/Assert.java": """package org.junit;
public class Assert {
  public static void assertEquals(Object a, Object b) {}
  public static void assertEquals(String m, Object a, Object b) {}
  public static void assertEquals(long a, long b) {}
  public static void assertEquals(double a, double b, double d) {}
  public static void assertEquals(String m, long a, long b) {}
  public static void assertNotEquals(Object a, Object b) {}
  public static void assertTrue(boolean c) {}
  public static void assertTrue(String m, boolean c) {}
  public static void assertFalse(boolean c) {}
  public static void assertFalse(String m, boolean c) {}
  public static void assertNull(Object o) {}
  public static void assertNotNull(Object o) {}
  public static void assertSame(Object a, Object b) {}
  public static void assertArrayEquals(Object[] a, Object[] b) {}
  public static void fail() {}
  public static void fail(String m) {}
}""",
}

IMPORTS = ("import java.util.*; import java.util.concurrent.*; import java.util.concurrent.atomic.*; "
           "import java.util.function.*; import java.util.stream.*; import java.io.*; import java.time.*; "
           "import java.text.*; import static org.junit.Assert.*; import org.junit.*;\n")

_ERR = re.compile(r"^(?:.*[\\/])?(V\w*)\.java:\d+: error: (.*)$")
_SYM = re.compile(r"^\s+symbol:\s*(.*)$")


def _normalize(msg):
    return re.sub(r"\bV\w*\b", "V", msg)


def _parse(stderr):
    """{file stem: Counter of normalized diagnostics}; a `symbol:` line refines its error."""
    out, cur = {}, None
    for line in stderr.splitlines():
        m = _ERR.match(line)
        if m:
            stem, msg = m.group(1), _normalize(m.group(2))
            out.setdefault(stem, Counter())[msg] += 1
            cur = (stem, msg)
            continue
        s = _SYM.match(line)
        if s and cur:
            out[cur[0]][f"{cur[1]} :: {_normalize(s.group(1).strip())}"] += 1
    return out


def javac_available():
    return shutil.which("javac") is not None


def check_variants(original, variants, timeout=300):
    """variants: {name: code}. Returns {name: (checked, ok, mode, detail)}."""
    if not variants:
        return {}
    if not javac_available():
        return {n: (False, None, "javac_unavailable", "javac not found on PATH") for n in variants}
    items, key_of = {"V_orig": original}, {}
    for i, (name, code) in enumerate(variants.items()):
        items[f"V{i}"] = code
        key_of[name] = f"V{i}"
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        for rel, text in JUNIT_STUBS.items():
            p = td / "stubs" / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
        files = []
        for stem, code in items.items():
            f = td / f"{stem}.java"
            f.write_text(IMPORTS + f"class {stem} {{\n{code}\n}}\n", encoding="utf-8")
            files.append(str(f))
        cmd = ["javac", "-proc:none", "-Xlint:none", "-Xmaxerrs", "100000", "-XDshould-stop.ifError=FLOW",
               "-encoding", "UTF-8", "-d", str(td / "out"), "-sourcepath", str(td / "stubs")] + files
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, encoding="utf-8",
                               errors="replace")
        except subprocess.TimeoutExpired:
            return {n: (True, None, "timeout", "javac timed out") for n in variants}
    diags = _parse(p.stderr)
    base = diags.get("V_orig", Counter())
    mode = "full" if not base else "differential"
    res = {}
    for name, stem in key_of.items():
        new = diags.get(stem, Counter()) - base
        if new:
            first = next(iter(new))
            res[name] = (True, False, mode, f"{sum(new.values())} new diagnostic(s), e.g. {first}"[:300])
        else:
            res[name] = (True, True, mode, "")
    return res
