"""Suite-level metrics from variant_predictions.csv (score_variants.py) and, optionally,
pair_predictions.csv (classify_pairs.py, the developer Fix Pairs).

Definitions (all per VALID variant; c = the variant's target category)
  delta_target   C_c(modified) - C_c(original)         change in target-category confidence
  flip           argmax(modified) != argmax(original)   label change
  delta_max      max(modified) - max(original)          change in top confidence
  delta_pred     P_mod[orig label] - P_orig[orig label] change in the originally predicted class
  tv             0.5 * sum |P_mod - P_orig|             total change of the whole distribution

  invariance consistency      1 - flip rate over invariance variants (+ mean tv, mean |delta_max|)
  fake-fix flip rate / mean   flip rate, mean delta_target, mean delta_max over fake_fix variants
  token-probe flip rate       same over token_probe variants
  causal sensitivity          real_cause: share with delta_target > 0 (and > eps), mean delta_target
  causal reversal             real_fix:   share with delta_target < 0 (and < -eps), mean delta_target
  causal specificity          specificity: share with |delta_target| <= eps, mean |delta_target|
  agreement with developer    Fix Pairs: among pairs the model called flaky before the fix and whose
  fixes                       model input changed: share with a drop in the pre-predicted class,
                              share flipped to non-flaky

A label flip alone is NOT evidence of causal understanding; every rate is reported together
with the confidence-based quantities and a Wilson 95% interval. `eps` is an analyst choice
(default 0.05) and is reported next to every metric that uses it.

Exclusions are counted, never silent: variants whose manifest status is not "ok" or whose
compilation check failed, and (by default) variants/pairs whose input is IDENTICAL after
512-token truncation (the edit cannot influence the model). They stay in the manifest.
"""
import argparse
import math
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

NONFLAKY = 5
NOT_CLASSES = {"nonflaky", "orig_class"}      # helper columns that look like p_<x>_orig


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def class_names(df):
    names = []
    for c in df.columns:
        m = re.fullmatch(r"p_(.+)_orig", c)
        if m and m.group(1) not in NOT_CLASSES and f"p_{m.group(1)}_mod" in df.columns:
            names.append(m.group(1))
    return names


def _truthy(s):
    return s.astype(str).str.lower().eq("true")


def prepare(df, manifest=None, drop_identical=True):
    """Add per-row quantities and a `valid` flag; returns (df, exclusion counts)."""
    df = df.copy()
    names = class_names(df)
    P0 = df[[f"p_{n}_orig" for n in names]].to_numpy(float)
    P1 = df[[f"p_{n}_mod" for n in names]].to_numpy(float)
    idx = np.arange(len(df))
    top0, top1 = P0.argmax(1), P1.argmax(1)
    df["orig_label"] = [names[i] for i in top0]
    df["mod_label"] = [names[i] for i in top1]
    df["flip"] = top0 != top1
    df["delta_max"] = P1.max(1) - P0.max(1)
    df["delta_pred"] = P1[idx, top0] - P0[idx, top0]
    df["tv"] = 0.5 * np.abs(P1 - P0).sum(1)
    tgt = df["target_category"].fillna("").astype(str)
    col = {n: i for i, n in enumerate(names)}
    has = tgt.isin(col)
    ti = tgt.map(col).fillna(0).astype(int).to_numpy()
    df["delta_target"] = np.where(has, P1[idx, ti] - P0[idx, ti], np.nan)
    df["target_is_orig_label"] = has & (tgt == df["orig_label"])
    valid = pd.Series(True, index=df.index)
    excl = {}
    if manifest is not None:
        m = manifest.drop_duplicates("variant_id").set_index("variant_id")
        bad_status = df["variant_id"].map(m["status"]).ne("ok")
        bad_compile = df["variant_id"].map(m["compile_ok"]).astype(str).str.lower().eq("false")
        excl["manifest_status_not_ok"] = int(bad_status.sum())
        excl["compile_check_failed"] = int((bad_compile & ~bad_status).sum())
        valid &= ~(bad_status | bad_compile)
    if drop_identical and "identical_after_truncation" in df:
        ident = _truthy(df["identical_after_truncation"])
        excl["identical_after_truncation"] = int((ident & valid).sum())
        valid &= ~ident
    df["valid"] = valid
    if "orig_tokens" in df:
        excl["truncated_but_kept"] = int(((df["orig_tokens"] > 512) | (df["mod_tokens"] > 512))[valid].sum())
    return df, excl


def _rate(rows, metric, suite, mask, extra=""):
    n, k = len(mask), int(mask.sum())
    lo, hi = wilson(k, n)
    rows.append(dict(metric=metric, suite=suite, n=n, value=k / n if n else float("nan"),
                     ci95_low=lo, ci95_high=hi, extra=extra))


def _stat(rows, metric, suite, s, extra="", fn="mean"):
    s = s.dropna()
    rows.append(dict(metric=metric, suite=suite, n=len(s), value=float(getattr(s, fn)()) if len(s) else float("nan"),
                     ci95_low=float("nan"), ci95_high=float("nan"), extra=extra))


def variant_metrics(df, eps=0.05):
    rows = []
    v = df[df["valid"]]
    e = f"eps={eps}"
    s = v[v.suite == "invariance"]
    if len(s):
        _rate(rows, "invariance_consistency", "invariance", ~s.flip, "share with unchanged top-1 label")
        _stat(rows, "invariance_mean_total_variation", "invariance", s.tv)
        _stat(rows, "invariance_mean_abs_delta_max", "invariance", s.delta_max.abs())
        _stat(rows, "invariance_mean_abs_delta_pred_class", "invariance", s.delta_pred.abs())
    for suite in ("fake_fix", "token_probe"):
        s = v[v.suite == suite]
        if not len(s):
            continue
        _rate(rows, f"{suite}_flip_rate", suite, s.flip, "all variants")
        _stat(rows, f"{suite}_mean_delta_target", suite, s.delta_target, "signed; target = the edit's category")
        _stat(rows, f"{suite}_mean_delta_max", suite, s.delta_max)
        m = s[s.target_is_orig_label]
        if len(m):
            _rate(rows, f"{suite}_flip_rate_target_is_predicted", suite, m.flip,
                  "subset: the edit targets the category predicted for the original")
            _stat(rows, f"{suite}_mean_delta_target_target_is_predicted", suite, m.delta_target)
    for suite, name, sign in (("real_cause", "causal_sensitivity", 1), ("real_fix", "causal_reversal", -1)):
        s = v[v.suite == suite].dropna(subset=["delta_target"])
        if not len(s):
            continue
        d = s.delta_target * sign
        _rate(rows, f"{name}_share_expected_direction", suite, d > 0, "delta_target has the expected sign")
        _rate(rows, f"{name}_share_beyond_eps", suite, d > eps, e)
        _stat(rows, f"{name}_mean_delta_target", suite, s.delta_target)
        _stat(rows, f"{name}_median_delta_target", suite, s.delta_target, fn="median")
        _rate(rows, f"{name}_label_flip_rate", suite, s.flip, "reported separately; not a causal claim")
    s = v[v.suite == "specificity"].dropna(subset=["delta_target"])
    if len(s):
        _rate(rows, "causal_specificity_share_within_eps", "specificity", s.delta_target.abs() <= eps, e)
        _stat(rows, "causal_specificity_mean_abs_delta_target", "specificity", s.delta_target.abs())
        _rate(rows, "causal_specificity_label_flip_rate", "specificity", s.flip)
    return pd.DataFrame(rows)


def by_transformation(df):
    v = df[df["valid"]]
    keys = ["suite", "variant"] if "variant" in v else ["suite"]
    return v.groupby(keys).agg(n=("flip", "size"), flip_rate=("flip", "mean"),
                               mean_delta_target=("delta_target", "mean"), mean_delta_max=("delta_max", "mean"),
                               mean_delta_pred=("delta_pred", "mean"), mean_tv=("tv", "mean")).reset_index()


def fix_pair_metrics(pairs):
    """Agreement with developer fixes, from classify_pairs' pair_predictions.csv."""
    usable = pairs[~_truthy(pairs["identical_after_truncation"])]
    flaky = usable[usable["pre_top"] != NONFLAKY]
    n = len(flaky)
    rows = [dict(metric="fixpairs_pairs_total", n=len(pairs), value=len(pairs)),
            dict(metric="fixpairs_excluded_identical_after_truncation", n=len(pairs),
                 value=len(pairs) - len(usable)),
            dict(metric="fixpairs_pre_called_flaky", n=len(usable), value=n)]
    if n:
        for name, mask in (("share_pre_class_confidence_dropped", flaky.delta_pre_class < 0),
                           ("share_flipped_to_nonflaky", flaky.post_top == NONFLAKY),
                           ("share_top1_changed", _truthy(flaky.top1_changed))):
            lo, hi = wilson(int(mask.sum()), n)
            rows.append(dict(metric=f"fixpairs_{name}", n=n, value=float(mask.mean()), ci95_low=lo, ci95_high=hi))
        rows.append(dict(metric="fixpairs_mean_delta_pre_class", n=n, value=float(flaky.delta_pre_class.mean())))
    return pd.DataFrame(rows)


def main(argv=None):
    root = Path(__file__).resolve().parent.parent
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--variant-predictions", default=str(root / "data/results/variant_predictions.csv"))
    ap.add_argument("--manifest", default=str(root / "data/results/manifest.csv"))
    ap.add_argument("--pair-predictions", default=str(root / "results/pair_predictions.csv"))
    ap.add_argument("--out-dir", default=str(root / "data/results"))
    ap.add_argument("--eps", type=float, default=0.05)
    ap.add_argument("--keep-identical", action="store_true",
                    help="do not drop variants identical to the original after 512-token truncation")
    a = ap.parse_args(argv)
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    frames = []
    vp = Path(a.variant_predictions)
    if vp.exists():
        df = pd.read_csv(vp, keep_default_na=False, na_values=[""])
        man = pd.read_csv(a.manifest, keep_default_na=False) if Path(a.manifest).exists() else None
        df, excl = prepare(df, man, drop_identical=not a.keep_identical)
        m = variant_metrics(df, a.eps)
        m.to_csv(out / "metrics.csv", index=False)
        by_transformation(df).to_csv(out / "metrics_by_transformation.csv", index=False)
        print(f"variants scored: {len(df)}, valid: {int(df.valid.sum())}; exclusions: {excl}")
        frames.append(m)
    else:
        print(f"{vp} not found (run score_variants.py first); skipping variant metrics")
    pp = Path(a.pair_predictions)
    if pp.exists():
        fm = fix_pair_metrics(pd.read_csv(pp))
        fm.to_csv(out / "metrics_fixpairs.csv", index=False)
        frames.append(fm)
    if frames:
        print(pd.concat(frames).to_string(index=False, float_format=lambda x: f"{x:.3f}"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
