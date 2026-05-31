# Hardware Setup, Measurement & Test Guide (Arduino Uno / ESP32-S3)

The firmware auto-detects the board:
- **Arduino Uno R4** (Minima/WiFi, Renesas RA4M1) — pin **A0**, **14-bit** ADC, 5 V reference.
  The 14-bit resolution compensates for the 5 V reference on the small 0.1 Ω shunt signal.
- **Arduino Uno R3 / Nano** (ATmega328) — pin **A0**, 10-bit ADC, **INTERNAL 1.1 V reference**
  (small shunt voltages need the 1.1 V ref for usable resolution on 10-bit).
- **ESP32-S3** — **GPIO4** (ADC1), 12-bit, ~3.3 V range.

## 1. Bill of Materials
- Microcontroller: **Arduino Uno/Nano** (A0) or ESP32-S3 (GPIO4)
- Small DC motor (have)
- Current-limited bench/student power supply (have)
- Shunt resistor: **0.1 Ω** works for this motor (currents are <0.5 A, so any wattage is fine).
  A larger 1–2 Ω shunt would give a cleaner signal if you have one.
- Flyback diode: **1N4007** (or any ≥1 A standard diode)
- Breadboard + jumpers

### Reference operating point (this motor)
Supply **4 V**, current limit ~0.7 A, shunt **0.1 Ω**, Arduino Uno (1.1 V ref):
running ≈ 0.12 A (node ~12 mV, ~11 ADC counts), stall ≈ 0.41 A (node ~41 mV, ~38 counts).
Set the firmware `R_SHUNT` to your actual resistor (0.1).

## 2. Wiring (low-side shunt)
```
Supply(+) --+----------------------+
            |                 [1N4007]  (stripe/cathode toward Supply+)
        [ DC Motor ]               |
            |                       |
  node_A ---+-----------------------+
   |        |
   |   [ R_shunt 0.1Ω ]
   |        |
ADC pin reads node_A     (Arduino Uno: A0  |  ESP32-S3: GPIO4)
Board GND ----- Supply(-)        (COMMON GROUND, required)
Board powered by USB from laptop.
```
Connections: Supply(+)→Motor A; Motor B→node_A; node_A→R_shunt→Supply(−);
1N4007 across motor (cathode→Supply+ side); ADC pin (A0 or GPIO4)→node_A; board GND→Supply(−).

## 3. Safety (read before powering)
1. **ESP32-S3** ADC max **3.3 V**, NOT 5 V tolerant — keep node_A < 3.3 V. **Arduino Uno** is
   5 V tolerant, and with the 0.1 Ω shunt node_A is only tens of mV, so no over-voltage risk.
2. Set supply **current limit ≈ 0.7 A** (above the ~0.41 A stall) before powering.
3. With multimeter: stall the motor by hand and confirm node_A stays low (tens of mV here)
   BEFORE wiring it to the ADC pin.
4. Common ground mandatory. Flyback diode mandatory.
5. Motor powered by supply; board by USB — never drive the motor from board pins.

## 4. Boot self-check
Open serial @115200. First line by board (`PIN=14` is A0):
- Uno R4: `# stall_stream R_SHUNT=0.100 ADC_BITS=14 PIN=14 VREF=5.00`
- Uno R3 / Nano: `# stall_stream R_SHUNT=0.100 ADC_BITS=10 PIN=14 VREF=1.10`
- ESP32-S3: `# stall_stream R_SHUNT=0.100 ADC_BITS=12 PIN=4 VREF=3.30`
Confirm `R_SHUNT` matches your installed resistor. If not, edit the `#define` and reflash.
Then confirm the streamed current reads ~0.12 A running and ~0.41 A when you stall by hand.

**Resolution note (Uno + 0.1 Ω):** the running signal is only ~11 ADC counts and stall ~38,
but the sliding-window MEAN over 75 samples averages out the per-sample quantization noise, so
the classes separate cleanly. A larger shunt (1–2 Ω) would widen the per-sample margin if needed.

**ADC reference accuracy:** the Uno INTERNAL ref is ~1.1 V ±10% part-to-part; the ESP32-S3 ~3.3 V
ref reads ~6% high. Either way **classification is unaffected** — the model trains and runs on the
same scale. Only the displayed absolute amps would shift; calibrate `ADC_VREF` against a multimeter
if you need accurate amps.

## 5. Collect data
```bash
source .venv/bin/activate
python -m src.collect --source serial --port /dev/tty.usbmodemXXXX --out data/labeled.csv
```
The guided collector captures all THREE classes, in order:
1. `normal` — let it run steadily (10 s)
2. `stall` — hold the shaft by hand (5 s)
3. `normal` — let it run steadily again (10 s)
4. `startup` — 6 power-on cycles: motor OFF → press Enter → flip it ON immediately (records the inrush)

The startup cycles are essential: without them the model never sees the power-on inrush and
will false-alarm (red) every time the motor starts. The input buffer is flushed between phases
so each segment records fresh data.

## 6. Train + read results
```bash
python -m src.train --data data/labeled.csv --model model/tree.joblib
```
- `classification_report`: stall **recall** should be high.
- Confusion matrix: the cell (true=startup, pred=stall) should be ~0 — this is the
  property that proves you separated inrush from a real stall.
- `plots/tree.txt`: the learned rules (show these to judges — interpretability).

## 7. Real-time test (the demo)
```bash
python -m src.detect --source serial --port /dev/tty.usbmodemXXXX --model model/tree.joblib
```
Verify, in order:
1. Motor running → banner GREEN.
2. Power-cycle the motor a few times → brief orange, **never red** (no false alarm on inrush).
3. Hold the shaft → banner turns **RED within ~0.1 s**.
4. Release → returns to GREEN.
