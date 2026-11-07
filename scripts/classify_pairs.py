import argparse
import json
import sys
from pathlib import Path
 
import numpy as np
import pandas as pd
 
ROOT = Path(__file__).resolve().parent.parent
 
 
# --------------------------------------------------------------------------
# Model loading / inference  (needs torch + transformers; imported lazily)
# --------------------------------------------------------------------------
def load_model(model_path, base_model, num_labels, device):
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
 
    p = Path(model_path)
    if p.is_dir():
        if not (p / "config.json").exists():
            sys.exit(f"{p} is a directory but has no config.json. Point --model at the folder "
                     "that contains config.json, or at a .pt/.bin file.")
        has_tok = any((p / f).exists() for f in ("tokenizer.json", "vocab.json", "tokenizer_config.json"))
        tok = AutoTokenizer.from_pretrained(p if has_tok else base_model)
        model = AutoModelForSequenceClassification.from_pretrained(p)
    else:
        try:
            obj = torch.load(p, map_location="cpu", weights_only=True)
        except Exception:
            print("note: weights_only load failed; loading as a full pickle "
                  "(only do this for the authors' released artifact)", file=sys.stderr)
            obj = torch.load(p, map_location="cpu", weights_only=False)
        tok = AutoTokenizer.from_pretrained(base_model)
        if isinstance(obj, torch.nn.Module):
            model = obj
        else:
            sd = obj
            for k in ("model_state_dict", "state_dict", "model"):
                if isinstance(sd, dict) and isinstance(sd.get(k), dict):
                    sd = sd[k]
            sd = {k.removeprefix("module."): v for k, v in sd.items()}
            model = AutoModelForSequenceClassification.from_pretrained(base_model, num_labels=num_labels)
            res = model.load_state_dict(sd, strict=False)
            bad = [k for k in list(res.missing_keys) + list(res.unexpected_keys) if "position_ids" not in k]
            if bad:
                sys.exit("The checkpoint's weights do not match RobertaForSequenceClassification "
                         f"(first mismatches: {bad[:6]}).\nThe authors probably use a custom classification "
                         "head. Open the FlakyLens src/ file that builds the model and adapt load_model().")
    model.to(device).eval()
    return tok, model
 
 
def predict(texts, tok, model, device, max_len, batch_size=8):
    """Return (probs [n, n_classes], n_tokens [n]) for a list of code strings."""
    import torch
 
    probs, ntok = [], []
    with torch.no_grad():
        for i in range(0, len(texts), batch_size):
            chunk = texts[i:i + batch_size]
            enc = tok(chunk, truncation=True, max_length=max_len, padding=True, return_tensors="pt")
            logits = model(**{k: v.to(device) for k, v in enc.items()}).logits
            probs.append(torch.softmax(logits, dim=-1).cpu().numpy())
            ntok += [len(tok.tokenize(t)) + 2 for t in chunk]  # +2: <s>, </s>  (untruncated length)
    return np.concatenate(probs), np.array(ntok)
 
 
# --------------------------------------------------------------------------
# Pure-pandas parts (no torch needed)
# --------------------------------------------------------------------------
def squash(s):
    return " ".join(str(s).split())
 
 
def label_names(flakylens_csv, n_classes):
    names = {i: f"class_{i}" for i in range(n_classes)}
    if flakylens_csv:
        d = pd.read_csv(flakylens_csv, usecols=["label", "category"]).drop_duplicates()
        names.update({int(r.label): str(r.category) for r in d.itertuples()})
    return names
 
 
def load_pairs(pairs_dir):
    rows = []
    for d in sorted(Path(pairs_dir).glob("*/")):
        if (d / "pre.java").exists() and (d / "post.java").exists():
            meta = json.loads((d / "meta.json").read_text()) if (d / "meta.json").exists() else {}
            rows.append({"pair_id": d.name, "idoft_category": meta.get("category"),
                         "pre": (d / "pre.java").read_text(), "post": (d / "post.java").read_text()})
    return rows
 
 
def build_table(pairs, pre_p, post_p, pre_n, post_n, names, max_len, nonflaky, seen_codes=None):
    k = pre_p.shape[1]
    out = pd.DataFrame({
        "pair_id": [p["pair_id"] for p in pairs],
        "idoft_category": [p["idoft_category"] for p in pairs],
        "pre_tokens": pre_n, "post_tokens": post_n,
        "truncated": (pre_n > max_len) | (post_n > max_len),
    })
    for tag, P in (("pre", pre_p), ("post", post_p)):
        top = P.argmax(1)
        out[f"{tag}_top"] = top
        out[f"{tag}_top_name"] = [names[int(t)] for t in top]
        out[f"{tag}_conf"] = P.max(1)
    out["top1_changed"] = out["pre_top"] != out["post_top"]
    # confidence in the class the model chose for the PRE-fix code, before vs after the fix
    idx = np.arange(len(out))
    out["p_pre_class_pre"] = pre_p[idx, out["pre_top"].values]
    out["p_pre_class_post"] = post_p[idx, out["pre_top"].values]
    out["delta_pre_class"] = out["p_pre_class_post"] - out["p_pre_class_pre"]
    if nonflaky is not None:
        out["p_nonflaky_pre"] = pre_p[:, nonflaky]
        out["p_nonflaky_post"] = post_p[:, nonflaky]
    for i in range(k):
        out[f"p_{names[i]}_pre"] = pre_p[:, i]
        out[f"p_{names[i]}_post"] = post_p[:, i]
    if seen_codes is not None:
        out["pre_in_flakylens_csv"] = [squash(p["pre"]) in seen_codes for p in pairs]
    return out
 
 
def summarize(out, names, nonflaky):
    n = len(out)
    lines = [f"pairs: {n}   truncated at max length: {int(out['truncated'].sum())}"]
    if "pre_in_flakylens_csv" in out:
        lines.append(f"pre-fix code found verbatim in the FlakyLens dataset (possible train/test overlap): "
                     f"{int(out['pre_in_flakylens_csv'].sum())}")
    lines.append("\npre-fix top-1 prediction counts:\n" + out["pre_top_name"].value_counts().to_string())
    lines.append(f"\ntop-1 changed after the fix: {int(out['top1_changed'].sum())}/{n} "
                 f"({out['top1_changed'].mean():.0%})")
    if nonflaky is not None:
        flaky_pre = out[out["pre_top"] != nonflaky]
        lines.append(f"\nmodel called the PRE-fix code flaky: {len(flaky_pre)}/{n}")
        lines.append("(pairs the model already calls non-flaky before the fix cannot show a fix effect)")
        if len(flaky_pre):
            flip = int((flaky_pre["post_top"] == nonflaky).sum())
            lines.append(f"  of those, post-fix flipped to non-flaky: {flip}/{len(flaky_pre)} ({flip/len(flaky_pre):.0%})")
            lines.append(f"  of those, mean confidence change in the pre-predicted class: "
                         f"{flaky_pre['delta_pre_class'].mean():+.3f}  (negative = confidence dropped, as expected)")
            lines.append(f"  of those, confidence dropped: {int((flaky_pre['delta_pre_class'] < 0).sum())}/{len(flaky_pre)}")
            by = flaky_pre.groupby("pre_top_name").agg(n=("pair_id", "size"),
                                                        flipped=("post_top", lambda s: int((s == nonflaky).sum())),
                                                        mean_delta=("delta_pre_class", "mean"))
            lines.append("\nper pre-predicted category:\n" + by.round(3).to_string())
    return "\n".join(lines)
 
 
def run_sanity(csv_path, n, tok, model, device, max_len):
    d = pd.read_csv(csv_path, usecols=["full_code", "label"])
    d = d.sample(n=min(n, len(d)), random_state=0)
    probs, _ = predict(d["full_code"].astype(str).tolist(), tok, model, device, max_len)
    pred = probs.argmax(1)
    acc = float((pred == d["label"].values).mean())
    print(f"sanity: accuracy on {len(d)} labelled FlakyLens tests = {acc:.1%}")
    print("(these include tests the model was trained on, so expect HIGH accuracy; this only checks that "
          "loading, tokenization and the label order are right)")
    if acc < 0.5:
        print("WARNING: accuracy is low. Suspect the loader, the tokenizer, or the label order.")
    return acc
 
 
# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", required=True, help="HF directory (config.json) or .pt/.bin/.pth file")
    ap.add_argument("--base-model", default="microsoft/codebert-base",
                    help="used for the tokenizer / architecture when --model is a bare weights file")
    ap.add_argument("--flakylens-csv", help="FlakyLens_dataset_with_nonflaky_indented.csv (label names, overlap check)")
    ap.add_argument("--num-labels", type=int, default=6)
    ap.add_argument("--nonflaky-label", type=int, default=5, help="label id of the non-flaky class (5 in the FlakyLens CSV)")
    ap.add_argument("--max-len", type=int, default=512)
    ap.add_argument("--pairs", default=str(ROOT / "data" / "pairs"))
    ap.add_argument("--out", default=str(ROOT / "results" / "pair_predictions.csv"))
    ap.add_argument("--device", default="auto")
    ap.add_argument("--sanity", type=int, default=0, metavar="N",
                    help="only check the model on N labelled rows of --flakylens-csv, then exit")
    args = ap.parse_args()
 
    import torch
    device = ("cuda" if torch.cuda.is_available() else "cpu") if args.device == "auto" else args.device
    tok, model = load_model(args.model, args.base_model, args.num_labels, device)
    print(f"model loaded on {device}")
 
    if args.sanity:
        if not args.flakylens_csv:
            sys.exit("--sanity needs --flakylens-csv")
        run_sanity(args.flakylens_csv, args.sanity, tok, model, device, args.max_len)
        return
 
    pairs = load_pairs(args.pairs)
    if not pairs:
        sys.exit(f"no pairs found in {args.pairs} (expected <pair_id>/pre.java and post.java)")
    pre_p, pre_n = predict([p["pre"] for p in pairs], tok, model, device, args.max_len)
    post_p, post_n = predict([p["post"] for p in pairs], tok, model, device, args.max_len)
 
    names = label_names(args.flakylens_csv, pre_p.shape[1])
    seen = None
    if args.flakylens_csv:
        seen = {squash(c) for c in pd.read_csv(args.flakylens_csv, usecols=["full_code"])["full_code"].astype(str)}
    nonflaky = args.nonflaky_label if args.nonflaky_label < pre_p.shape[1] else None
    out = build_table(pairs, pre_p, post_p, pre_n, post_n, names, args.max_len, nonflaky, seen)
 
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out, index=False)
    print(f"wrote {args.out}\n")
    print(summarize(out, names, nonflaky))
 
 
if __name__ == "__main__":
    main()
 