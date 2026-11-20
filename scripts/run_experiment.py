"""Run the fake-fix + real-fix experiment from curated pairs to final tables.

From the repository root inside the FlakyLens container:
  /opt/conda/envs/flakylens/bin/python scripts/run_experiment.py

Optional GitHub-backed refresh of the curated pairs:
  /opt/conda/envs/flakylens/bin/python scripts/run_experiment.py --refresh-pairs

Fake-fix scoring runs in resumable batches; completed batches are reused when
variant IDs match. Use --force-rescore to rerun model inference.
"""
import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
DATA = ROOT / "data"
RESULTS = DATA / "results"


def run(label, script, *args):
    print(f"\n=== {label} ===", flush=True)
    subprocess.run([sys.executable, str(SCRIPTS / script), *map(str, args)], cwd=ROOT, check=True)


def score_args(args):
    return ["--src-dir", args.src_dir, "--data-dir", args.data_dir,
            "--models-dir", args.models_dir, "--weights-pattern", args.weights_pattern,
            "--device", args.device]


def list_complete_pairs(pairs_dir):
    return sorted(d.name for d in pairs_dir.iterdir()
                  if d.is_dir() and (d / "pre.java").exists() and (d / "post.java").exists())


def make_batches(variants_path, batch_dir, batch_size):
    variants = pd.read_csv(variants_path, keep_default_na=False)
    ids = sorted(variants["id"].astype(str).unique())
    input_dir = batch_dir / "inputs"
    prediction_dir = batch_dir / "predictions"
    input_dir.mkdir(parents=True, exist_ok=True)
    prediction_dir.mkdir(parents=True, exist_ok=True)
    batches = []
    for start in range(0, len(ids), batch_size):
        part = start // batch_size + 1
        chosen = ids[start:start + batch_size]
        frame = variants[variants["id"].astype(str).isin(chosen)].copy()
        input_path = input_dir / f"part_{part:02}.csv"
        frame.to_csv(input_path, index=False)
        expected = set(frame.loc[frame["suite"] != "original", "variant_id"].astype(str))
        out_path = prediction_dir / f"part_{part:02}_predictions.csv"
        batches.append((input_path, out_path, expected, len(chosen)))
    return batches


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src-dir", default="/app/src", help="FlakyLens source folder containing codebert_model.py")
    ap.add_argument("--data-dir", default="/app/src/FlakyLens_Categorization_PerProject-Data")
    ap.add_argument("--models-dir", default="/app/models")
    ap.add_argument("--weights-pattern", default="per_project_model_weights_on__dataset_project_group_{k}.pt")
    ap.add_argument("--device", default="auto", help="auto, cpu, or a torch device such as cuda")
    ap.add_argument("--batch-tests", type=int, default=10, help="test IDs per fake-fix scoring batch")
    ap.add_argument("--force-rescore", action="store_true", help="rerun real and fake model scoring")
    ap.add_argument("--refresh-pairs", action="store_true",
                    help="refresh curated pairs using accepted_candidates.csv and GitHub; requires gh")
    args = ap.parse_args()
    if args.batch_tests < 1:
        ap.error("--batch-tests must be at least 1")

    pairs_dir = DATA / "pairs"
    if args.refresh_pairs:
        if not shutil.which("gh"):
            raise SystemExit("--refresh-pairs requires the GitHub CLI (gh) in PATH. "
                             "The normal run uses existing curated data/pairs and does not need gh.")
        accepted_path = DATA / "interim/accepted_candidates.csv"
        if not accepted_path.exists():
            raise SystemExit(f"Curated candidate list not found: {accepted_path}")
        accepted = pd.read_csv(accepted_path)
        run("Resolve curated pull requests (cached responses are reused)", "resolve_prs.py")
        resolved = pd.read_csv(DATA / "interim/resolved_candidates.csv")
        if len(resolved) != len(accepted):
            raise SystemExit(f"PR resolution incomplete: {len(resolved)}/{len(accepted)} rows. "
                             "Check GitHub access/rate limits, then rerun.")
        resolved_ok = int(resolved["resolve_note"].eq("ok").sum())
        run("Extract changed pre/post test methods", "extract_pairs.py")
        pair_index = pd.read_csv(DATA / "interim/pairs_index.csv")
        if len(pair_index) != resolved_ok:
            raise SystemExit(f"Pair extraction incomplete: {len(pair_index)}/{resolved_ok} rows. "
                             "Check GitHub access/rate limits, then rerun.")
        usable = pair_index["usable"].astype(str).str.lower().eq("true")
        pair_ids = sorted(str(x) for x in pair_index.loc[usable, "pair_id"]
                          if (pairs_dir / str(x) / "pre.java").exists()
                          and (pairs_dir / str(x) / "post.java").exists())
    else:
        # The experiment uses a curated set of extracted pairs. Do not filter
        # the full raw IDoFT CSV here; that would silently change the sample.
        pair_ids = list_complete_pairs(pairs_dir)
    if not pair_ids:
        raise SystemExit("No complete pre/post test pairs found under data/pairs.")
    print(f"Using {len(pair_ids)} curated pre/post test pairs.", flush=True)

    pair_out = ROOT / "results/pair_predictions.csv"
    pair_out.parent.mkdir(parents=True, exist_ok=True)
    current_pair_ids = set()
    if pair_out.exists() and not args.force_rescore:
        old = pd.read_csv(pair_out)
        if "pair_id" in old:
            current_pair_ids = set(old["pair_id"].astype(str))
    if args.force_rescore or current_pair_ids != set(pair_ids):
        run("Score real developer-fix pairs", "classify_pairs.py",
            "--pairs", pairs_dir, "--out", pair_out, *score_args(args))
    else:
        print(f"Reusing {len(pair_ids)} matching real-pair predictions.", flush=True)

    fake_variants = RESULTS / "fake_variants.csv"
    fake_manifest = RESULTS / "fake_manifest.csv"
    fake_sources = RESULTS / "fake_variant_sources"
    run("Generate fake-fix variants", "perturb.py", "--pairs-dir", pairs_dir,
        "--out", fake_variants, "--manifest", fake_manifest, "--java-dir", fake_sources,
        "--suites", "fake_fix")

    batch_dir = RESULTS / "fake_batches"
    batches = make_batches(fake_variants, batch_dir, args.batch_tests)
    for input_path, out_path, expected_ids, test_count in batches:
        reusable = False
        if out_path.exists() and not args.force_rescore:
            try:
                scored = pd.read_csv(out_path, usecols=["variant_id"])
                actual_ids = set(scored["variant_id"].astype(str))
                reusable = actual_ids == expected_ids and len(scored) == len(expected_ids)
            except (ValueError, pd.errors.EmptyDataError):
                reusable = False
        if reusable:
            print(f"Reuse {out_path.name}: {test_count} tests, {len(expected_ids)} variants", flush=True)
            continue
        tmp_path = out_path.with_suffix(out_path.suffix + ".tmp")
        print(f"\n=== Score {input_path.name}: {test_count} tests, {len(expected_ids)} variants ===", flush=True)
        subprocess.run([sys.executable, str(SCRIPTS / "score_variants.py"),
                        "--variants", str(input_path), "--out", str(tmp_path),
                        *score_args(args)], cwd=ROOT, check=True)
        tmp_path.replace(out_path)

    variants = pd.read_csv(fake_variants, usecols=["variant_id", "suite"])
    expected_all = set(variants.loc[variants["suite"] != "original", "variant_id"].astype(str))
    combined = pd.concat([pd.read_csv(out) for _, out, _, _ in batches], ignore_index=True)
    actual = combined["variant_id"].astype(str)
    if actual.duplicated().any() or set(actual) != expected_all:
        raise SystemExit("Combined fake-fix predictions do not match generated variants. "
                         "Rerun to resume missing batches.")
    fake_predictions = RESULTS / "fake_variant_predictions.csv"
    combined.to_csv(fake_predictions, index=False)
    print(f"Combined {len(combined)} predictions from {len(batches)} fake-fix batches.", flush=True)

    out_dir = RESULTS / "final_metrics"
    run("Calculate metrics", "metrics.py", "--pair-predictions", pair_out,
        "--variant-predictions", fake_predictions, "--manifest", fake_manifest,
        "--out-dir", out_dir)
    run("Run paired, project-clustered comparison", "compare_fake_real.py",
        "--fake-predictions", fake_predictions, "--manifest", fake_manifest,
        "--fake-variants", fake_variants, "--pair-predictions", pair_out,
        "--out-dir", out_dir)

    metadata = {
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_dataset": "data/pairs/*/{pre,post}.java",
        "source_pairs_refreshed": bool(args.refresh_pairs),
        "real_fix_pairs": len(pair_ids),
        "fake_fix_variants_scored": len(combined),
        "fake_score_batches": len(batches),
        "batch_tests": args.batch_tests,
        "device": args.device,
        "model_source": args.src_dir,
        "model_data": args.data_dir,
        "models_dir": args.models_dir,
        "weights_pattern": args.weights_pattern,
    }
    (out_dir / "run_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print("\nExperiment complete. Final tables are in data/results/final_metrics/", flush=True)


if __name__ == "__main__":
    main()
