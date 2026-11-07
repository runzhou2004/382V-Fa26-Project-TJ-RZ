import pandas as pd

df = pd.read_csv("data/pr-data.csv")
cols = {c: c for c in df.columns}
test_col = next(c for c in df.columns if c.startswith("Fully-Qualified Test Name"))

keep = df[
    (df["Status"] == "Accepted")
    & df["PR Link"].notna()
    & df["Category"].notna()
]
# one category per test keeps the label unambiguous (multi-category rows contain ';')
keep = keep[~keep["Category"].str.contains(";")]

print(keep["Category"].value_counts())
print(keep["Project URL"].nunique(), "projects,", len(keep), "tests")
keep.to_csv("data/interim/accepted_candidates.csv", index=False)