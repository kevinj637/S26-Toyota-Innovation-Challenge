"""Complete multi-motor analysis on Toyota's real telemetry (full date range).

Runs our benchtop feature pipeline (src/features.compute_features, unchanged) across EVERY joint
of EVERY robot, pooling windows from ALL available day-files per robot (not just one day), then
trains an UNSUPERVISED Isolation Forest on the six features (the data has no fault labels) to flag
abnormal-load windows. Output: a robot x joint anomaly heatmap + a summary.

Joints are aligned by 1-based POSITION (robots vary: robot_1 is current_0..7; robot_4 is 7-DOF).
Logging is event-driven/variable-rate (~55 Hz during motion), so windows are filtered to dense,
active segments. Per (robot, joint) windows are capped and accumulated across the robot's days.
"""
import glob
import os
import sys
from collections import defaultdict

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.ensemble import IsolationForest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.features import compute_features, FEATURE_NAMES  # noqa: E402  (benchtop code, unchanged)

DATA_DIR = "/tmp/toyota_telemetry/UW_Hackathon_Raw_Data"
HERE = os.path.dirname(os.path.abspath(__file__))
PLOTS = os.path.join(HERE, "plots")
os.makedirs(PLOTS, exist_ok=True)

NJOINTS = 8
CHUNK_ROWS = 150_000        # rows read from the start of each day-file
CAP_PER_JOINT = 1500        # per (robot, joint), pooled across the robot's day-files
WIN, HOP = 75, 25           # window/hop in samples (~1.3 s at ~55 Hz)
ACTIVE_A = 0.5              # |current| threshold to call a window "active"
DENSE_S = 1.5              # max window time-span to count as densely logged (not idle)


def files_per_robot():
    d = defaultdict(list)
    for p in sorted(glob.glob(os.path.join(DATA_DIR, "robot_*.csv.xz"))):
        d[os.path.basename(p).split("_2026")[0]].append(p)
    return dict(sorted(d.items()))


def collect_robot(paths):
    """Pool dense active windows per joint position across the robot's day-files (capped)."""
    per_joint = defaultdict(list)
    files_used, rows = 0, 0
    for path in paths:
        df = next(pd.read_csv(path, compression="xz", chunksize=CHUNK_ROWS))
        files_used += 1
        rows += len(df)
        t = (df["ts"].to_numpy().astype(float) - float(df["ts"].iloc[0])) / 1e9
        cols = [c for _, c in sorted((int(c.split("_")[1]), c)
                                     for c in df.columns if c.startswith("current_"))]
        for pos, col in enumerate(cols, start=1):
            if len(per_joint[pos]) >= CAP_PER_JOINT:
                continue
            I = np.abs(df[col].to_numpy())
            i = 0
            while i + WIN <= len(df) and len(per_joint[pos]) < CAP_PER_JOINT:
                if (t[i + WIN - 1] - t[i]) < DENSE_S and I[i:i + WIN].max() > ACTIVE_A:
                    per_joint[pos].append(compute_features(t[i:i + WIN], I[i:i + WIN]))
                i += HOP
        if cols and all(len(per_joint[p]) >= CAP_PER_JOINT for p in range(1, len(cols) + 1)):
            break  # this robot is fully sampled; skip its remaining days
    return per_joint, files_used, rows


def main():
    fpr = files_per_robot()
    robots = sorted(fpr)
    print(f"Analyzing {len(robots)} robots; {sum(len(v) for v in fpr.values())} day-files available")

    X, meta = [], []
    tot_files, tot_rows = 0, 0
    for ri, robot in enumerate(robots):
        pj, fu, rows = collect_robot(fpr[robot])
        tot_files += fu; tot_rows += rows
        nwin = sum(len(v) for v in pj.values())
        print(f"  {robot}: {fu} day-files, {rows:,} rows scanned, {nwin} windows")
        for pos, fvs in pj.items():
            for fv in fvs:
                X.append(fv); meta.append((ri, pos))
    X = np.array(X); meta = np.array(meta)
    n_motors = len({tuple(m) for m in meta})
    print(f"\nCoverage: {tot_files} day-files, {tot_rows:,} rows scanned | "
          f"{n_motors} active motors | {len(X)} feature windows "
          f"(features unchanged from benchtop: {FEATURE_NAMES})")

    iso = IsolationForest(contamination=0.05, random_state=0).fit(X)
    anom = iso.predict(X) == -1
    print(f"Isolation Forest flagged {int(anom.sum())} / {len(X)} windows as anomalous (~5% target)")

    rate = np.full((len(robots), NJOINTS), np.nan)
    for ri in range(len(robots)):
        for j in range(1, NJOINTS + 1):
            m = (meta[:, 0] == ri) & (meta[:, 1] == j)
            if m.sum() >= 10:
                rate[ri, j - 1] = anom[m].mean()

    fig, ax = plt.subplots(figsize=(9, 5))
    im = ax.imshow(rate * 100, cmap="OrRd", aspect="auto", vmin=0)
    ax.set_xticks(range(NJOINTS)); ax.set_xticklabels([f"J{j}" for j in range(1, NJOINTS + 1)])
    ax.set_yticks(range(len(robots))); ax.set_yticklabels(robots)
    ax.set_xlabel("Joint (motor)"); ax.set_title(
        "Toyota fleet (all days) — anomalous-load rate per motor "
        "(our features + unsupervised Isolation Forest)")
    for ri in range(len(robots)):
        for j in range(NJOINTS):
            if not np.isnan(rate[ri, j]):
                ax.text(j, ri, f"{rate[ri, j]*100:.0f}", ha="center", va="center", fontsize=8)
    fig.colorbar(im, label="% windows flagged anomalous")
    fig.tight_layout(); fig.savefig(os.path.join(PLOTS, "fleet_anomaly_heatmap.png"), dpi=120)
    plt.close(fig)

    flat = [(robots[ri], j + 1, rate[ri, j]) for ri in range(len(robots))
            for j in range(NJOINTS) if not np.isnan(rate[ri, j])]
    flat.sort(key=lambda r: -r[2])
    print("\nMost anomaly-prone motors (robot, joint, %flagged):")
    for r, j, v in flat[:5]:
        print(f"  {r} joint {j}: {v*100:.1f}%")
    print("\nsaved plots/fleet_anomaly_heatmap.png")


if __name__ == "__main__":
    main()
