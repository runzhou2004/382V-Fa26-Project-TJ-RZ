# Evaluating ML-based flaky-test classifiers' responses to flakiness fixes

This repository measures whether a FlakyLens-style classifier (CodeBERT, six classes) tracks the
*mechanism* behind a flaky test or only surface features of the source. Experiments:

| Suite (this repo's name) | Question | Implemented by |
|---|---|---|
| **Invariance** (`invariance`) | do behaviour-preserving edits leave predictions/confidences stable? | `scripts/perturb.py` |
| **Sensitivity** (`real_cause`) | does *introducing* a verified cause raise confidence in that category? | `scripts/perturb.py` |
| **Reversal** (`real_fix`) | does *removing* a verified cause lower confidence in that category? | `scripts/perturb.py` |
| **Specificity** (`specificity`) | does editing unrelated code, with the cause kept, leave confidence stable? | `scripts/perturb.py` |
| **Fix Pairs** | what happens on real developer fixes (pre vs post)? | `scripts/classify_pairs.py` (unchanged) |
| Fake-fix and token-probe (`fake_fix`, `token_probe`) | does fix-looking code / category vocabulary move the prediction without changing the cause? | `scripts/perturb.py` |

> A prediction change is evidence of **sensitivity to a surface feature or pattern**. It is not, on its
> own, evidence for or against causal understanding. All metrics therefore report label flips,
> target-category confidence change and top-confidence change separately (see *Scoring and metrics*).

## Pipeline

```
data/pairs/*/pre.java|post.java          (extract_pairs.py, unchanged)
   |  python scripts/perturb.py --also-post --compile-check
   v
data/results/variants.csv   successful variants + one 'original' row per test/base (input of scoring)
data/results/manifest.csv   EVERY attempted transformation: ok, inapplicable (with reason), invalid
data/results/variants/<test id>/<pre|post>__<transformation>.java   the variant sources
   |  python scripts/score_variants.py --src-dir ... --data-dir ... --models-dir ...   (needs torch + FlakyLens)
   v
data/results/variant_predictions.csv   per-category probabilities for original (*_orig) and variant (*_mod)
   |  python scripts/metrics.py
   v
data/results/metrics.csv, metrics_by_transformation.csv, metrics_fixpairs.csv
```

Tests (no model needed): `python tests/tests_perturb.py` and `python tests/tests_metrics.py`
(plain `test_*` functions, so they should also run under pytest, which is not installed here and was not tried). Requirements: Python 3.10+, pandas, numpy; `javac` on PATH is
optional (compile checks and compile tests are skipped without it). Torch/transformers and the FlakyLens
artifacts are only needed by `score_variants.py` / `classify_pairs.py`, exactly as before.

`python scripts/perturb.py --list` prints the registry (name, suite, kind, expected direction, target).
Example outputs for two hand-written tests are in [`examples/`](examples): `examples/pairs` (inputs),
`examples/out/variants/**.java`, `examples/out/manifest.csv`, `examples/out/variants.csv`
(regenerate with `python scripts/perturb.py --pairs-dir examples/pairs --out examples/out/variants.csv --manifest examples/out/manifest.csv --java-dir examples/out/variants --compile-check --also-post`).

## Design

* **No new dependency.** tree-sitter-java and JavaParser were considered. JavaParser needs a JVM jar and a
  Java-side driver; tree-sitter needs compiled wheels and still leaves scope analysis to us. Neither is
  installed in this environment and the project's Docker image is not part of the repo, so adding one would
  be an unverified change. Instead `scripts/javalex.py` is an *exact* lexer (strings with escapes, char
  literals, text blocks incl. `\"""`, line/block comments) plus conservative token-pattern analysis
  (method structure, declarations, nested-class bodies). Anything it does not understand is **refused with
  a reason**, never guessed. Swapping in tree-sitter later only requires re-implementing `javalex.py`.
* **Pure functions + proof obligations.** A transformation takes the method source and returns new source.
  Afterwards the variant is re-lexed and a token-level post-condition is checked:
  `same_tokens` (comments/whitespace: code tokens identical), `insertion` (one contiguous token run was
  added), `deletion`, `replace` (only the recorded sites changed), `rename` (only mapped identifiers
  changed, consistently). A violated post-condition marks the variant `invalid`.
* **Deterministic.** No randomness anywhere (`seed` is recorded as empty); output order is fixed.
* **Compile check** (`--compile-check`, `scripts/javacheck.py`): original and variants are wrapped in a stub
  class (JDK imports + JUnit stubs) and compiled in one `javac` run. If the original compiles, variants must
  compile (`full` mode). If it does not (typically unresolved project classes) a variant must not add any
  diagnostic the original did not have (`differential` mode, a lower bound). javac runs with
  `-XDshould-stop.ifError=FLOW` so flow errors (e.g. unreachable code) are still reported.
  Compilation shows syntactic/type validity, **not** behavioural equivalence.

## Transformations

All names appear in `manifest.csv` as `name`. `fix_kind` distinguishes `fake`, `real_fix`, `real_cause`, `none`.

### Invariance (`expected = unchanged`)
| name | what it does | refuses / limitation |
|---|---|---|
| `rename_locals` | renames locals, for-/catch-/try-resource variables and lambda parameters to `v0, v1, …` (names avoid every identifier already in the method). Occurrences preceded by `.`/`::`, followed by `(`, labels, annotation names, strings and comments are untouched | method parameters, fields, names declared/shadowed inside anonymous/local classes, names used before/outside any declaring scope (probably a field), names declared in unbraced compound statements and `case` labels are not renamed (listed in `notes`); switch type patterns refuse the whole variant. Scopes are checked at name level, not by a full resolver |
| `reindent_tabs`, `reindent_2space` | 4-space indentation → tabs / 2 spaces | lines inside text blocks are never touched |
| `neutral_comment`, `trailing_comment` | `// reviewed` at body start / `// ok` after the first statement that ends its line | inline bodies get a newline so the comment cannot swallow code |
| `strip_comments` | removes all comments; a block comment between two tokens becomes a space (`a/**/-/**/-a` ≠ `a--a`); comment-only lines are deleted | comment markers inside strings/text blocks are kept |
| `dead_code` | `int unusedCounter[N] = 0;` at body start | name is collision-free |

### Fake fixes (`fix_kind = fake`, `expected = unchanged`)
`fake_fix_<category>_<start|end>` inserts statements that *look like* a fix for the category
(`LinkedHashMap`/`Collections.sort`, `Clock.fixed`, `CountDownLatch`, `synchronized`/`ReentrantLock`,
`HashMap.clear`) but only act on **fresh objects** built from fully-qualified types and fresh variable names.
Review of the earlier version: the statements were side-effect free, but the fixed name `fixedClock` could
collide and the `end` placement could land after `return`/`throw` (unreachable → compile error). Now: fresh
names, `end` placement refused after `return`/`throw`/`break`/`continue` and infinite loops, refused if an
identifier `java` exists. Post-condition: pure insertion, so the original cause is untouched by construction.
Fake fixes are generated for every category regardless of the test's own category; use `target_category`,
`mechanism_evidence` (heuristic code-token indicators, e.g. `HashMap`, `Thread`) and the `idoft_category`
column to select the *matched* subset. `metrics.py` also reports the subset where the edit's category equals
the original prediction.

### Token probes (`token_probe`, `expected = unchanged`)
`comment_words_<category>` (body start) and `comment_words_<category>_header` (above the method) for the five
FlakyLens flaky categories **and `non-flaky`**. Only comments change (post-condition: identical code tokens).
`tokens_introduced` lists the exact words, `tokens_already_present` the ones the method already contained
(e.g. `sleep` in a comment); an identical probe comment is never added twice.
*Limitations:* comments are a legitimate but narrow mechanism: they test lexical sensitivity to vocabulary,
not understanding. If the FlakyLens preprocessing strips comments the probe is a no-op (visible as identical
probabilities). A probe near the top of the body can push code past the 512-token limit; token counts and
truncation flags are carried into the predictions.

### Real fixes / causes — unordered collections (`real_fix`, `real_cause`, `specificity`)
Per `new [java.util.]HashMap|HashSet` (or `LinkedHash*`) instantiation the framework records: line/column/offset,
assigned variable, declared type, and **order-observation evidence** (`keySet/entrySet/values/iterator/stream/
forEach/toArray/toString`, for-each, string concatenation, serialization/formatting call arguments such as
`toJson`, `String.valueOf`, `new ArrayList<>(x)`). A site is changed only if
1. it is assigned to a local variable whose declared type is compatible (`Map`, `HashMap`, `Set`, `Collection`,
   `Iterable`, `Object`, `var`, … — a `LinkedHashMap`-typed variable cannot become a `HashMap`), and
2. the variable has strong order evidence.

| name | change | expected |
|---|---|---|
| `real_fix_unordered` | observed `HashMap/HashSet` → `LinkedHashMap/LinkedHashSet` (that variable's own instantiation only) | `confidence_drop` |
| `real_cause_unordered` | observed `LinkedHashMap/LinkedHashSet` → `HashMap/HashSet` | `confidence_rise` |
| `specificity_unordered_unrelated` | `Hash*` → `Linked*` on collections *only* used through order-neutral calls (`put/get/contains/size/…`) **while an order-observed `Hash*` is kept** | `unchanged` |

Inline arguments, field assignments, arrays, unobserved collections and `ConcurrentHashMap/TreeMap/…` are never
touched; the reason for each skipped site is in `notes`. The exact sites are in `changes`
(`line, col, offset, from, to, variable, declared_type, order_evidence`). The simple name `LinkedHashMap` is
used (as developers write it), so the surrounding file must import `java.util.LinkedHashMap`/`java.util.*`.

*Not claimed:* that `LinkedHashMap` fixes order-dependent test *execution* order flakiness, or fixes flakiness
when the insertion order is itself nondeterministic (e.g. filled from another `HashSet`). `fix_kind=real_fix`
only means "removes a statically visible source of unordered iteration that the test observes". `manual_review`
is `not_done` for every variant and **no variant is verified by execution**. Unobserved ≠ proven unrelated, so
the specificity suite is conservative and often inapplicable.

### Other categories — what is and is not implemented
* **Implemented (experimental; `--no-experimental` skips it):** `real_cause_concurrency_unsync` removes
  `synchronized(<simple monitor>) { … }` wrappers in tests that show thread usage (`Thread`, executors,
  `parallelStream`, …). The race is *plausible*, not demonstrated; keep it out of headline claims unless
  reviewed manually.
* **Deliberately not implemented** (no defensible, automatically verifiable relation to the mechanism without
  project context): inserting/removing arbitrary `Thread.sleep` (a sleep is neither a fix nor a cause of an
  async-wait flake and needs `throws InterruptedException`); replacing fixed delays with condition waits
  (needs the awaited condition); adding synchronization (needs to know which state is shared); time
  mocking / fixed clocks (needs the code under test); test-order dependence (shared state across tests is not
  visible in one method — use the developer Fix Pairs).

## Manifest and metadata

`manifest.csv` has one row per (test, base, transformation), **including failures and exclusions**:
`test_id, base, variant_id, name, suite, fix_kind, target_category, expected, status` (`ok | inapplicable |
invalid`), `reason`, `compile_checked/compile_ok/compile_mode/compile_detail`, `validated_by` (automatic only),
`manual_review` (`not_done`), `post_check`, `tokens_introduced`, `tokens_already_present`, `mechanism_evidence`,
`changes` (JSON), `notes` (JSON), `original_sha1`, `variant_sha1`, `original_path`, `variant_path`, `seed`,
`transform_version`. `variants.csv` (consumed by scoring) contains only `ok` variants plus the originals, with
`id`, `variant_id`, `base`, `project`, `idoft_category`, `suite`, `fix_kind`, `expected`, `target_category`,
`code`. Failed variants stay in the manifest and are excluded from metrics (which join the manifest again,
so a later manual `invalid` marking removes a variant).

## Scoring and metrics

`score_variants.py` reuses `classify_pairs.py` (`Scorer`, `encode`/`score`, project→group assignment, dedent,
table builder) with *original = pre* and *variant = post*, so each original and its variants are always scored
by the same checkpoint(s); token counts, `truncated` and `identical_after_truncation` are carried along.
Nothing about model loading or tokenization is duplicated. **The variants have not been run through FlakyLens
yet** (that needs torch and the checkpoints); the scoring/metrics code is only tested with a stub scorer.

`metrics.py` (definitions in its docstring) computes, with Wilson 95% intervals for rates: invariance
consistency; fake-fix and token-probe flip rate / mean target-category change / mean top-confidence change;
causal sensitivity, reversal, specificity (`eps` = 0.05 is an analyst choice, always printed, and the strict
"expected sign" share is reported next to it); agreement with developer fixes (Fix Pairs). For a target
category `c`: `ΔC_c = C_c(modified) − C_c(original)`. Variants identical to the original after 512-token
truncation, or whose manifest status/compile check failed, are excluded **and counted**.

## Research-integrity notes
* Nothing is dropped because of the classifier's reaction; every attempt is in the manifest.
* Syntactic validity (lexing, post-conditions, javac) is recorded separately from semantic validity, which is
  only ever *argued* statically, never executed.
* Of the 15 current pairs in `data/pairs`, none contains a `HashMap/HashSet/LinkedHash*` instantiation, so
  `real_fix`, `real_cause` and `specificity` are all inapplicable on them (manifest rows carry the reasons).
  Check coverage in `manifest.csv` before drawing conclusions about those suites.

## Changes relative to the first `perturb.py`
Found by code review: ad-hoc scanner and regexes; `rename_locals` renamed by name across the whole body (fields
used before a local declaration, names shadowed in anonymous classes) and applied sequential substitutions, so
a pre-existing `v0` could be double-renamed; `strip_comments` could fuse tokens (`a/**/-/**/-a` → `a--a`);
text blocks containing `\"""` ended early; a line comment inserted into an inline body swallowed the code after
it; `insert_at_end` removed the closing brace's indentation and could place code after `return`/`throw`; fixed
names (`unusedCounter`, `fixedClock`) could collide; `real_fix_unordered` replaced *every* `new HashMap/HashSet`
regardless of use, and `real_cause_unordered` checked declared-type compatibility with one whole-method regex
instead of per variable; failures were dropped silently and there was no metadata; only three tiny stubs were
compile-checked. `tests/tests_perturb.py` (31 tests) now covers nested braces/annotations, literals and text
blocks, shadowing/scopes, name collisions, comments next to operators, lambdas/anonymous classes, multiple
applicable/inapplicable transformations, determinism and input immutability, javac compilation of every
variant of 12 realistic fixtures, preservation of the suspected mechanism and of unrelated lines, metadata
correctness and the CLI/manifest.
