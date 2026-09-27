"""Usage: python3 scripts/dif_dataset.py <dataset_name> <path.csv> --t T_COL --y Y_COL [--cols a b c]
Appends DIF rows to results/dif_by_dataset.csv. The CSV must be time-orderable."""
import sys, argparse; sys.path.insert(0, "src")
import pandas as pd
from t13.datasets import dif_table
p = argparse.ArgumentParser(); p.add_argument("name"); p.add_argument("csv")
p.add_argument("--t", required=True); p.add_argument("--y", required=True); p.add_argument("--cols", nargs="*")
p.add_argument("--grains", nargs="*", default=["flow", "window:60"])
a = p.parse_args()
df = pd.read_csv(a.csv); df = df.rename(columns={a.t: "t", a.y: "y"})
tab = dif_table(df, a.name, grains=a.grains, columns=a.cols)
try:
    old = pd.read_csv("results/dif_by_dataset.csv"); tab = pd.concat([old[old.dataset != a.name], tab])
except FileNotFoundError:
    pass
tab.to_csv("results/dif_by_dataset.csv", index=False); print(tab.to_string())
