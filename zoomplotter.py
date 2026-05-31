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


def graphZoomWindows(file_name, windows, yCols: list[YCol], pad=None,
                     smooth=True, export_prefix='MotorStallTestSetup/plots/zoom'):
    """One zoomed figure per stress window, saved as a separate PNG.

    file_name : the CSV (e.g. robot_7_...).
    windows   : list of (start, end) SAMPLE INDICES marking each red stress window.
                This is the piece you supply from your detection script. If you only
                have a centre + width, pass [(c - w//2, c + w//2), ...].
    yCols     : same tuples newplotters.py uses. Each gets its OWN stacked subplot
                sharing the x-axis (current and velocity have wildly different scales,
                so stacking beats the single-axis-with-offsets trick — you can read
                each shape on its own).
    pad       : context samples shown on each side of the window. Defaults to one
                full window-width, so you see the lead-in and the recovery.

    NOTE: no downsampling here on purpose. The whole point of a zoom is detail, and
    these slices are small enough to draw every point.
    """
    col_indices = sorted({col_to_index(c[1]) for c in yCols})
    times, cols = _read_columns(file_name, col_indices)
    n = len(times)
    if n == 0:
        print("No data parsed from file.")
        return

    for w_i, (start, end) in enumerate(windows):
        start, end = int(start), int(end)
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


# ---- Example usage (set the velocity column letter to whatever it is in your CSV) ----
if __name__ == "__main__":
    normal_filename = r'.\data\robot_7_2026-02-17.csv'
    stress_windows = [(16000, 16400), (30500, 30900)]  # <- from your detection script
    graphZoomWindows(normal_filename, stress_windows, [
        ('|current_3| (A)', 'T', 'green', 1, 0),
        ('|velocity| (deg/s)', 'AB', 'blue', 1, 0),  # <- confirm this column letter
    ])