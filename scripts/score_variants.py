"""Score original/variant pairs with FlakyLens, reusing classify_pairs.py unchanged.

Input : data/results/variants.csv   (written by perturb.py; one 'original' row per test/base
        plus one row per successful variant)
Output: data/results/variant_predictions.csv   one row per (original, variant) pair with
        per-category probabilities for BOTH sides (columns *_orig / *_mod), token counts,
        truncation flags and group/checkpoint information.

Nothing here loads a model or tokenizer itself: Scorer, encode/score, project->group
assignment, dedenting and the per-class probability table all come from classify_pairs.py,
so the original and its variants are always scored by exactly the same checkpoint(s).

Naming: classify_pairs calls the two sides "pre"/"post". Here "pre" is the ORIGINAL test and
"post" is the MODIFIED variant, and the columns are renamed to *_orig / *_mod to avoid
confusion with developer pre-fix/post-fix pairs.
"""
import argparse
import re
import sys
import textwrap
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import classify_pairs as cp   # noqa: E402

ROOT = cp.ROOT


def _dedent(s, on=True):
    return textwrap.dedent(s).strip("\n") if on else s


def build_pairs(variants, dedent=True):
    """(pairs for classify_pairs, aligned metadata DataFrame, list of orphan variant ids).
    Every variant is paired with the original of the SAME test and base (pre/post)."""
    orig = {(r.id, r.base): r.code for r in variants.itertuples() if r.suite == "original"}
    pairs, meta, orphans = [], [], []
    for r in variants.itertuples():
        if r.suite == "original":
            continue
        o = orig.get((r.id, r.base))
        if not isinstance(o, str) or not o.strip():
            orphans.append(r.variant_id)
            continue
        pairs.append({"pair_id": r.variant_id, "idoft_category": getattr(r, "idoft_category", None),
                      "project": cp.project_key(getattr(r, "project", "") or r.id.split("__")[0]),
                      "pre": _dedent(o, dedent), "post": _dedent(r.code, dedent)})
        meta.append({"variant_id": r.variant_id, "id": r.id, "base": r.base, "variant": r.variant,
                     "suite": r.suite, "fix_kind": getattr(r, "fix_kind", ""),
                     "expected": r.expected, "target_category": r.target_category})
    return pairs, pd.DataFrame(meta), orphans


def rename_sides(df):
    return df.rename(columns={c: re.sub(r"(?<![a-z])post(?![a-z])", "mod",
                                        re.sub(r"(?<![a-z])pre(?![a-z])", "orig", c)) for c in df.columns})


def score_variants(variants, scorer, test_sets, dedent=True):
    pairs, meta, orphans = build_pairs(variants, dedent)
    if not pairs:
        raise SystemExit("no variants to score")
    names = cp.class_names(test_sets)
    groups, source = cp.assign_groups(pairs, cp.project_groups(test_sets))
    pre_p, post_p, pre_n, post_n, same = cp.classify(pairs, scorer, groups)
    table = cp.build_table(pairs, pre_p, post_p, pre_n, post_n, same, groups, source, names,
                           cp.code_lookup(test_sets, names))
    table = rename_sides(table).drop(columns=["pair_id"])
    out = pd.concat([meta.reset_index(drop=True), table.reset_index(drop=True)], axis=1)
    return out, orphans


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src-dir", default="/app/src", help="folder containing the authors' codebert_model.py")
    ap.add_argument("--data-dir", default="/app/src/FlakyLens_Categorization_PerProject-Data")
    ap.add_argument("--models-dir", default="/app/models")
    ap.add_argument("--weights-pattern", default="per_project_model_weights_on__dataset_project_group_{k}.pt")
    ap.add_argument("--variants", default=str(ROOT / "data" / "results" / "variants.csv"))
    ap.add_argument("--out", default=str(ROOT / "data" / "results" / "variant_predictions.csv"))
    ap.add_argument("--device", default="auto")
    ap.add_argument("--no-dedent", action="store_true")
    args = ap.parse_args()

    import torch
    device = ("cuda" if torch.cuda.is_available() else "cpu") if args.device == "auto" else args.device
    scorer = cp.Scorer(args.src_dir, args.models_dir, args.weights_pattern, device)
    test_sets = cp.load_test_sets(args.data_dir)
    if not test_sets:
        sys.exit(f"no test_set_*.csv found in {args.data_dir}")
    variants = pd.read_csv(args.variants, keep_default_na=False)
    out, orphans = score_variants(variants, scorer, test_sets, dedent=not args.no_dedent)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out, index=False, encoding="utf-8")
    print(f"wrote {len(out)} scored variants to {args.out}")
    if orphans:
        print(f"WARNING: {len(orphans)} variants had no original and were not scored: {orphans[:5]}...")
    print(f"truncated (>512 tokens): original {int((out['orig_tokens'] > cp.MAX_LEN).sum())}, "
          f"variant {int((out['mod_tokens'] > cp.MAX_LEN).sum())}; "
          f"identical after truncation: {int(out['identical_after_truncation'].sum())}")


if __name__ == "__main__":
    main()
