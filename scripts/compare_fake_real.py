"""Paired, project-clustered comparison of fake-fix variants vs real developer fixes.

Run from the repository root with the FlakyLens environment:
  python scripts/compare_fake_real.py

The unit of inference is the project (repository), not each fake variant. Fake
variants are averaged within test first; test-level contrasts are then averaged
within project. The script reports project-cluster bootstrap 95% CIs and a
one-sample t-test on the 34 project-level contrasts. It also saves the matched
per-test values so the analysis can be inspected.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))
import metrics as metric_helpers  # noqa: E402


def truthy(series):
    return series.astype(str).str.lower().eq("true")


def project_key(value, pair_id):
    value = str(value or "").strip().lower().rstrip("/")
    if value:
        return value
    return "__".join(str(pair_id).split("__")[:2]).lower()


def cluster_bootstrap_ci(project_values, seed=2026, reps=50000):
    values = np.asarray(project_values, dtype=float)
    rng = np.random.default_rng(seed)
    draws = rng.choice(values, size=(reps, len(values)), replace=True).mean(axis=1)
    return np.quantile(draws, [0.025, 0.975])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fake-predictions", default=str(ROOT / "data/results/fake_variant_predictions.csv"))
    ap.add_argument("--manifest", default=str(ROOT / "data/results/fake_manifest.csv"))
    ap.add_argument("--fake-variants", default=str(ROOT / "data/results/fake_variants.csv"))
    ap.add_argument("--pair-predictions", default=str(ROOT / "results/pair_predictions.csv"))
    ap.add_argument("--out-dir", default=str(ROOT / "data/results/final_metrics"))
    ap.add_argument("--bootstrap-reps", type=int, default=50000)
    ap.add_argument("--seed", type=int, default=2026)
    args = ap.parse_args()

    fake = pd.read_csv(args.fake_predictions, keep_default_na=False)
    manifest = pd.read_csv(args.manifest, keep_default_na=False)
    pair = pd.read_csv(args.pair_predictions)
    variant_meta = pd.read_csv(args.fake_variants, usecols=["id", "project"]).drop_duplicates("id")

    # Apply the project's existing exclusions: non-ok manifest rows, failed
    # compile checks, and edits identical to the original after 512-token truncation.
    fake, exclusions = metric_helpers.prepare(fake, manifest, drop_identical=True)
    fake = fake[(fake["suite"] == "fake_fix") & (fake["base"] == "pre") & fake["valid"]].copy()
    if fake.empty:
        raise SystemExit("No valid pre-fix fake-fix predictions found.")

    # Verify that the pre-fix inputs used for both analyses received the same
    # model group and original top prediction wherever a fake result is available.
    originals = fake.groupby("id", as_index=False).first()
    check = pair.merge(
        originals[["id", "orig_label", "model_groups", "group_source"]],
        left_on="pair_id", right_on="id", how="inner", suffixes=("_real", "_fake"))
    if not (check["orig_label"] == check["pre_top_name"]).all():
        raise SystemExit("Pre-fix predicted labels differ between real and fake scoring; comparison stopped.")
    if not (check["model_groups_real"] == check["model_groups_fake"]).all():
        raise SystemExit("Model groups differ between real and fake scoring; comparison stopped.")
    if not (check["group_source_real"] == check["group_source_fake"]).all():
        raise SystemExit("Model sources differ between real and fake scoring; comparison stopped.")

    # One fake-fix summary per test. delta_pred is the change in probability of
    # that test's ORIGINAL top-predicted class; flip is a top-1 label change.
    fake_by_test = fake.groupby("id", as_index=False).agg(
        fake_variant_count=("variant_id", "nunique"),
        fake_mean_delta_original_class=("delta_pred", "mean"),
        fake_flip_rate=("flip", "mean"),
    ).merge(variant_meta, on="id", how="left")

    # Match to real pairs with visible inputs and a flaky pre-fix prediction,
    # matching the fix-pair metric's eligibility definition.
    pair["identical_after_truncation"] = truthy(pair["identical_after_truncation"])
    eligible = pair[(~pair["identical_after_truncation"]) & (pair["pre_top"] != metric_helpers.NONFLAKY)].copy()
    matched = eligible.merge(fake_by_test, left_on="pair_id", right_on="id", how="inner", validate="one_to_one")
    if matched.empty:
        raise SystemExit("No matched eligible real/fake test pairs found.")

    matched["project"] = [project_key(p, i) for p, i in zip(matched["project"], matched["pair_id"])]
    matched["real_delta_original_class"] = matched["delta_pre_class"]
    matched["real_top1_change"] = matched["top1_changed"].astype(float)
    matched["real_minus_fake_confidence_delta"] = (
        matched["real_delta_original_class"] - matched["fake_mean_delta_original_class"])
    matched["fake_minus_real_flip_rate"] = matched["fake_flip_rate"] - matched["real_top1_change"]

    definitions = [
        ("confidence_change", "real_minus_fake_confidence_delta",
         "real minus fake change in original-class confidence; positive means fake edits lowered it more"),
        ("top1_change_rate", "fake_minus_real_flip_rate",
         "fake flip rate minus real top-1 change; positive means fake edits changed labels more"),
    ]
    rows = []
    for metric_name, col, interpretation in definitions:
        # Inference uses one mean contrast per repository, preventing multiple
        # tests from a single repository from being treated as independent.
        project_means = matched.groupby("project")[col].mean().to_numpy(dtype=float)
        test_weighted = float(matched[col].mean())
        project_equal = float(project_means.mean())
        ci_low, ci_high = cluster_bootstrap_ci(project_means, args.seed, args.bootstrap_reps)
        test = stats.ttest_1samp(project_means, popmean=0.0)
        rows.append({
            "comparison": metric_name,
            "matched_tests": int(len(matched)),
            "independent_projects": int(len(project_means)),
            "project_equal_effect": project_equal,
            "test_weighted_effect_descriptive": test_weighted,
            "cluster_bootstrap_95ci_low": float(ci_low),
            "cluster_bootstrap_95ci_high": float(ci_high),
            "one_sample_t_p_project_means": float(test.pvalue),
            "interpretation": interpretation,
        })

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = pd.DataFrame(rows)
    # Correct the two planned p-values for testing two related outcomes (Holm).
    raw_p = summary["one_sample_t_p_project_means"].to_numpy(dtype=float)
    order = np.argsort(raw_p)
    holm = np.empty_like(raw_p)
    running = 0.0
    for rank, idx in enumerate(order):
        running = max(running, min(1.0, (len(raw_p) - rank) * raw_p[idx]))
        holm[idx] = running
    summary["one_sample_t_p_holm"] = holm
    summary.to_csv(out_dir / "paired_comparison.csv", index=False)
    matched.to_csv(out_dir / "paired_comparison_by_test.csv", index=False)
    print(f"Matched {len(matched)} tests across {matched['project'].nunique()} projects.")
    print(f"Fake rows excluded by existing metrics rules: {exclusions}")
    print(summary.to_string(index=False, float_format=lambda x: f"{x:.4g}"))
    print(f"Wrote {out_dir / 'paired_comparison.csv'}")
    print(f"Wrote {out_dir / 'paired_comparison_by_test.csv'}")


if __name__ == "__main__":
    main()
