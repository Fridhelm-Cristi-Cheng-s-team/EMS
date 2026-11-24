"""Plot the old and revised valid cells at their respective tabulation resolution."""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from review import read

cli = argparse.ArgumentParser()
cli.add_argument("--original",type=Path,default=Path("original_replay"))
cli.add_argument("--out",type=Path,default=Path("outputs"))
args = cli.parse_args()
old = read(args.original/"propeller_map.csv")
new = read(args.out/"propeller_map.csv")
fig, axes = plt.subplots(3, 3, figsize=(12, 8), sharex=True, layout="constrained")
for i, candidate in enumerate(("PROP-A","PROP-B","PROP-C")):
    for j, (variable, label) in enumerate((("CT","Thrust coefficient"),("CQ","Torque coefficient"),("eta","Efficiency"))):
        ax = axes[i,j]
        ax.grid(color="#b6c6cc",alpha=.35)
        for source, run, valid, style in ((old,"05A","map_valid","--"),(new,"05AR","valid","-")):
            rr = [r for r in source if r["candidate_id"]==candidate]
            field = "eta_prop" if variable=="eta" and run=="05A" else variable
            ax.plot([float(r["J"]) for r in rr],
                    [float(r[field]) if r[valid]=="True" else np.nan for r in rr],
                    style, label=run, color="#77838d" if run=="05A" else "#17697a", lw=1.8)
        if i==0:
            ax.set_title(label)
        if j==0:
            ax.set_ylabel(candidate)
        if i==2:
            ax.set_xlabel("Advance ratio J")
axes[0,2].legend(frameon=False)
fig.suptitle("EMS V3  |  Powered axial propeller map comparison  |  valid cells only")
fig.savefig(args.out/"propeller_map_comparison.png",dpi=165)
