"""Transfer demo: run our benchtop stall-detection pipeline on Toyota's real 8-DOF arm telemetry.

Shows that the SAME windowed-feature code (src/features.py) that classifies stall on our benchtop
motor runs unchanged on Toyota's industrial-arm current. The dataset has no fault labels, so we apply
our features unsupervised and surface the highest-stress windows (high current), plus the benchtop
"stall" signature: high current + near-zero joint motion = force-without-motion (jam / overload).

Logging is event-driven/variable-rate with long idle stretches, so for a readable waveform plot we
CONCATENATE the active segments (idle removed) — showing ~8,000 samples of real activity (≈10x the
earlier single-burst view), not a few seconds.

Data: Toyota UW_Hackathon_Raw_Data (Google Drive). Set DATA_FILE below.
"""
import os
import sys

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.features import compute_features, FEATURE_NAMES  # noqa: E402  (benchtop code, unchanged)

DATA_FILE = "/tmp/toyota_telemetry/UW_Hackathon_Raw_Data/robot_0_2026-02-17.csv.xz"
HERE = os.path.dirname(os.path.abspath(__file__))
PLOTS = os.path.join(HERE, "plots")
os.makedirs(PLOTS, exist_ok=True)

ROWS = 250_000        # rows read from the start of the file
ACTIVE_A = 0.5        # |current| over which a row counts as "active"
TARGET = 8000         # concatenate active segments until we have this many active samples
WIN, HOP = 75, 25

df = next(pd.read_csv(DATA_FILE, compression="xz", chunksize=ROWS))
ts = df["ts"].to_numpy().astype(float)
cur_cols = [c for _, c in sorted((int(c.split("_")[1]), c) for c in df.columns if c.startswith("current_"))]
ang_cols = [c for _, c in sorted((int(c.split("_")[1]), c) for c in df.columns if c.startswith("joint_"))]

# --- find contiguous active segments and concatenate them (idle removed) ---
act = df[cur_cols].abs().max(axis=1).to_numpy() > ACTIVE_A
idx = np.where(act)[0]
brk = np.where(np.diff(idx) > 5)[0]
starts = np.concatenate([[idx[0]], idx[brk + 1]])
ends = np.concatenate([idx[brk] + 1, [idx[-1] + 1]])
segs = [(s, e) for s, e in zip(starts, ends) if e - s >= 50]

chosen, total = [], 0
for s, e in segs:
    chosen.append((s, e)); total += e - s
    if total >= TARGET:
        break

cur = {c: [] for c in cur_cols}
ang = {c: [] for c in ang_cols}
dt_parts, bounds = [], [0]
for s, e in chosen:
    for c in cur_cols:
        cur[c].append(df[c].to_numpy()[s:e])
    for c in ang_cols:
        ang[c].append(df[c].to_numpy()[s:e])
    lt = np.diff(ts[s:e]) / 1e9
    dt_parts.append(np.concatenate([[np.nan], lt]))   # break velocity at segment joins
    bounds.append(bounds[-1] + (e - s))
cur = {c: np.concatenate(v) for c, v in cur.items()}
ang = {c: np.concatenate(v) for c, v in ang.items()}
dt = np.concatenate(dt_parts)
x = np.arange(len(dt))
fs = np.nanmedian(1.0 / dt)
print(f"concatenated {len(chosen)} active segments -> {len(x)} samples (~{len(x)/fs:.0f}s of activity at ~{fs:.0f} Hz)")

# --- Plot 1: per-joint current, FACETED (one row per joint) so it stays readable at scale ---
n = len(cur_cols)
fig, axes = plt.subplots(n, 1, figsize=(12, 1.1 * n), sharex=True)
for axj, c in zip(axes, cur_cols):
    axj.plot(x, cur[c], lw=0.5, color="#2a6f97")
    axj.set_ylabel(c.replace("current_", "J"), rotation=0, ha="right", va="center", fontsize=9)
    axj.tick_params(labelsize=7)
    for b in bounds[1:-1]:
        axj.axvline(b, color="k", lw=0.3, alpha=0.15)
axes[0].set_title(f"Toyota 8-DOF arm — per-joint current, {len(x)} active samples "
                  f"(~{len(x)/fs:.0f}s of operation, idle removed)")
axes[-1].set_xlabel("active sample # (idle removed)")
fig.tight_layout(); fig.savefig(os.path.join(PLOTS, "joints_current.png"), dpi=120); plt.close(fig)

# --- most active joint: run OUR features + benchtop stall logic over all of it ---
ji = max(cur_cols, key=lambda c: np.mean(np.abs(cur[c])))
jang = ang_cols[cur_cols.index(ji)] if cur_cols.index(ji) < len(ang_cols) else ang_cols[-1]
I = np.abs(cur[ji])
vel = np.abs(np.diff(ang[jang], prepend=ang[jang][0]) / dt)   # |deg/s|, NaN across segment joins

tc, rms_i, mot = [], [], []
i = 0
while i + WIN <= len(I):
    fv = compute_features(np.arange(WIN) / fs, I[i:i + WIN])   # our benchtop feature code, unchanged
    tc.append(i + WIN / 2)
    rms_i.append(fv[FEATURE_NAMES.index("rms")])
    seg_vel = vel[i:i + WIN]
    mot.append(np.nanmean(seg_vel) if np.isfinite(seg_vel).any() else np.nan)
    i += HOP
tc, rms_i, mot = np.array(tc), np.array(rms_i), np.array(mot)
stress = rms_i > np.percentile(rms_i, 90)
print(f"joint {ji}: {len(tc)} windows | {int(stress.sum())} high mechanical-stress windows flagged")

# --- Plot 2: current + motion with flagged stress windows ---
fig, ax = plt.subplots(2, 1, figsize=(12, 6), sharex=True)
ax[0].plot(x, I, lw=0.6, color="#d8572a"); ax[0].set_ylabel(f"|{ji}| (A)")
ax[0].set_title(f"Toyota arm {ji}: benchtop features on real data — red = high mechanical-stress windows "
                f"({len(tc)} windows over {len(x)} active samples)")
ax[1].plot(x, vel, lw=0.6, color="#1f78b4"); ax[1].set_ylabel("|velocity| (deg/s)")
ax[1].set_xlabel("active sample # (idle removed)")
for tcj, st in zip(tc, stress):
    if st:
        for a in ax:
            a.axvspan(tcj - HOP / 2, tcj + HOP / 2, color="red", alpha=0.15)
plt.tight_layout(); plt.savefig(os.path.join(PLOTS, "joint_stall_risk.png"), dpi=120); plt.close()
print("saved plots/joints_current.png, plots/joint_stall_risk.png")
