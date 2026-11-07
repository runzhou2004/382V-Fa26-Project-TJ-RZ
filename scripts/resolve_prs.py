import argparse
import sys
 
import pandas as pd
 
from common import RateLimited, ROOT, gh_api, parse_fqn, parse_pr_link
 
ap = argparse.ArgumentParser()
ap.add_argument("--limit", type=int, default=None, help="only process the first N rows (for testing)")
args = ap.parse_args()
 
df = pd.read_csv(ROOT / "data/interim/accepted_candidates.csv")
test_col = next(c for c in df.columns if c.startswith("Fully-Qualified Test Name"))
if args.limit:
    df = df.head(args.limit)
 
pr_cache = {}  # many tests share one PR: resolve each PR once
 
 
def resolve_pr(owner, repo, n):
    key = (owner, repo, n)
    if key in pr_cache:
        return pr_cache[key]
    info = {"pr_state": None, "pr_merged": None, "pre_sha": None, "post_sha": None,
            "post_source": None, "files": []}
    pr = gh_api(f"repos/{owner}/{repo}/pulls/{n}")
    if pr is None:
        info["pr_state"] = "unavailable"
        pr_cache[key] = info
        return info
    info["pr_state"] = pr["state"]
    info["pr_merged"] = bool(pr.get("merged"))
    base_sha, head_sha = pr["base"]["sha"], pr["head"]["sha"]
 
    cmp_ = gh_api(f"repos/{owner}/{repo}/compare/{base_sha}...{head_sha}")
    info["pre_sha"] = (cmp_ or {}).get("merge_base_commit", {}).get("sha") or base_sha
    # is the head commit actually readable from the base repo?
    if gh_api(f"repos/{owner}/{repo}/commits/{head_sha}") is not None:
        info["post_sha"], info["post_source"] = head_sha, "pr_head"
    elif pr.get("merge_commit_sha"):
        info["post_sha"], info["post_source"] = pr["merge_commit_sha"], "merge_commit"
    info["files"] = gh_api(f"repos/{owner}/{repo}/pulls/{n}/files", paginate=True) or []
    pr_cache[key] = info
    return info
 
 
def find_test_file(files, pkg_path, cls):
    """Return (path_at_post, path_at_pre, status) of the changed file holding the class."""
    suffix = f"{pkg_path}/{cls}.java" if pkg_path else f"{cls}.java"
    hits = [f for f in files if f["filename"].endswith(suffix) or f["filename"].endswith("/" + cls + ".java")]
    exact = [f for f in hits if f["filename"].endswith(suffix)]
    hits = exact or hits
    if not hits:
        return None, None, "test_file_not_changed"
    f = hits[0]
    return f["filename"], f.get("previous_filename", f["filename"]), f["status"]
 
 
rows = []
try:
    for i, r in df.iterrows():
        out = r.to_dict()
        pr = parse_pr_link(r["PR Link"])
        fq = parse_fqn(r[test_col])
        out.update(pr_state=None, pr_merged=None, pre_sha=None, post_sha=None, post_source=None,
                   test_file_post=None, test_file_pre=None, file_status=None,
                   test_class=None, test_method=None, resolve_note="")
        if not pr:
            out["resolve_note"] = "bad_pr_link"
        elif not fq:
            out["resolve_note"] = "bad_test_name"
        else:
            owner, repo, n = pr
            info = resolve_pr(owner, repo, n)
            pkg_path, cls, method = fq
            out.update({k: info[k] for k in ("pr_state", "pr_merged", "pre_sha", "post_sha", "post_source")})
            out["test_class"], out["test_method"] = cls, method
            if info["pr_state"] == "unavailable":
                out["resolve_note"] = "pr_unavailable"
            elif not info["pr_merged"]:
                out["resolve_note"] = "pr_not_merged"
            else:
                post_p, pre_p, status = find_test_file(info["files"], pkg_path, cls)
                out.update(test_file_post=post_p, test_file_pre=pre_p, file_status=status)
                out["resolve_note"] = "ok" if post_p and info["post_sha"] else (status or "no_post_sha")
        rows.append(out)
        if len(rows) % 25 == 0:
            print(f"  {len(rows)}/{len(df)} rows", file=sys.stderr)
except RateLimited as e:
    print(f"\nGitHub rate limit hit after {len(rows)} rows: {e}\n"
          "Cache is saved; wait for the quota to reset and re-run.", file=sys.stderr)
 
res = pd.DataFrame(rows)
res.to_csv(ROOT / "data/interim/resolved_candidates.csv", index=False)
print(res["resolve_note"].value_counts().to_string())
print(f"\n{(res['resolve_note'] == 'ok').sum()} of {len(res)} rows have a changed test file -> usable for step 3")
 