"""Produce labeled current data.

- Sim mode (tested, used now): auto-labeled scenario -> CSV.
- Serial mode (event): guided segments timed against the live Arduino stream.
"""
import argparse
import csv
import pandas as pd
from src.simulator import simulate
from src.sources import SerialSource

# Repeated states give the tree more examples; multiple startup/stall events.
DEFAULT_SCENARIO = [
    ("off", 0.5), ("startup", 0.3), ("running", 1.5), ("stall", 0.8), ("running", 1.0),
    ("off", 0.3), ("startup", 0.3), ("running", 1.2), ("stall", 0.6), ("running", 0.8),
    ("off", 0.4),
]

def generate_sim_dataset(out_path, scenario=DEFAULT_SCENARIO, fs=1000, seed=0):
    t, x, y = simulate(scenario, fs=fs, seed=seed)
    df = pd.DataFrame({"t_s": t, "current_a": x, "label": y})
    df.to_csv(out_path, index=False)
    return out_path

def collect_serial(out_path, port, baud=115200,
                   segments=(("normal", 10), ("stall", 5), ("normal", 10)),
                   startup_reps=6, startup_dur=0.8):
    """Guided collection: operator follows prompts; samples labeled by segment timing.

    Captures ALL THREE classes so the 3-class model trains correctly:
      - steady `normal` / `stall` via `segments`
      - `startup` inrush via repeated power-on bursts (the brief high-then-decaying spike).
        Without startup examples the model cannot learn "inrush != stall" and will
        false-alarm on every power-on.
    """
    src = SerialSource(port, baud)
    rows = []

    def record(label, dur):
        src.ser.reset_input_buffer()  # drop stale buffered samples from the previous state
        t0 = None
        for t_s, cur in src:
            if t0 is None:
                t0 = t_s
            rows.append((t_s, cur, label))
            if t_s - t0 >= dur:
                break

    for label, dur in segments:
        input(f"\n>>> Get the motor into '{label}' state, then press Enter to record {dur}s...")
        record(label, dur)

    print(f"\n=== Startup capture: {startup_reps} power-on cycles (records the inrush spike) ===")
    print("    Tip: flip the motor ON the instant you press Enter, so the burst starts at power-on.")
    for i in range(startup_reps):
        input(f">>> [{i+1}/{startup_reps}] Motor OFF. Press Enter, then IMMEDIATELY switch the motor ON...")
        record("startup", startup_dur)

    with open(out_path, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["t_s", "current_a", "label"]); w.writerows(rows)
    print(f"Wrote {len(rows)} samples to {out_path} (labels: normal / stall / startup)")
    return out_path

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["sim", "serial"], default="sim")
    ap.add_argument("--out", default="data/labeled.csv")
    ap.add_argument("--port", default=None)
    args = ap.parse_args()
    import os; os.makedirs("data", exist_ok=True)
    if args.source == "sim":
        generate_sim_dataset(args.out)
    else:
        collect_serial(args.out, args.port)
    print(f"Saved {args.out}")
