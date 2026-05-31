# Demo Runbook

How to run the live demo (Arduino Uno R4 + web dashboard + on-chip LED). Narration is in `PITCH.md`.

## One-time wiring
Low-side shunt (see `HARDWARE.md`): `supply(+) → motor → node_A → 0.1Ω → supply(−)`,
**A0 → node_A**, **board GND → supply(−)**, flyback diode across the motor. Supply **5 V**.

## Start the demo
1. **Flash the demo firmware** (streams to the dashboard **and** runs the tree on-chip + LED):
   ```bash
   bash scripts/flash_demo.sh
   ```
2. **Open the dashboard** (port from `arduino-cli board list`, e.g. `/dev/cu.usbmodem1301`):
   ```bash
   .venv/bin/python -m web.app --source serial --port /dev/cu.usbmodemXXXX
   ```
   Browser → **http://localhost:5050**
3. Power the motor (supply output ON, 5 V).

## The sequence (money shot)
| Action | Dashboard | Onboard LED |
|---|---|---|
| Motor running | 🟢 GREEN | off |
| Power-cycle 2–3× | spikes, stays 🟢 | off  ← **no false alarm on start-up** |
| Hold the shaft (stall) | 🔴 RED in ~0.1 s | **ON** |
| Release | 🟢 GREEN | off |

**Edge-ML beat:** power the board from a USB charger (not the laptop), keep stalling — the **LED still
fires** because inference runs on-chip. No laptop, no cloud.

## Backup (no hardware)
```bash
.venv/bin/python -m web.app --source sim
```
Replays the physics simulator through the same dashboard — green/orange/red all show. Use if the
bench setup misbehaves during judging.
