import argparse
import json
import sys
 
import pandas as pd
 
from common import RateLimited, ROOT, extract_methods, gh_api, normalize, parse_pr_link
 
ap = argparse.ArgumentParser()
ap.add_argument("--limit", type=int, default=None)
args = ap.parse_args()
 
df = pd.read_csv(ROOT / "data/interim/resolved_candidates.csv")
df = df[df["resolve_note"] == "ok"].reset_index(drop=True)
if args.limit:
    df = df.head(args.limit)
test_col = next(c for c in df.columns if c.startswith("Fully-Qualified Test Name"))
 
 
def fetch(owner, repo, path, sha):
    return gh_api(f"repos/{owner}/{repo}/contents/{path}?ref={sha}", raw=True)
 
 
index = []
try:
    for i, r in df.iterrows():
        owner, repo, n = parse_pr_link(r["PR Link"])
        pair_id = f"{owner}__{repo}__pr{n}__{r['test_class']}.{r['test_method']}"
        rec = {"pair_id": pair_id, "project": r["Project URL"], "category": r["Category"],
               "pr_link": r["PR Link"], "pre_sha": r["pre_sha"], "post_sha": r["post_sha"],
               "post_source": r["post_source"], "file_status": r["file_status"],
               "test_class": r["test_class"], "test_method": r["test_method"],
               "usable": False, "reason": ""}
 
        if r["file_status"] == "added":
            rec["reason"] = "test_file_added_in_pr"  # no pre-fix version exists
        else:
            pre_src = fetch(owner, repo, r["test_file_pre"], r["pre_sha"])
            post_src = fetch(owner, repo, r["test_file_post"], r["post_sha"])
            if pre_src is None or post_src is None:
                rec["reason"] = "file_fetch_failed"
            else:
                pre_m = extract_methods(pre_src, r["test_method"])
                post_m = extract_methods(post_src, r["test_method"])
                rec["n_pre_matches"], rec["n_post_matches"] = len(pre_m), len(post_m)
                if not pre_m or not post_m:
                    rec["reason"] = "method_missing_pre" if not pre_m else "method_missing_post"
                elif len(pre_m) > 1 or len(post_m) > 1:
                    rec["reason"] = "ambiguous_overloads"
                elif normalize(pre_m[0]) == normalize(post_m[0]):
                    rec["reason"] = "method_unchanged"  # fix was elsewhere (prod code, setup, config)
                else:
                    rec["usable"], rec["reason"] = True, "ok"
                    d = ROOT / "data" / "pairs" / pair_id
                    d.mkdir(parents=True, exist_ok=True)
                    (d / "pre.java").write_text(pre_m[0])
                    (d / "post.java").write_text(post_m[0])
                    rec["pre_chars"], rec["post_chars"] = len(pre_m[0]), len(post_m[0])
                    (d / "meta.json").write_text(json.dumps(rec, indent=2, default=str))
        index.append(rec)
        if len(index) % 25 == 0:
            print(f"  {len(index)}/{len(df)} rows", file=sys.stderr)
except RateLimited as e:
    print(f"\nGitHub rate limit hit after {len(index)} rows: {e}\nCache saved; re-run later.", file=sys.stderr)
 
idx = pd.DataFrame(index)
idx.to_csv(ROOT / "data/interim/pairs_index.csv", index=False)
if idx.empty:
    print("No rows to process. resolved_candidates.csv has no rows with resolve_note == 'ok'.")
    sys.exit(0)
print(idx["reason"].value_counts().to_string())
if len(idx):
    print("\nusable pairs per category:")
    print(idx[idx["usable"]]["category"].value_counts().to_string())