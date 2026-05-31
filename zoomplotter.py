import matplotlib.pyplot as plt
import numpy as np
import csv

# Same convolution width as newplotters.py
WINDOW = 5


def col_to_index(index) -> int:
    """Excel-style column letter -> 0-based index ('a'->0, 't'->19, 'ab'->27).
    Pass-through if already an int. (newplotters.py duplicates this 3x; this is the
    single shared version, and it RAISES on bad input instead of returning the error.)"""
    if isinstance(index, str):
        index = index.lower()
        if len(index) > 2:
            raise TypeError(f"index '{index}' not valid")
        if len(index) == 2:
            return (ord(index[0]) - (ord('a') - 1)) * 26 + ord(index[1]) - ord('a')
        return ord(index) - ord('a')
    return index


def _read_columns(file_name, col_indices):
    """Read the CSV ONCE and pull out time (col 0) + the requested columns.

    newplotters.py re-parses the whole file once per column; on a 50k+ row robot
    log that's painfully slow. This reads it a single time. A row is only kept if
    EVERY requested column parses, so all arrays stay aligned with time.
    """
    col_indices = list(col_indices)
    times = []
    cols = {ci: [] for ci in col_indices}
    with open(file_name, 'r', newline='') as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        for row in reader:
            try:
                t = float(row[0])
                vals = {ci: float(row[ci]) for ci in col_indices}
            except (ValueError, IndexError):
                continue  # junk / short row -> skip whole row, keep alignment
            times.append(t)
            for ci in col_indices:
                cols[ci].append(vals[ci])
    times = np.array(times)
    if times.size:
        times = times - times[0]  # normalize so the axis starts at 0
    return times, {ci: np.array(v) for ci, v in cols.items()}


# Same YCol shape as newplotters.py: (name, col index/letter, color, multiplier, offset)
type colour = str
type YCol = tuple[str, int | str, colour, float, float]


def find_windows(series, thresh=None, k=3.0, min_len=20, min_gap=20):
    """Auto-detect stress regions: contiguous runs where `series` sits above a
    threshold. Use this when you DON'T have a window list from a detector — it just
    reads the signal and flags the spikes.

    thresh : level that counts as 'stressed'. If None, uses mean + k*std of the
             signal, which adapts to whatever baseline/noise the channel has.
    min_len: drop runs shorter than this (kills single-sample noise blips).
    min_gap: merge two runs separated by fewer than this many samples (so one event
             that briefly dips under the line isn't split into two).

    Returns a list of (start, end) sample-index tuples.
    """
    series = np.asarray(series, float)
    if thresh is None:
        thresh = series.mean() + k * series.std()
    hot = series > thresh
    edges = np.diff(hot.astype(int))
    starts = list(np.where(edges == 1)[0] + 1)
    ends = list(np.where(edges == -1)[0] + 1)
    if hot[0]:
        starts = [0] + starts
    if hot[-1]:
        ends = ends + [len(series)]
    runs = list(zip(starts, ends))

    merged = []  # merge runs that are closer than min_gap
    for s, e in runs:
        if merged and s - merged[-1][1] < min_gap:
            merged[-1] = (merged[-1][0], e)
        else:
            merged.append((s, e))
    out = [(s, e) for s, e in merged if e - s >= min_len]
    print(f"find_windows: thresh={thresh:.2f} -> {len(out)} regions")
    return out


def graphZoomWindows(file_name, windows, yCols: list[YCol], pad=None, max_files=20,
                     smooth=True, export_prefix='MotorStallTestSetup/plots/zoom'):
    """One zoomed figure per stress window, saved as a separate PNG.

    file_name : the CSV (e.g. robot_7_...).
    windows   : list of (start, end) SAMPLE INDICES marking each red stress window.
                Pass None to AUTO-DETECT them from the first yCol (spikes above
                mean + 3*std) — that's how you get dozens of files without a
                hand-typed list. If you only have a centre + width, pass
                [(c - w//2, c + w//2), ...].
    yCols     : same tuples newplotters.py uses. Each gets its OWN stacked subplot
                sharing the x-axis (current and velocity have wildly different scales,
                so stacking beats the single-axis-with-offsets trick — you can read
                each shape on its own).
    pad       : context samples shown on each side of the window. Defaults to one
                full window-width, so you see the lead-in and the recovery.
    max_files : cap on how many PNGs to emit. If you pass more windows than this,
                it samples them EVENLY across the run (early to late), so you get a
                representative spread of time periods instead of either two files or
                two thousand. Set to None to dump every window.

    NOTE: no downsampling here on purpose. The whole point of a zoom is detail, and
    these slices are small enough to draw every point.
    """
    col_indices = sorted({col_to_index(c[1]) for c in yCols})
    times, cols = _read_columns(file_name, col_indices)
    n = len(times)
    if n == 0:
        print("No data parsed from file.")
        return

    if windows is None:  # auto-detect from the first signal
        detect_idx = col_to_index(yCols[0][1])
        series = cols[detect_idx] * yCols[0][3] + yCols[0][4]
        windows = find_windows(series)
    windows = [(int(s), int(e)) for s, e in windows]
    total = len(windows)
    if max_files is not None and total > max_files:  # even spread across the run
        sel = np.linspace(0, total - 1, max_files).round().astype(int)
        windows = [windows[i] for i in sel]
    print(f"Rendering {len(windows)} of {total} windows...")

    for w_i, (start, end) in enumerate(windows):
        w_pad = pad if pad is not None else max(1, end - start)
        lo = max(0, start - w_pad)
        hi = min(n, end + w_pad)
        x = times[lo:hi]

        fig, axes = plt.subplots(len(yCols), 1, figsize=(10, 2.3 * len(yCols)),
                                 sharex=True)
        if len(yCols) == 1:
            axes = [axes]

        for ax, (name, idx, color, mult, off) in zip(axes, yCols):
            y = cols[col_to_index(idx)][lo:hi] * mult + off
            if smooth and len(y) >= WINDOW:
                y = np.convolve(y, np.ones(WINDOW) / WINDOW, mode='same')
            ax.plot(x, y, color=color, linewidth=0.8, label=name)
            # shade the actual flagged window across this subplot
            ax.axvspan(times[start], times[min(end, n - 1)],
                       color='red', alpha=0.15)
            ax.set_ylabel(name)
            ax.grid(True, linestyle='--', alpha=0.5)
            ax.legend(loc='upper right', fontsize=8)

        axes[0].set_title(f"Stress window {w_i}: samples {start}\u2013{end} "
                          f"(+/- {w_pad} context)")
        axes[-1].set_xlabel("Time (normalized)")
        fig.tight_layout()
        out = f"{export_prefix}_{start}_{end}.png"
        fig.savefig(out, dpi=120)
        plt.close(fig)
        print(f"Saved {out}")


def graphAllWindowsOverlay(file_name, windows, yCols: list[YCol], pad=50,
                           export_file='MotorStallTestSetup/plots/overlay.png'):
    """ALL windows on ONE figure, each aligned to its own start (x=0) and drawn
    translucent on top of each other, with a bold mean curve. This is the view that
    answers 'what does a stress event typically look like, and how consistent are
    they?' — tight overlap = a reliable signature, scatter = noisy windows.

    Scales to thousands of windows (unlike one-PNG-per-window). One stacked subplot
    per signal, sharing the relative-sample x-axis.
    """
    col_indices = sorted({col_to_index(c[1]) for c in yCols})
    times, cols = _read_columns(file_name, col_indices)
    n = len(times)
    if n == 0 or not windows:
        print("No data / no windows.")
        return

    windows = [(int(s), int(e)) for s, e in windows]
    Lmin = min(e - s for s, e in windows)  # shortest window, for the mean region

    fig, axes = plt.subplots(len(yCols), 1, figsize=(10, 2.6 * len(yCols)),
                             sharex=True)
    if len(yCols) == 1:
        axes = [axes]

    for ax, (name, idx, color, mult, off) in zip(axes, yCols):
        series = cols[col_to_index(idx)] * mult + off
        stack = []  # in-window portions, truncated to Lmin, for the mean
        for s, e in windows:
            lo, hi = max(0, s - pad), min(n, e + pad)
            rel = np.arange(lo - s, hi - s)  # 0 == window start
            ax.plot(rel, series[lo:hi], color=color, alpha=0.04, linewidth=0.6)
            w = series[s:s + Lmin]
            if len(w) == Lmin:
                stack.append(w)
        if stack:
            mean = np.mean(stack, axis=0)
            ax.plot(np.arange(Lmin), mean, color='black', linewidth=1.8,
                    label=f"{name} mean (n={len(stack)})")
        ax.axvspan(0, Lmin, color='red', alpha=0.08)  # typical window extent
        ax.axvline(0, color='red', linewidth=0.8, alpha=0.6)
        ax.set_ylabel(name)
        ax.grid(True, linestyle='--', alpha=0.5)
        ax.legend(loc='upper right', fontsize=8)

    axes[0].set_title(f"All {len(windows)} stress windows, aligned to start")
    axes[-1].set_xlabel("Samples relative to window start")
    fig.tight_layout()
    fig.savefig(export_file, dpi=120)
    plt.close(fig)
    print(f"Saved {export_file}")


def graphWindowGrid(file_name, windows, yCol: YCol, pad=50, max_panels=24,
                    cols_per_row=6, export_file='MotorStallTestSetup/plots/grid.png'):
    """Contact sheet: a grid of small zoomed panels, one per window, for ONE signal.
    If there are more windows than max_panels, it samples them evenly so the sheet
    stays readable and still spans the whole run. Call again with a different yCol
    (e.g. velocity) for that signal's sheet.
    """
    name, idx, color, mult, off = yCol
    ci = col_to_index(idx)
    times, cols = _read_columns(file_name, [ci])
    n = len(times)
    if n == 0 or not windows:
        print("No data / no windows.")
        return
    series = cols[ci] * mult + off

    windows = [(int(s), int(e)) for s, e in windows]
    total = len(windows)
    if total > max_panels:  # even spread across the run, not just the first few
        sel = np.linspace(0, total - 1, max_panels).round().astype(int)
        windows = [windows[i] for i in sel]

    rows = int(np.ceil(len(windows) / cols_per_row))
    fig, axes = plt.subplots(rows, cols_per_row,
                             figsize=(2.0 * cols_per_row, 1.6 * rows))
    axes = np.array(axes).reshape(-1)
    for ax, (s, e) in zip(axes, windows):
        lo, hi = max(0, s - pad), min(n, e + pad)
        rel = np.arange(lo - s, hi - s)
        ax.plot(rel, series[lo:hi], color=color, linewidth=0.7)
        ax.axvspan(0, e - s, color='red', alpha=0.15)
        ax.set_title(f"{s}", fontsize=7)
        ax.tick_params(labelsize=6)
    for ax in axes[len(windows):]:  # blank the unused cells
        ax.axis('off')

    fig.suptitle(f"{name}: showing {len(windows)} of {total} windows", fontsize=10)
    fig.tight_layout()
    fig.savefig(export_file, dpi=120)
    plt.close(fig)
    print(f"Saved {export_file}")


# ---- Example usage (set the velocity column letter to whatever it is in your CSV) ----
if __name__ == "__main__":
    normal_filename = r'.\data\robot_7_2026-02-17.csv'
    stress_windows = [(16000, 16400), (30500, 30900)]  # <- from your detection script

    cur = ('|current_3| (A)', 'T', 'green', 1, 0)
    vel = ('|velocity| (deg/s)', 'AB', 'blue', 1, 0)  # <- confirm this column letter

    # No window list needed: auto-detect spikes and dump up to 20 zoom files
    # spread across the whole run.
    graphZoomWindows(normal_filename, None, [cur, vel], max_files=20)

    # Or, if you DO have windows from your detector, pass them instead of None.
    # graphZoomWindows(normal_filename, stress_windows, [cur, vel])

    graphAllWindowsOverlay(normal_filename, find_windows(  # all events superimposed
        _read_columns(normal_filename, [col_to_index('T')])[1][col_to_index('T')]),
        [cur, vel])