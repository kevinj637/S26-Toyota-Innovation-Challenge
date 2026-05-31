"""Shared constants — single source of truth for the whole pipeline."""

FS_HZ = 1000            # nominal sampling rate (Hz) for simulator
WINDOW_S = 0.075        # feature window length (s) — within the 50-100ms design range
HOP_S = 0.025           # window hop (s) — 3x overlap

FEATURE_NAMES = ["mean", "std", "rms", "peak", "max_slope", "half_diff"]
CLASSES = ["normal", "startup", "stall"]

# State machine debounce
ENTER_N = 3             # consecutive 'stall' windows to raise alarm
EXIT_M = 5              # consecutive 'normal' windows to clear alarm
