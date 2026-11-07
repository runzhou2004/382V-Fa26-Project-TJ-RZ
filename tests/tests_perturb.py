"""Tests for the perturbation framework (scripts/perturb.py, javalex.py, javacheck.py).

Run:  python tests/tests_perturb.py        (or: pytest tests/tests_perturb.py)

Compilation tests use javac when it is on PATH and are reported as SKIPPED otherwise.
Fixtures are realistic test methods. Those in FULL compile against the JDK + JUnit stubs
without any project classes, so their variants are checked in javac's strict "full" mode.
"""
import csv
import difflib
import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import javacheck                                                          # noqa: E402
from javalex import analyze_method, code_tokens, tokenize                 # noqa: E402
from perturb import (REGISTRY, Out, apply_transform, attempt_variants, body_span,   # noqa: E402
                     check_post, generate_variants, well_formed)

HAVE_JAVAC = shutil.which("javac") is not None

# --------------------------------------------------------------------------- fixtures
MAP_ORDER = '''    @Test
    public void testSerializeScores() throws Exception {
        // sleep here is only in a comment
        Map<String, Integer> scores = new HashMap<>();
        scores.put("alice", 3);
        scores.put("bob", 5);
        Map<String, Integer> lookup = new HashMap<>();
        lookup.put("x", 1);
        StringBuilder sb = new StringBuilder();
        for (String key : scores.keySet()) {
            sb.append(key).append(',');
        }
        String text = "scores { not a brace, new HashMap<>() in a string";
        assertEquals("alice,bob,", sb.toString());
        assertTrue(lookup.containsKey("x"));
    }'''

LINKED_ORDER = '''    @Test
    public void testLinkedToString() {
        Map<String, Integer> m = new LinkedHashMap<>();
        m.put("a", 1);
        m.put("b", 2);
        LinkedHashMap<String, Integer> typed = new LinkedHashMap<>();
        typed.put("z", 0);
        assertEquals("{a=1, b=2}", m.toString());
        assertEquals(1, typed.size());
    }'''

# first line is NOT indented, as in data/pairs/*/pre.java
PAIRS_FORMAT = '''@Test
    public void TestDateSerializers() throws ParseException {
        SimpleDateFormat fmt = new SimpleDateFormat("yyyy-MM-dd", Locale.ENGLISH);
        fmt.setTimeZone(TimeZone.getTimeZone("GMT"));
        Date d = fmt.parse("2018-10-31");
        String json = "{\\n"
                + "  \\"date\\": \\"2018-10-31\\"\\n"
                + "}";
        assertEquals(1, json.length() > 0 ? 1 : 0);
    }'''

NESTED_ANNOT = '''    @Test(expected = {IllegalStateException.class}, timeout = 1000)
    public void testNested() {
        int total = 0;
        for (int i = 0; i < 3; i++) {
            if (i % 2 == 0) { total += i; } else { total -= 1; }
        }
        assertEquals(1, total);
    }'''

LAMBDA_ANON = '''    @Test
    public void testCallbacks() throws Exception {
        final AtomicInteger counter = new AtomicInteger();
        List<String> items = new ArrayList<>(Arrays.asList("x", "y", "z"));
        items.forEach(item -> counter.addAndGet(item.length()));
        Runnable task = new Runnable() {
            int counter2 = 0;
            @Override
            public void run() {
                int items = 5;
                counter.incrementAndGet();
                counter2 += items;
            }
        };
        task.run();
        assertEquals(4, counter.get());
    }'''

SCOPES = '''    @Test
    public void testScopes() throws Exception {
        int count = 0;
        for (int i = 0; i < 2; i++) {
            int tmp = i * 2;
            count += tmp;
        }
        for (int i = 0; i < 3; i++) {
            String tmp = "v" + i;
            count += tmp.length();
        }
        for (int j = 0; j < 2; j++) count += j;
        try (StringReader reader = new StringReader("abc")) {
            count += reader.read();
        } catch (IOException e) {
            count = -1;
        }
        int a = 1, b = 2;
        assertEquals(1, a + b - 2);
    }'''

COLLISION = '''    @Test
    public void testCollision() {
        int v0 = 1;
        int total = v0 + 1;
        int unusedCounter = 7;
        int fixedClock = 1;
        assertEquals(2, total + unusedCounter - 7 - fixedClock + 1);
    }'''

STRINGS = '''    @Test
    public void testStrings() {
        String json = "{\\"k\\": \\"v\\", \\"c\\": \\"// not a comment /* nor this */\\"}";
        char brace = '{';
        char quote = '"';
        String block = """
            {
              "synchronized": "sleep",
              "esc": "a \\""" b"
            }
            """;
        assertEquals(true, json.length() + block.length() > 0);
    }'''

COMMENTS = '''    @Test
    public void testComments() {
        int a = 5;
        int b = a/**/-/**/-a;   // a - (-a) = 10
        int c = a /* one */ + /* two */ b;
        int d = a- /* three */-c;
        /* block
           spanning */
        assertEquals(10, b);
    }'''

THREADS = '''    @Test
    public void testThreads() throws Exception {
        final Object lock = new Object();
        final int[] shared = new int[1];
        Thread t1 = new Thread(() -> { synchronized (lock) { shared[0]++; } });
        Thread t2 = new Thread(() -> { synchronized (lock) { shared[0]++; } });
        t1.start(); t2.start(); t1.join(); t2.join();
        assertEquals(2, shared[0]);
    }'''

EARLY_THROW = '''    @Test
    public void testEndsWithThrow() {
        long start = System.currentTimeMillis();
        if (start < 0) {
            return;
        }
        throw new IllegalStateException("never");
    }'''

INLINE = '''    @Test public void testInline() { int x = 1; assertEquals(1, x); }'''

FIELD_SHADOW = '''    @Test
    public void testFieldShadow() {
        total = 5;
        int total = 2;
        assertEquals(2, total);
    }'''

INLINE_SET = '''    @Test
    public void testInlineSet() {
        List<String> list = Arrays.asList("a", "b");
        this.cache = new HashMap<>();
        assertEquals(new HashSet<>(list), new HashSet<>(list));
    }'''

# these compile in javac "full" mode (no project classes needed)
FULL = {"MAP_ORDER": MAP_ORDER, "LINKED_ORDER": LINKED_ORDER, "PAIRS_FORMAT": PAIRS_FORMAT,
        "NESTED_ANNOT": NESTED_ANNOT, "LAMBDA_ANON": LAMBDA_ANON, "SCOPES": SCOPES, "COLLISION": COLLISION,
        "STRINGS": STRINGS, "COMMENTS": COMMENTS, "THREADS": THREADS, "EARLY_THROW": EARLY_THROW,
        "INLINE": INLINE}
ALL = dict(FULL, FIELD_SHADOW=FIELD_SHADOW, INLINE_SET=INLINE_SET)


# --------------------------------------------------------------------------- helpers
def ok(name, code):
    v = apply_transform(name, code)
    assert v.status == "ok", f"{name}: expected ok, got {v.status}: {v.reason}"
    return v


def not_ok(name, code):
    v = apply_transform(name, code)
    assert v.status != "ok", f"{name}: expected a refusal"
    assert v.reason, f"{name}: a refusal must carry a reason"
    assert v.code is None
    return v


def toks(code):
    return [t.text for t in code_tokens(tokenize(code))]


def changed_lines(a, b):
    sm = difflib.SequenceMatcher(None, a.split("\n"), b.split("\n"), autojunk=False)
    return [op for op in sm.get_opcodes() if op[0] != "equal"]


def text_blocks(code):
    return [t.text for t in tokenize(code) if t.kind == "textblock"]


def is_pure_insertion(orig, var):
    a = 0
    while a < len(orig) and a < len(var) and orig[a] == var[a]:
        a += 1
    return len(var) > len(orig) and orig[a:] == var[a + len(var) - len(orig):]


# --------------------------------------------------------------------------- lexer / structure
def test_lexer_is_lossless_and_handles_literals():
    for name, code in ALL.items():
        assert "".join(t.text for t in tokenize(code)) == code, name
    blocks = text_blocks(STRINGS)
    assert len(blocks) == 1 and '"synchronized"' in blocks[0] and blocks[0].rstrip().endswith('"""')
    assert '\\"""' in blocks[0]                                            # escaped quote does not end the block
    kinds = {x.text: x.kind for x in tokenize(STRINGS) if x.kind in ("char", "string")}
    assert kinds["'{'"] == "char" and kinds["'\"'"] == "char"
    assert not [x for x in tokenize(STRINGS) if x.kind == "comment"], "markers inside strings are not comments"


def test_well_formed_and_body_span():
    for name, code in ALL.items():
        assert well_formed(code), name
    s, e = body_span(NESTED_ANNOT)          # braces inside annotation arguments are skipped
    assert NESTED_ANNOT[s:].lstrip("{").lstrip().startswith("int total")
    assert e == len(NESTED_ANNOT) - 1 and NESTED_ANNOT[e] == "}"
    for bad in ("", "   ", "@Test public void t() { int x = 1; ", "void t() { String s = \"abc; }",
                "void a() { } void b() { }", "int x = 3;", "void t() { /* open "):
        assert not well_formed(bad), repr(bad)


def test_unsupported_source_still_yields_complete_records():
    recs = attempt_variants("void t() { int x = \"oops; }", test_id="T")
    assert len(recs) == len(REGISTRY)
    assert all(r.status == "inapplicable" and r.reason.startswith("source not supported") for r in recs)


# --------------------------------------------------------------------------- rename_locals
def test_rename_basic_preserves_strings_apis_and_names():
    v = ok("rename_locals", MAP_ORDER)
    c = v.code
    assert '"scores { not a brace, new HashMap<>() in a string"' in c        # string untouched
    assert "// sleep here is only in a comment" in c                          # comment untouched
    assert "keySet()" in c and "assertEquals" in c and "StringBuilder" in c    # API names untouched
    assert "testSerializeScores" in c                                          # method name untouched
    assert "scores.put" not in c and "sb.append" not in c
    mapping = {ch["old"]: ch["new"] for ch in v.changes}
    assert set(mapping) == {"scores", "lookup", "sb", "key", "text"}
    assert len(set(mapping.values())) == len(mapping)
    assert all(n.startswith("v") for n in mapping.values())


def test_rename_scopes_shadowing_and_unbraced_for():
    v = ok("rename_locals", SCOPES)
    mapping = {ch["old"]: ch["new"] for ch in v.changes}
    # i/tmp are declared in sibling scopes (different types); one consistent mapping is applied to both
    assert {"count", "i", "tmp", "j", "reader", "e", "a", "b"} <= set(mapping)
    assert f"{mapping['count']} += {mapping['j']};" in v.code and "+= j;" not in v.code      # unbraced for body
    assert "reader.read" not in v.code


def test_rename_refuses_unsafe_names():
    v = not_ok("rename_locals", FIELD_SHADOW)                      # `total` is used as a field before the local
    assert "total" in v.reason and "outside" in v.reason
    v = ok("rename_locals", LAMBDA_ANON)
    mapping = {ch["old"]: ch["new"] for ch in v.changes}
    assert "items" not in mapping and any("items" in n for n in v.notes)      # shadowed in anonymous class
    assert "counter2" not in mapping                                          # nested-class field
    assert {"counter", "task", "item"} <= set(mapping)
    assert f"{mapping['counter']}.incrementAndGet()" in v.code               # captured variable renamed in the body
    assert "int items = 5;" in v.code and "counter2 += items;" in v.code     # anonymous class internals intact
    assert "items.forEach" in v.code                                          # outer `items` left alone


def test_rename_never_collides_with_existing_identifiers():
    v = ok("rename_locals", COLLISION)
    mapping = {ch["old"]: ch["new"] for ch in v.changes}
    assert mapping["v0"] != "v0"                               # the existing `v0` is renamed, never reused as a target
    assert len(set(mapping.values())) == len(mapping)
    assert "v0" not in set(mapping.values())


def test_rename_leaves_parameters_and_nonlocals():
    code = '''    @Test
    public void t(int param) {
        int local = param + 1;
        this.field = local;
        System.out.println(local);
        assertEquals(local, field);
    }'''
    v = ok("rename_locals", code)
    assert "int param" in v.code and "param + 1" in v.code
    assert "this.field" in v.code and ", field)" in v.code
    assert "local" not in v.code.replace("this.", "")


# --------------------------------------------------------------------------- formatting / comments
def test_reindent_preserves_text_block_content():
    v = ok("reindent_tabs", STRINGS)
    assert "\n\t\tString json" in v.code
    assert text_blocks(v.code) == text_blocks(STRINGS)                          # text block bytes unchanged
    assert toks(v.code) == toks(STRINGS)
    v2 = ok("reindent_2space", STRINGS)
    assert "\n    String json" in v2.code.replace("\n        String json", "\n    String json")
    assert text_blocks(v2.code) == text_blocks(STRINGS) and toks(v2.code) == toks(STRINGS)


def test_strip_comments_keeps_tokens_separated():
    v = ok("strip_comments", COMMENTS)
    assert "/*" not in v.code and "//" not in v.code
    assert toks(v.code) == toks(COMMENTS)
    assert "int b = a - -a;" in v.code                              # `a/**/-/**/-a` must not become `a--a`
    assert apply_transform("strip_comments", STRINGS).status == "inapplicable"      # markers only inside strings
    m = ok("strip_comments", MAP_ORDER)
    assert '"scores { not a brace, new HashMap<>() in a string"' in m.code
    assert "sleep here" not in m.code
    assert all(line.strip() for line in m.code.split("\n")), "comment-only lines should be removed, not left blank"


def test_strip_comments_marker_text_in_strings_is_kept():
    code = '''    @Test
    public void t() {
        String url = "http://example.com/*x*/"; // trailing
        assertEquals("http://example.com/*x*/", url);
    }'''
    v = ok("strip_comments", code)
    assert v.code.count("http://example.com/*x*/") == 2 and "trailing" not in v.code


def test_comment_insertion_never_swallows_code():
    for name in ("neutral_comment", "trailing_comment", "comment_words_time", "comment_words_time_header"):
        v = apply_transform(name, INLINE)
        if v.status == "ok":
            assert toks(v.code) == toks(INLINE), name
    v = ok("neutral_comment", INLINE)
    assert "// reviewed\n" in v.code                                # newline added after the inline-body comment


def test_trailing_comment_targets_a_statement_end():
    v = ok("trailing_comment", MAP_ORDER)
    assert "Map<String, Integer> scores = new HashMap<>(); // ok" in v.code
    assert toks(v.code) == toks(MAP_ORDER)


# --------------------------------------------------------------------------- dead code / fake fixes
def test_dead_code_uses_collision_free_name():
    v = ok("dead_code", COLLISION)
    assert "int unusedCounter0 = 0;" in v.code
    v = ok("dead_code", MAP_ORDER)
    assert "int unusedCounter = 0;" in v.code
    assert v.code.index("unusedCounter") < v.code.index("Map<String, Integer> scores")


def test_fake_fix_never_modifies_original_logic():
    n = 0
    for name, code in FULL.items():
        for v in generate_variants(code, suites={"fake_fix"}):
            assert v.fix_kind == "fake" and v.expected == "unchanged" and v.post_check == "insertion"
            assert is_pure_insertion(toks(code), toks(v.code)), (name, v.name)
            n += 1
    assert n > 30
    v = ok("fake_fix_unordered_collections_start", MAP_ORDER)
    assert v.code.count("new HashMap<>()") == MAP_ORDER.count("new HashMap<>()")   # original cause intact
    assert "LinkedHashMap" in v.code and "Collections.sort" in v.code


def test_fake_fix_unique_names_and_end_placement_safety():
    v = ok("fake_fix_time_start", COLLISION)
    assert "fixedClock0" in v.code and "int fixedClock = 1;" in v.code
    for name in ("fake_fix_time_end", "fake_fix_concurrency_end"):
        assert "unreachable" in not_ok(name, EARLY_THROW).reason
    ok("fake_fix_time_start", EARLY_THROW)
    v = ok("fake_fix_time_end", MAP_ORDER)
    assert v.code.split("\n")[-1] == "    }"                                    # closing-brace indentation kept
    loop = "    @Test\n    public void t() {\n        while (true) { }\n    }"
    assert "infinite loop" in not_ok("fake_fix_async_wait_end", loop).reason


def test_fake_fix_refuses_when_java_identifier_shadows_fqn():
    code = "    @Test\n    public void t() {\n        int java = 1;\n        assertEquals(1, java);\n    }"
    assert "java" in not_ok("fake_fix_time_start", code).reason


# --------------------------------------------------------------------------- token probes
def test_token_probe_comment_only_and_metadata():
    v = ok("comment_words_async_wait", MAP_ORDER)
    assert toks(v.code) == toks(MAP_ORDER)                       # executable code untouched
    assert set(v.tokens_introduced) >= {"wait", "async", "poll", "sleep", "timeout"}
    assert "sleep" in v.tokens_already_present                  # already in the original comment
    assert v.fix_kind == "none" and v.suite == "token_probe" and v.target_category == "async wait"
    h = ok("comment_words_time_header", PAIRS_FORMAT)
    assert h.code.startswith("// uses current time") and toks(h.code) == toks(PAIRS_FORMAT)
    again = v.code.replace("// wait for async result, poll until ready, sleep, timeout",
                           "// uses current time, timezone, date, clock")
    assert "already present" in not_ok("comment_words_time", again).reason     # no duplicate insertion
    names = {t.name for t in REGISTRY if t.suite == "token_probe"}
    assert {"comment_words_non_flaky", "comment_words_time", "comment_words_concurrency",
            "comment_words_unordered_collections", "comment_words_test_order_dependency",
            "comment_words_async_wait"} <= names                  # all six FlakyLens categories covered


# --------------------------------------------------------------------------- real fixes / causes
def test_real_fix_only_touches_order_observed_collection():
    v = ok("real_fix_unordered", MAP_ORDER)
    assert "scores = new LinkedHashMap<>();" in v.code
    assert "lookup = new HashMap<>();" in v.code                 # unrelated collection untouched
    assert "new HashMap<>() in a string" in v.code               # string untouched
    assert v.fix_kind == "real_fix" and v.expected == "confidence_drop"
    assert v.target_category == "unordered collections"
    assert len(v.changes) == 1
    ch = v.changes[0]
    assert (ch["from"], ch["to"], ch["variable"], ch["declared_type"]) == ("HashMap", "LinkedHashMap", "scores", "Map")
    assert ch["order_evidence"] == ["call:keySet"] and ch["line"] == 4 and ch["offset"] > 0
    assert len(changed_lines(MAP_ORDER, v.code)) == 1             # nothing else moved


def test_real_fix_refuses_unobservable_or_unsupported_sites():
    v = not_ok("real_fix_unordered", INLINE_SET)
    assert "never observed" in v.reason
    assert any("field" in n for n in v.notes) and any("not assigned" in n for n in v.notes)
    assert "no HashMap/HashSet" in not_ok("real_fix_unordered", NESTED_ANNOT).reason
    unobserved = ("    @Test\n    public void t() {\n        Map<String, String> m = new HashMap<>();\n"
                  "        m.put(\"a\", \"b\");\n        assertEquals(1, m.size());\n    }")
    assert "never observed" in not_ok("real_fix_unordered", unobserved).reason
    typed = ("    @Test\n    public void t() {\n        HashSet<String> s = new HashSet<>();\n        s.add(\"a\");\n"
             "        for (String x : s) { System.out.println(x); }\n    }")
    v = ok("real_fix_unordered", typed)
    assert "new LinkedHashSet<>()" in v.code and v.changes[0]["order_evidence"] == ["for-each"]
    concurrent = ("    @Test\n    public void t() {\n        Map<String, String> m = new ConcurrentHashMap<>();\n"
                  "        for (String k : m.keySet()) { }\n    }")
    assert "no HashMap/HashSet" in not_ok("real_fix_unordered", concurrent).reason


def test_real_cause_inverse_and_declared_type_compatibility():
    v = ok("real_cause_unordered", LINKED_ORDER)
    assert "Map<String, Integer> m = new HashMap<>();" in v.code
    assert "typed = new LinkedHashMap<>()" in v.code            # a LinkedHashMap-typed variable cannot become HashMap
    assert v.fix_kind == "real_cause" and v.expected == "confidence_rise"
    assert [c["variable"] for c in v.changes] == ["m"]
    assert apply_transform("real_cause_unordered", MAP_ORDER).status == "inapplicable"
    assert apply_transform("real_fix_unordered", LINKED_ORDER).status == "inapplicable"


def test_fix_cause_fake_are_distinguishable_in_metadata():
    for code in (MAP_ORDER, LINKED_ORDER, THREADS):
        for v in attempt_variants(code):
            if v.suite == "real_fix":
                assert v.fix_kind == "real_fix" and v.expected == "confidence_drop"
            elif v.suite == "real_cause":
                assert v.fix_kind == "real_cause" and v.expected == "confidence_rise"
            elif v.suite == "fake_fix":
                assert v.fix_kind == "fake" and v.expected == "unchanged"
            else:
                assert v.fix_kind == "none"
            if v.status == "ok" and v.suite in ("real_fix", "real_cause"):
                assert v.manual_review == "not_done" and v.changes


def test_specificity_changes_only_unrelated_collection():
    v = ok("specificity_unordered_unrelated", MAP_ORDER)
    assert "lookup = new LinkedHashMap<>();" in v.code
    assert "scores = new HashMap<>();" in v.code                 # suspected cause preserved
    assert v.mechanism_evidence == ["call:keySet"]
    assert any("cause preserved" in n for n in v.notes)
    assert apply_transform("specificity_unordered_unrelated", LINKED_ORDER).status == "inapplicable"


def test_concurrency_unsync_is_gated_on_thread_evidence():
    v = ok("real_cause_concurrency_unsync", THREADS)
    assert "synchronized" not in v.code and v.code.count("shared[0]++") == 2
    assert v.changes[0]["monitor"] == "lock" and "Thread" in v.mechanism_evidence
    assert any("experimental" in n for n in v.notes)
    no_thread = ("    @Test\n    public void t() {\n        Object l = new Object();\n"
                 "        synchronized (l) { l.hashCode(); }\n    }")
    assert "no evidence of multithreading" in not_ok("real_cause_concurrency_unsync", no_thread).reason
    complex_monitor = THREADS.replace("synchronized (lock)", "synchronized (make())", 1)
    assert len(apply_transform("real_cause_concurrency_unsync", complex_monitor).changes) == 1   # simple monitors only


# --------------------------------------------------------------------------- manifest / determinism / purity
def test_every_attempt_has_complete_metadata():
    for name, code in ALL.items():
        recs = attempt_variants(code, test_id=name, base="pre")
        assert [r.name for r in recs] == [t.name for t in REGISTRY], name        # nothing silently skipped
        for r in recs:
            assert r.status in ("ok", "inapplicable"), (name, r.name, r.status, r.reason)
            assert r.original_sha1 and r.test_id == name and r.base == "pre"
            if r.status == "ok":
                assert r.code and r.code != code and r.variant_sha1 and r.post_check
            else:
                assert r.reason and r.code is None, (name, r.name)
            assert r.seed == "" and r.manual_review == "not_done" and r.validated_by.startswith("automatic")
            json.dumps(asdict(r))                                                  # metadata is serialisable


def test_deterministic_and_inputs_unmodified():
    for name, code in ALL.items():
        before = str(code)
        a = [asdict(v) for v in attempt_variants(code, test_id="t")]
        b = [asdict(v) for v in attempt_variants(code, test_id="t")]
        assert a == b, name
        assert code == before


def test_suite_filter():
    assert {r.suite for r in attempt_variants(MAP_ORDER, suites={"real_fix"})} == {"real_fix"}
    assert not [r for r in attempt_variants(THREADS, include_experimental=False) if r.name.endswith("unsync")]


def test_postconditions_catch_a_broken_transformation():
    ct = analyze_method(MAP_ORDER).ct
    changed = analyze_method(MAP_ORDER.replace('scores.put("bob", 5)', 'scores.put("bob", 6)')).ct
    assert not check_post(Out(post="same_tokens"), ct, changed)[0]
    assert not check_post(Out(post="insertion"), ct, changed)[0]
    assert not check_post(Out(post="replace", allowed={0}), ct, changed)[0]


# --------------------------------------------------------------------------- compilation
def test_every_variant_of_every_compiling_fixture_compiles():
    if not HAVE_JAVAC:
        print("  SKIPPED (javac not found)")
        return
    total = 0
    for name, code in FULL.items():
        vs = {v.name: v.code for v in generate_variants(code)}
        assert vs, name
        for vname, (checked, good, mode, detail) in javacheck.check_variants(code, vs).items():
            assert checked and mode == "full", (name, vname, mode, detail)
            assert good, f"{name}/{vname} does not compile: {detail}"
            total += 1
    print(f"  {total} variants compiled in javac full mode")


def test_compile_check_detects_broken_variants_and_differential_mode():
    if not HAVE_JAVAC:
        print("  SKIPPED (javac not found)")
        return
    broken = MAP_ORDER.replace('scores.put("bob", 5);', 'scoresX.put("bob", 5);')
    res = javacheck.check_variants(MAP_ORDER, {"broken": broken, "same": MAP_ORDER})
    assert res["broken"][1] is False and res["same"][1] is True
    unreachable = EARLY_THROW.replace('throw new IllegalStateException("never");',
                                      'throw new IllegalStateException("never");\n        int y = 0;')
    assert javacheck.check_variants(EARLY_THROW, {"u": unreachable})["u"][1] is False
    # an unresolved project type makes the original non-compilable -> differential mode, still sensitive
    orig = PAIRS_FORMAT.replace("SimpleDateFormat fmt", "Zork fmt")
    res = javacheck.check_variants(orig, {"v": orig.replace("fmt.parse", "fmtt.parse"), "same": orig})
    assert res["v"][2] == "differential" and res["v"][1] is False and res["same"][1] is True


# --------------------------------------------------------------------------- CLI / manifest
def test_cli_writes_manifest_with_failures_and_consumable_variants():
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        pairs = td / "pairs"
        for pid, pre, post in (("proj__a__pr1__T.m1", MAP_ORDER, LINKED_ORDER), ("proj__a__pr1__T.m2", "", "")):
            d = pairs / pid
            d.mkdir(parents=True)
            (d / "pre.java").write_text(pre, encoding="utf-8")
            (d / "post.java").write_text(post, encoding="utf-8")
            (d / "meta.json").write_text(json.dumps({"project": "https://github.com/x/y", "category": "ID"}))
        out, man, jdir = td / "variants.csv", td / "manifest.csv", td / "java"
        p = subprocess.run([sys.executable, str(ROOT / "scripts" / "perturb.py"), "--pairs-dir", str(pairs),
                            "--out", str(out), "--manifest", str(man), "--java-dir", str(jdir), "--also-post"],
                           capture_output=True, text=True, cwd=str(ROOT), encoding="utf-8")
        assert p.returncode == 0, p.stderr
        mrows = list(csv.DictReader(man.open(encoding="utf-8")))
        vrows = list(csv.DictReader(out.open(encoding="utf-8")))
        assert len(mrows) == 4 * len(REGISTRY)                                   # 2 tests x (pre, post)
        assert any(r["status"] == "inapplicable" and r["test_id"].endswith("m2") for r in mrows)
        assert {r["status"] for r in mrows} >= {"ok", "inapplicable"}
        ok_ids = {r["variant_id"] for r in mrows if r["status"] == "ok"}
        var_ids = {r["variant_id"] for r in vrows if r["suite"] != "original"}
        assert ok_ids == var_ids                                                 # failures stay out of variants.csv
        assert {"id", "variant", "base", "suite", "expected", "target_category", "code", "project",
                "idoft_category", "fix_kind", "variant_id"} <= set(vrows[0])
        assert len([r for r in vrows if r["suite"] == "original"]) == 4
        assert all(Path(r["variant_path"]).exists() for r in mrows if r["status"] == "ok")
        assert all(r["original_sha1"] and r["seed"] == "" for r in mrows)
        assert (jdir / "proj__a__pr1__T.m1" / "pre__real_fix_unordered.java").exists()


# --------------------------------------------------------------------------- runner
def _run():
    import traceback
    tests = [(k, f) for k, f in sorted(globals().items()) if k.startswith("test_") and callable(f)]
    failed = 0
    for k, f in tests:
        try:
            f()
            print("ok  ", k)
        except Exception:                # noqa: BLE001
            failed += 1
            print("FAIL", k)
            traceback.print_exc()
    print(f"\n{len(tests) - failed}/{len(tests)} passed" + ("" if HAVE_JAVAC else " (javac tests skipped)"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
