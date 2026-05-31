# realtime-stall-detector

Real-time DC motor stall detection for the Toyota Innovation Challenge (S26) — Fault Prediction track.

Detects motor stalls from current draw in real time, distinguishing a **startup inrush**
(brief high current) from a **true stall** (sustained high current) using windowed features
and a decision tree. Verified now with a physics-based current simulator; runs on real
hardware by switching the data source to an Arduino serial stream.

- **Design doc:** [docs/superpowers/specs/2026-05-29-realtime-motor-stall-detection-design.md](docs/superpowers/specs/2026-05-29-realtime-motor-stall-detection-design.md)
- **Status:** A1 + A2 fully implemented and verified (18 tests pass; confusion matrix clean).

## Phases

- **A1** — laptop-side inference: Arduino streams current → Python features → decision tree → live dashboard alert.
- **A2** — edge inference: decision tree exported to C, runs on the board itself (LED alert, no laptop).

## Web dashboard

Live current chart + record/save/train controls in the browser:

```bash
python -m web.app --source serial --port /dev/cu.usbmodemXXXX   # real hardware
python -m web.app --source sim                                  # no hardware (simulator)
```

Then open http://localhost:5050 — record labeled segments (normal/startup/stall), save the dataset,
click Train, and watch the live green/orange/red state.
(Port 5050 avoids macOS AirPlay Receiver, which occupies 5000.)
