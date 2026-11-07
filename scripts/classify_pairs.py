import argparse
import json
import sys
import textwrap
from pathlib import Path
 
import numpy as np
import pandas as pd
 
ROOT = Path(__file__).resolve().parent.parent
BASE_MODEL = "microsoft/codebert-base"
N_CLASSES = 6
NONFLAKY = 5          # class id of "not flaky" (the authors treat category 5 as non-flaky)
MAX_LEN = 512
GROUPS = (1, 2, 3, 4)
 
 
# --------------------------------------------------------------------------
# Model wrapper (needs torch / transformers / the authors' codebert_model.py)
# --------------------------------------------------------------------------
class Scorer:
    def __init__(self, src_dir, models_dir, pattern, device):
        import torch
        from transformers import AutoConfig, AutoModel, AutoTokenizer
 
        sys.path.insert(0, str(src_dir))
        try:
            from codebert_model import BERT_Arch   # the authors' own class
        except ImportError as e:
            sys.exit(f"Could not import codebert_model from {src_dir}: {e}\n"
                     "Use --src-dir to point at the folder containing codebert_model.py.")
        self.torch = torch
        self.device = device
        self.models_dir, self.pattern, self.loaded = Path(models_dir), pattern, None
        # same construction as utils.codebert_model_define()
        cfg = AutoConfig.from_pretrained(BASE_MODEL, return_dict=False, output_hidden_states=True)
        self.tok = AutoTokenizer.from_pretrained(BASE_MODEL)
        self.model = BERT_Arch(AutoModel.from_pretrained(BASE_MODEL, config=cfg), N_CLASSES)
        self.model.to(device).eval()
 
    def encode(self, texts):
        enc = self.tok(texts, max_length=MAX_LEN, padding="max_length", truncation=True)
        n_tok = np.array([len(self.tok.tokenize(t)) + 2 for t in texts])  # untruncated length
        return enc["input_ids"], enc["attention_mask"], n_tok
 
    def _use(self, k):
        if self.loaded == k:
            return
        path = self.models_dir / self.pattern.format(k=k)
        if not path.exists():
            sys.exit(f"missing checkpoint: {path}")
        self.model.load_state_dict(self.torch.load(path, map_location=self.device))
        self.model.eval()
        self.loaded = k
 
    def score(self, k, ids, mask, batch_size=8):
        """Probabilities [n, 6] from the group-k model."""
        torch = self.torch
        self._use(k)
        out = []
        with torch.no_grad():
            for i in range(0, len(ids), batch_size):
                s = torch.tensor(ids[i:i + batch_size]).long().to(self.device)
                m = torch.tensor(mask[i:i + batch_size]).long().to(self.device)
                out.append(torch.exp(self.model(s, m)).cpu().numpy())   # model returns LogSoftmax
        return np.concatenate(out) if out else np.zeros((0, N_CLASSES))
 
 
# --------------------------------------------------------------------------
# Data helpers (pure pandas)
# --------------------------------------------------------------------------
def squash(s):
    return " ".join(str(s).split())
 
 
def project_key(url_or_name):
    """'https://github.com/apache/hadoop' -> 'apache_hadoop' (FlakyLens naming), lowercased."""
    s = str(url_or_name).strip().rstrip("/")
    if "github.com/" in s:
        owner, repo = s.split("github.com/")[1].split("/")[:2]
        s = f"{owner}_{repo}"
    return s.lower()
 
 
def class_columns(df):
    """In the FlakyLens CSVs one of `label`/`category` holds the integer class id and
    the other the name (they are swapped in some files); detect which is which."""
    if pd.api.types.is_numeric_dtype(df["category"]):
        return df["category"].astype(int), df["label"].astype(str)
    return df["label"].astype(int), df["category"].astype(str)
 
 
def load_test_sets(data_dir):
    sets = {}
    for k in GROUPS:
        f = Path(data_dir) / f"test_set_{k}.csv"
        if f.exists():
            sets[k] = pd.read_csv(f)
        else:
            print(f"warning: {f} not found; group {k} cannot be used for project matching", file=sys.stderr)
    return sets
 
 
def class_names(test_sets):
    names = {i: f"class_{i}" for i in range(N_CLASSES)}
    for df in test_sets.values():
        ids, nm = class_columns(df)
        names.update(dict(zip(ids, nm)))
    return names
 
 
def project_groups(test_sets):
    """project key -> set of groups whose HELD-OUT test set contains that project."""
    out = {}
    for k, df in test_sets.items():
        for p in df["project"].astype(str).map(project_key).unique():
            out.setdefault(p, set()).add(k)
    return out
 
 
def code_lookup(test_sets, names):
    """squashed code -> (class id, class name) for tests that are in the FlakyLens dataset."""
    out = {}
    for df in test_sets.values():
        ids, nm = class_columns(df)
        for code, i, n in zip(df["full_code"].astype(str), ids, nm):
            out[squash(code)] = (int(i), n)
    return out
 
 
def load_pairs(pairs_dir, dedent=True):
    rows = []
    for d in sorted(Path(pairs_dir).glob("*/")):
        if not ((d / "pre.java").exists() and (d / "post.java").exists()):
            continue
        meta = json.loads((d / "meta.json").read_text(encoding="utf-8")) if (d / "meta.json").exists() else {}
        pre, post = (d / "pre.java").read_text(encoding="utf-8"), (d / "post.java").read_text(encoding="utf-8")
        if dedent:  # FlakyLens' dataset stores methods with the class indentation removed
            pre, post = textwrap.dedent(pre).strip("\n"), textwrap.dedent(post).strip("\n")
        rows.append({"pair_id": d.name, "idoft_category": meta.get("category"),
                     "project": project_key(meta.get("project", d.name.split("__")[0] + "_" + d.name.split("__")[1])),
                     "pre": pre, "post": post})
    return rows
 
 
def assign_groups(pairs, proj_groups):
    """Return (tuple of groups per pair, 'held_out' | 'all_groups_avg')."""
    groups, source = [], []
    for p in pairs:
        g = proj_groups.get(p["project"])
        groups.append(tuple(sorted(g)) if g else GROUPS)
        source.append("held_out" if g else "all_groups_avg")
    return groups, source
 
 
def classify(pairs, scorer, groups):
    """Score pre/post with the chosen model(s); average if several. Returns arrays + token info."""
    pre_ids, pre_mask, pre_n = scorer.encode([p["pre"] for p in pairs])
    post_ids, post_mask, post_n = scorer.encode([p["post"] for p in pairs])
    n = len(pairs)
    pre_sum, post_sum, cnt = np.zeros((n, N_CLASSES)), np.zeros((n, N_CLASSES)), np.zeros(n)
    for k in GROUPS:
        idx = [i for i, g in enumerate(groups) if k in g]
        if not idx:
            continue
        pre_sum[idx] += scorer.score(k, [pre_ids[i] for i in idx], [pre_mask[i] for i in idx])
        post_sum[idx] += scorer.score(k, [post_ids[i] for i in idx], [post_mask[i] for i in idx])
        cnt[idx] += 1
        print(f"  group {k} model: scored {len(idx)} pairs", file=sys.stderr)
    same = np.array([a == b for a, b in zip(pre_ids, post_ids)])
    return pre_sum / cnt[:, None], post_sum / cnt[:, None], pre_n, post_n, same
 
 
def build_table(pairs, pre_p, post_p, pre_n, post_n, same_input, groups, source, names, lookup):
    out = pd.DataFrame({
        "pair_id": [p["pair_id"] for p in pairs],
        "idoft_category": [p["idoft_category"] for p in pairs],
        "model_groups": ["+".join(map(str, g)) for g in groups],
        "group_source": source,
        "pre_tokens": pre_n, "post_tokens": post_n,
        "truncated": (pre_n > MAX_LEN) | (post_n > MAX_LEN),
        "identical_after_truncation": same_input,   # fix lies past token 512 -> no signal possible
    })
    for tag, P in (("pre", pre_p), ("post", post_p)):
        top = P.argmax(1)
        out[f"{tag}_top"] = top
        out[f"{tag}_top_name"] = [names[int(t)] for t in top]
        out[f"{tag}_conf"] = P.max(1)
    out["top1_changed"] = out["pre_top"] != out["post_top"]
    idx = np.arange(len(out))
    out["p_pre_class_pre"] = pre_p[idx, out["pre_top"].values]
    out["p_pre_class_post"] = post_p[idx, out["pre_top"].values]
    out["delta_pre_class"] = out["p_pre_class_post"] - out["p_pre_class_pre"]
    out["p_nonflaky_pre"], out["p_nonflaky_post"] = pre_p[:, NONFLAKY], post_p[:, NONFLAKY]
    for i in range(N_CLASSES):
        out[f"p_{names[i]}_pre"], out[f"p_{names[i]}_post"] = pre_p[:, i], post_p[:, i]
    hit = [lookup.get(squash(p["pre"])) for p in pairs]
    out["in_flakylens_dataset"] = [h is not None for h in hit]
    out["dataset_class"] = [h[1] if h else None for h in hit]   # the authors' ground-truth label, if the test is in their data
    return out
 
 
def summarize(out):
    n = len(out)
    L = [f"pairs: {n}",
         f"  scored by a held-out model (project not in that model's training data): {(out['group_source'] == 'held_out').sum()}",
         f"  scored by the average of all 4 models (project not in FlakyLens' data):   {(out['group_source'] != 'held_out').sum()}",
         f"longer than 512 tokens (truncated): {int(out['truncated'].sum())}",
         f"pre and post are IDENTICAL after truncation (fix lies past token 512, so no signal): "
         f"{int(out['identical_after_truncation'].sum())}",
         f"pre-fix code found verbatim in FlakyLens' dataset: {int(out['in_flakylens_dataset'].sum())}",
         "\npre-fix top-1 prediction counts:\n" + out["pre_top_name"].value_counts().to_string(),
         f"\ntop-1 changed after the fix: {int(out['top1_changed'].sum())}/{n} ({out['top1_changed'].mean():.0%})"]
    usable = out[~out["identical_after_truncation"]]
    flaky_pre = usable[usable["pre_top"] != NONFLAKY]
    L.append(f"\namong the {len(usable)} pairs whose input actually changes, the model called the PRE-fix code flaky in {len(flaky_pre)}")
    L.append("(pairs it already calls non-flaky before the fix cannot show a fix effect)")
    if len(flaky_pre):
        flip = int((flaky_pre["post_top"] == NONFLAKY).sum())
        L.append(f"  post-fix flipped to non-flaky: {flip}/{len(flaky_pre)} ({flip / len(flaky_pre):.0%})")
        L.append(f"  confidence in the pre-predicted class dropped: {int((flaky_pre['delta_pre_class'] < 0).sum())}/{len(flaky_pre)}; "
                 f"mean change {flaky_pre['delta_pre_class'].mean():+.3f}")
        by = flaky_pre.groupby("pre_top_name").agg(n=("pair_id", "size"),
                                                    flipped=("post_top", lambda s: int((s == NONFLAKY).sum())),
                                                    mean_delta=("delta_pre_class", "mean"))
        L.append("\nper pre-predicted category:\n" + by.round(3).to_string())
    return "\n".join(L)
 
 
def run_sanity(scorer, test_sets, n_total):
    """Score held-out rows with the matching model; accuracy should be far above chance (~17%)."""
    per = max(1, n_total // len(test_sets))
    tot = ok = 0
    for k, df in sorted(test_sets.items()):
        d = df.sample(n=min(per, len(df)), random_state=0)
        ids_true, _ = class_columns(d)
        ids, mask, _ = scorer.encode(d["full_code"].astype(str).tolist())
        pred = scorer.score(k, ids, mask).argmax(1)
        acc = float((pred == ids_true.values).mean())
        print(f"group {k}: accuracy {acc:.1%} on {len(d)} held-out tests")
        tot += len(d)
        ok += int((pred == ids_true.values).sum())
    print(f"overall: {ok / tot:.1%}  (random guessing would be ~17%)")
    if ok / tot < 0.4:
        print("WARNING: very low. Something is wrong with loading, tokenizing or the group/checkpoint pairing.")
 
 
# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src-dir", default="/app/src", help="folder containing the authors' codebert_model.py")
    ap.add_argument("--data-dir", default="/app/src/FlakyLens_Categorization_PerProject-Data",
                    help="folder containing test_set_1..4.csv")
    ap.add_argument("--models-dir", default="/app/models")
    ap.add_argument("--weights-pattern", default="per_project_model_weights_on__dataset_project_group_{k}.pt")
    ap.add_argument("--pairs", default=str(ROOT / "data" / "pairs"))
    ap.add_argument("--out", default=str(ROOT / "results" / "pair_predictions.csv"))
    ap.add_argument("--device", default="auto")
    ap.add_argument("--no-dedent", action="store_true", help="do not strip the common indentation from methods")
    ap.add_argument("--sanity", type=int, default=0, metavar="N", help="check the models on N held-out tests, then exit")
    args = ap.parse_args()
 
    import torch
    device = ("cuda" if torch.cuda.is_available() else "cpu") if args.device == "auto" else args.device
    scorer = Scorer(args.src_dir, args.models_dir, args.weights_pattern, device)
    print(f"model ready on {device}", file=sys.stderr)
 
    test_sets = load_test_sets(args.data_dir)
    if not test_sets:
        sys.exit(f"no test_set_*.csv found in {args.data_dir}")
    if args.sanity:
        return run_sanity(scorer, test_sets, args.sanity)
 
    pairs = load_pairs(args.pairs, dedent=not args.no_dedent)
    if not pairs:
        sys.exit(f"no pairs found in {args.pairs}")
    names = class_names(test_sets)
    groups, source = assign_groups(pairs, project_groups(test_sets))
    pre_p, post_p, pre_n, post_n, same = classify(pairs, scorer, groups)
    out = build_table(pairs, pre_p, post_p, pre_n, post_n, same, groups, source, names, code_lookup(test_sets, names))
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out, index=False)
    print(f"wrote {args.out}\n")
    print(summarize(out))
 
 
if __name__ == "__main__":
    main()