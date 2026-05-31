# Pitch Script — Real-Time Motor Stall Detection
### Toyota Innovation Challenge · Fault Prediction · ~2.5 min

> **怎么用**：括号里是时间轴和**中文舞台提示**；正文加粗英文就是**照着念的话**。
> 一人讲、一人操作电机。先把仪表盘开着（`python -m web.app --source serial --port <你的端口>`，浏览器 http://localhost:5050），电机接好、电源 5V 开着。

---

## 🎬 The script

**[0:00–0:15 · Hook]**
> **"Unexpected machine downtime costs manufacturers millions every year. The earliest warning a motor gives before it fails is its own current — so we built a system that reads that current in real time and catches a stall the instant it happens."**

**[0:15–0:45 · The insight]** ← 这段是评委「哦，他们真懂」的关键
> **"Here's what makes this hard. When a motor stalls, current spikes. But current also spikes every single time the motor starts — the inrush. A naive 'current-too-high' alarm would cry wolf on every power-on. The real signal isn't *high* current — it's high current that *stays* high. A stall is sustained; a start-up just decays. Telling those two apart is the heart of our project."**

**[0:45–1:30 · LIVE DEMO]** ← 主秀，边做边说
> *（电机正常转）* **"Green — normal operation."**
> *（连续开关电机几次）* **"Watch the current spike when I power-cycle it... the system stays GREEN. It does not false-alarm on start-up."**
> *（用手按住电机轴堵转）* **"Now I actually stall it —"** *（仪表盘变红）* **"RED, in under a tenth of a second."** *（松手）* **"And back to green. Start-up: ignored. Real stall: caught instantly."**

**[1:30–2:00 · How it works + results]**
> **"Under the hood: we slice the current into short windows, pull out six features — level, slope, and whether it's still rising or holding — and feed a decision tree. We chose a tree on purpose: it's interpretable — here are the exact rules it learned — and it's tiny. On our collected data it cleanly separates the three states and never confuses a start-up for a stall. The whole pipeline ships with 18 automated tests and a physics simulator, so we validated it before touching hardware."**

**[2:00–2:20 · Edge ML / A2]**
> **"And it doesn't need a laptop. We compiled that same decision tree into C and flashed it onto the Arduino itself —"** *（指 LED）* **"the board runs inference on-chip and lights this LED on a stall. No PC, no cloud — detection at the edge."**

**[2:20–2:40 · Scale + Safety + Human]**
> **"And the method isn't locked to our bench — the exact same feature code runs unchanged on Toyota's real 8-DOF arm telemetry, across their whole fleet."** *（亮 fleet 热图，一句带过）* **"With labeled fault data, the same approach scales to production predictive maintenance. And it's human-centered: it catches failures before they cascade — protecting equipment, preventing unplanned line stops, and keeping workers out of harm's way."**

> 注：Toyota 只作「方法可扩展」一句脚注，**不要**说成"在臂上检测到了堵转"（那批数据无标签、无真故障）。主角始终是台架的现场实时检测 + LED。

**[2:40–2:50 · Close]**
> **"From a three-dollar motor to a Toyota production arm — same physics, same code. We turn a motor's current into an early-warning system. Thank you."**

---

## 🎯 Rubric mapping (评委按这 5 项打分，逐项都点到了)

| Rubric | 脚本里哪句命中 |
|---|---|
| **Ideation** | inrush-vs-stall 洞察；电流=最早故障信号；Toyota 迁移=影响力 |
| **Execution** | 现场实时 Demo（开机不误报 + 按住秒红）；18 测试；仿真验证 |
| **Safety** | 提前发现堵转防设备烧毁/连锁故障；台架低压限流 |
| **Human Centricity** | 减少停线、让工人远离危险、预测性维护 |
| **Presentation** | 决策树可解释（展示学到的规则）；物理→ML→边缘→产线 层层递进 |

---

## 🎥 Demo 编排清单（操作的人照这个走）
1. 开场前：仪表盘已开、电机正常转、状态条绿
2. Hook + 洞察讲完 → 进 Demo
3. **开关电机 2–3 次** → 指着曲线尖峰说「stays green」（证明不误报）
4. **手按住轴堵转** → 等状态条变红（~0.1s）→ 说「RED」
5. **松手** → 回绿
6. 讲 how/results 时，可点开 `plots/tree.txt`（决策树规则）和混淆矩阵
7. 讲 A2 时指板上 LED；讲 Scale 时亮 `toyota_transfer/plots/`

## 🛟 兜底
- 硬件抽风：`python -m web.app --source sim` 用仿真器照样演（绿/橙/红俱全）
- 板子没接：跳过 LED，口头说「on-chip C inference, here's the generated model.h」

## 🙋 评委可能问 + 答
- **「为什么不用神经网络/更复杂模型？」** → 信号签名干净、要可解释、要能上单片机；决策树同时满足，准确率已足够，且能画出规则。
- **「没有故障标签怎么办（真实产线）？」** → 台架我们自采带标；产线先用无监督异常检测（我们已在 Toyota 数据上演示「高电流+不动=卡死」判据），有标签后即变监督式。
- **「噪声/不同电机怎么泛化？」** → 特征是阈值无关的（slope/half_diff），且训练与推理同尺度；换电机只需重采几分钟、秒级重训。
- **「这和现成的电流继电器有何不同？」** → 继电器只看阈值，会在每次开机误报；我们区分浪涌 vs 堵转，这是它做不到的。
