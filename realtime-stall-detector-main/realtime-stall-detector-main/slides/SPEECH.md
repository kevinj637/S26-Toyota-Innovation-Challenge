# Pitch Speech — Real-Time Motor Stall Detection  (≈ 2:45)

Read top to bottom. `[SLIDE n]` = advance. **bold** = emphasis. *[brackets]* = stage action.
Deck: `slides/pitch.pptx` (same lines are in each slide's speaker notes).

---

**[SLIDE 1 · Title]**
"Unexpected machine downtime costs manufacturers **millions a year**. The earliest warning a motor gives before it fails is its own **current** — so we built a system that reads that current in real time and catches a stall the instant it happens."

**[SLIDE 2 · The trap]**
"Here's what makes this hard. When a motor stalls, current spikes — but current **also** spikes every single time the motor starts: the inrush. A naive 'current-too-high' alarm would cry wolf on every power-on. The real signal isn't *high* current — it's high current that **stays** high. A stall is sustained; a start-up just decays. Telling those two apart is the heart of our project."

**[SLIDE 3 · How it works]**
"Under the hood: we slice the current into short windows, pull out **six features** — level, slope, and whether it's still rising or holding — and feed a small **decision tree**. We chose a tree on purpose: it's **interpretable**, and tiny enough to run on a chip. And the algorithm itself discovered the key rule — that **steadiness** is what separates a real stall from a start-up."

**[SLIDE 4 · Live demo]**  *[switch to the live dashboard / the bench]*
"Let me show you. Running — **green**. Watch when I power-cycle it — *[power-cycle the motor]* — the current spikes, but it stays **green**. No false alarm. Now I actually stall it — *[hold the shaft]* — **RED**, in under a tenth of a second. Release — back to green. Start-up ignored, real stall caught instantly."

**[SLIDE 5 · Results]**
"On our collected data it cleanly separates the three states. Stall is **perfectly classified** — never missed — and a start-up is **never** predicted as a stall. That's the property that matters. The whole pipeline has **eighteen automated tests** and a physics simulator, so we validated it before we ever touched hardware."

**[SLIDE 6 · Edge ML]**
"And it doesn't need a laptop. We compiled that **same** decision tree into C and flashed it onto the Arduino itself. The board runs the inference **on-chip** and lights this LED on a stall. *[point to the board's LED]* Pull the laptop, power it from a charger — it still works. Detection at the edge, on a microcontroller — exactly where a factory sensor lives."

**[SLIDE 7 · Scale]**
"And the method isn't locked to our bench: the **exact same feature code** runs unchanged on Toyota's real eight-DOF arm telemetry, across the whole fleet — and it surfaces the most mechanically-stressed joints, the shoulder and elbow, exactly where the load is. With labeled fault data, the same approach scales to **production predictive maintenance**."

**[SLIDE 8 · Safety, Human, Close]**
"It's human-centered: it catches failures before they cascade — protecting equipment, preventing unplanned line stops, and keeping workers out of harm's way. **From a three-dollar motor to a robot fleet — same physics, same code.** We turn a motor's current into an early-warning system. **Thank you.**"

---

## Timing (~2:45)
| S1 | S2 | S3 | S4 (demo) | S5 | S6 | S7 | S8 |
|----|----|----|-----------|----|----|----|----|
| 0:15 | 0:30 | 0:30 | 0:45 | 0:20 | 0:20 | 0:20 | 0:15 |

## Rubric coverage
Ideation → inrush-vs-stall insight (S2) · Execution → live demo + tests (S4/S5) · Safety → S8 ·
Human Centricity → S8 · Presentation → interpretable tree (S3) + clean visuals throughout.

## If asked (Q&A)
- **"Did you reuse the small-motor model on the arm?"** → No. Only the **feature-extraction code** transfers; each deployment trains its own model. We do **not** claim arm stall detection — that data is unlabeled.
- **"Why a decision tree, not a neural net?"** → Interpretable, fits on a chip, and it's already perfect on the critical class. We can show the exact learned rule.
- **"Different motor / generalization?"** → Recollect a few minutes, retrain in seconds; the features are threshold-free, and we train + infer on the same scale.
- **"Are the Toyota red cells faults?"** → No — highest mechanical-stress windows, **not confirmed faults**. A real jam would look the same and be caught the same way.
- **"How is this different from a current relay?"** → A relay only sees a threshold — it false-alarms on every start-up. We distinguish inrush from stall.
