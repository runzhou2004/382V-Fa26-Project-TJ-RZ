"""Tests for the scoring/metrics plumbing (scripts/score_variants.py, scripts/metrics.py).

No model is loaded: a deterministic stub scorer replaces classify_pairs.Scorer (which these
scripts reuse unchanged), so the tests check pairing, group/truncation bookkeeping, exclusion
of invalid variants and the metric definitions - NOT classifier behaviour.

Run:  python tests/tests_metrics.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))
import metrics                                                      # noqa: E402
import score_variants as sv                                          # noqa: E402
from perturb import attempt_variants                                 # noqa: E402
from tests_perturb import MAP_ORDER, LINKED_ORDER                    # noqa: E402

CLASSES = ["async wait", "concurrency", "time", "unordered collections", "test order dependency", "non-flaky"]


class StubScorer:
    """Whitespace 'tokens'; truncates to 512 like the real encoder; probabilities depend on text."""
    def __init__(self):
        self.calls = []

    @staticmethod
    def probs(text):
        v = np.full(6, 0.1)
        v[3] = 0.5 if "new HashMap" in text else 0.1
        if "LinkedHashMap" in text:
            v[5] += 0.3
        return v / v.sum()

    def encode(self, texts):
        ids = [t.split()[:512] for t in texts]
        return ids, [[1] * len(i) for i in ids], np.array([len(t.split()) + 2 for t in texts])

    def score(self, k, ids, mask, batch_size=8):
        self.calls.append((k, len(ids)))
        return np.array([self.probs(" ".join(i)) for i in ids])


def stub_test_sets():
    return {k: pd.DataFrame({"project": ["x_y" if k == 1 else "other_proj"] * 6, "label": range(6),
                             "category": CLASSES, "full_code": [f"code{k}{i}" for i in range(6)]})
            for k in (1, 2, 3, 4)}


def variants_frame():
    rows = []
    for tid, code in (("a__b__pr1__T.m", MAP_ORDER), ("a__b__pr1__T.n", LINKED_ORDER)):
        common = dict(id=tid, base="pre", project="https://github.com/p/q", idoft_category="ID")
        rows.append(dict(common, variant="pre", variant_id=f"{tid}:pre", suite="original", fix_kind="none",
                         expected="", target_category="", code=code))
        for v in attempt_variants(code, test_id=tid, base="pre"):
            if v.status == "ok":
                rows.append(dict(common, variant=f"pre:{v.name}", variant_id=f"{tid}:pre:{v.name}", suite=v.suite,
                                 fix_kind=v.fix_kind, expected=v.expected, target_category=v.target_category,
                                 code=v.code))
    return pd.DataFrame(rows)


def scored():
    df, orphans = sv.score_variants(variants_frame(), StubScorer(), stub_test_sets())
    assert orphans == []
    return df


def test_every_variant_is_paired_with_its_own_original_and_columns_are_renamed():
    vf = variants_frame()
    out = scored()
    assert len(out) == int((vf.suite != "original").sum())
    assert set(out["variant_id"]) == set(vf[vf.suite != "original"]["variant_id"])
    for c in ("orig_tokens", "mod_tokens", "truncated", "identical_after_truncation", "orig_top_name",
              "mod_top_name", "model_groups", "group_source", "p_unordered collections_orig",
              "p_unordered collections_mod", "p_non-flaky_orig", "target_category", "suite", "fix_kind"):
        assert c in out.columns, c
    assert not [c for c in out.columns if c.endswith("_pre") or c.endswith("_post")]
    assert (out["model_groups"] == "1+2+3+4").all()                           # project not in any held-out set
    row = out[out.variant_id.str.endswith("real_fix_unordered")].iloc[0]
    assert abs(row["p_unordered collections_orig"] - StubScorer.probs(MAP_ORDER)[3]) < 1e-9


def test_same_checkpoint_scores_original_and_variant():
    sc = StubScorer()
    sv.score_variants(variants_frame(), sc, stub_test_sets())
    assert len(sc.calls) == 8 and len({k for k, _ in sc.calls}) == 4          # 4 groups x (original side, variant side)


def test_orphan_variants_are_reported_not_scored():
    vf = variants_frame()
    vf = vf[~((vf.suite == "original") & (vf.id == "a__b__pr1__T.n"))]
    out, orphans = sv.score_variants(vf, StubScorer(), stub_test_sets())
    assert orphans and all("T.n" in o for o in orphans) and not out.variant_id.str.contains("T.n").any()


def test_metrics_definitions_on_stub_scores():
    out = scored()
    df, excl = metrics.prepare(out)
    # the stub tokenizer ignores whitespace, so pure re-indentation is "identical after truncation" and is
    # excluded (but counted); everything else is valid
    ident = out[out.variant.str.contains("reindent")]
    assert excl["identical_after_truncation"] == len(ident) and ident.identical_after_truncation.all()
    assert int(df.valid.sum()) == len(df) - len(ident)
    m = metrics.variant_metrics(df).set_index("metric")
    # comments / formatting / dead code never change the stub's probabilities
    assert m.loc["invariance_consistency", "value"] == 1.0 and m.loc["invariance_mean_total_variation", "value"] == 0.0
    # fake fixes keep `new HashMap` in place (the stub only reacts to the real cause), probe comments change nothing
    assert m.loc["token_probe_flip_rate", "value"] == 0.0
    # real_fix: HashMap -> LinkedHashMap lowers p(unordered) in the stub
    fixed = MAP_ORDER.replace("scores = new HashMap", "scores = new LinkedHashMap")
    rf = df[df.suite == "real_fix"].iloc[0]
    assert abs(rf.delta_target - (StubScorer.probs(fixed)[3] - StubScorer.probs(MAP_ORDER)[3])) < 1e-12
    assert rf.delta_target < 0
    assert m.loc["causal_reversal_share_expected_direction", "value"] == 1.0
    assert m.loc["causal_reversal_share_beyond_eps", "value"] == 1.0
    assert m.loc["causal_sensitivity_share_expected_direction", "value"] == 1.0      # LINKED_ORDER -> HashMap
    assert "causal_specificity_share_within_eps" in m.index
    n = m.loc["invariance_consistency"]
    assert 0 <= n.ci95_low <= n.value <= n.ci95_high <= 1
    # label flips, target confidence and max confidence are separate quantities
    assert {"flip", "delta_target", "delta_max", "delta_pred", "tv"} <= set(df.columns)


def test_invalid_and_truncated_variants_are_excluded_but_counted():
    out = scored()
    manifest = pd.DataFrame({"variant_id": out.variant_id, "status": "ok", "compile_ok": "True"})
    manifest.loc[manifest.variant_id.str.endswith("real_fix_unordered"), "status"] = "invalid"
    manifest.loc[manifest.variant_id.str.endswith("dead_code"), "compile_ok"] = "False"
    df, excl = metrics.prepare(out, manifest)
    assert excl["manifest_status_not_ok"] >= 1 and excl["compile_check_failed"] >= 1
    assert not df[df.variant_id.str.endswith("real_fix_unordered")].valid.any()
    m = metrics.variant_metrics(df)
    assert "causal_reversal_share_expected_direction" not in set(m.metric)        # no valid reversal rows left
    # a variant whose edit lies beyond token 512 is identical to its original after truncation
    long_orig = "x " * 600 + "end"
    common = dict(id="a__b__pr1__T.m", base="pre", project="p_q", idoft_category="ID", fix_kind="none",
                  target_category="")
    vf = pd.DataFrame([
        dict(common, variant="pre", variant_id="a__b__pr1__T.m:pre", suite="original", expected="", code=long_orig),
        dict(common, variant="pre:neutral", variant_id="a__b__pr1__T.m:pre:neutral", suite="invariance",
             expected="unchanged", code=long_orig + " // reviewed")])
    o, _ = sv.score_variants(vf, StubScorer(), stub_test_sets(), dedent=False)
    assert bool(o.truncated.iloc[0]) and bool(o.identical_after_truncation.iloc[0])
    df, excl = metrics.prepare(o)
    assert excl["identical_after_truncation"] == 1 and not df.valid.any()


def test_fix_pair_metrics():
    pairs = pd.DataFrame({"pre_top": [3, 3, 5, 3], "post_top": [5, 3, 5, 3], "delta_pre_class": [-0.4, -0.1, 0.0, 0.0],
                          "top1_changed": [True, False, False, False],
                          "identical_after_truncation": [False, False, False, True]})
    m = metrics.fix_pair_metrics(pairs).set_index("metric")["value"]
    assert m["fixpairs_pre_called_flaky"] == 2                          # pair 3 is non-flaky, pair 4 has no signal
    assert m["fixpairs_share_pre_class_confidence_dropped"] == 1.0
    assert m["fixpairs_share_flipped_to_nonflaky"] == 0.5
    assert m["fixpairs_excluded_identical_after_truncation"] == 1


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
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
