# 实时电机堵转检测系统 — 设计文档

- 日期: 2026-05-29
- 项目: Toyota Innovation Challenge (S26) — Fault Prediction 赛题 / 方案 A
- 状态: 设计已确认，待用户最终审阅 spec

---

## 1. 背景与目标

Toyota Innovation Challenge 的 Fault Prediction 赛题要求「用智能系统减少非计划停机」。官方只圈定建议空间，具体目标与技术路线由各队自定。本项目把它落地为：

> **一套实时电机堵转检测系统**：连续采集电机电流 → 滑窗特征 → 决策树分类 `normal / startup / stall` → 去抖状态机 → 仪表盘绿/红报警。核心技术亮点是**区分「启动浪涌」与「真堵转」**（二者瞬时电流都高，单一阈值会在每次开机误报）。

物理依据：直流电机 `电流 = (电压 − 反电动势) / 绕组电阻`，反电动势 ∝ 转速。堵转时转速→0、反电动势→0、电流冲到最大且**持续**；启动时同样高但**短暂**回落。区分二者是本项目的灵魂。

## 2. 锁定的设计决策

| 维度 | 决策 |
|---|---|
| 检测核心 | 决策树（三分类）；阈值规则作基线对照 |
| 数据来源 | ③ 自采电机堵转数据为主；① Toyota 8-DOF 遥测作「方法可迁移」补充论证 |
| 目标板 | **开发/验证板：ESP32-S3**（Andrew 自有；12-bit ADC，**0–3.3V 上限、非 5V 容忍**，故选较大分流电阻 ~1Ω + 电源限流）。现场板待定（可能 Uno/PRIZM），固件保持可移植（`#define` 切 10/12-bit） |
| 交付形态 | 全栈 + 物理仿真器；**A1（笔记本端推理）→ A2（板上边缘推理）两阶段** |
| 仪表盘 | 先求稳（matplotlib 实时图 + 绿/红状态）；花哨版后置 |
| 代码仓库 | 独立 git repo（`realtime-stall-detector`），不混入官方 Toyota 仓库 |

## 3. 非目标（YAGNI）

- 不做轴承磨损/欠压等其它故障类型（仅 `normal/startup/stall` 三类）
- 不做 Web/前端花哨仪表盘（先 matplotlib）
- 不做云端/数据库/多机协同
- 不在 A1 阶段做边缘部署（留给 A2）

## 4. 核心设计决策：数据源抽象

把「数据从哪来」抽象成统一接口 `DataSource`，产出 `(t_seconds, current_amps)` 样本流。两个实现：

- `SimulatedSource`：物理仿真器（**现在**用，无硬件验证）
- `SerialSource`：读 Arduino 串口（**真实硬件**用）

下游所有模块只依赖该接口，不关心数据真假。**这是「现在验证 = 现场上线、同一套代码」的关键**——切换只改 `--source sim|serial`。

## 5. 整体架构与数据流

```
 数据源(Sim / Serial) ─▶ 滑窗特征 ─▶ 决策树 ─▶ 去抖状态机 ─▶ 仪表盘(绿/红 + 报警)
                              ▲
   训练(离线)：标注数据 ─▶ 特征 ─▶ 决策树 + 阈值基线 ─▶ 存模型 + 画树
```

- **实时路径**：源 → 滑窗 → 特征 → `model.predict` → 状态机(去抖) → 仪表盘
- **训练路径**：标注 CSV → 滑窗 → 特征 → 训练树 → 评估(混淆矩阵) → 存模型
- **A2 路径**：源(板上 ADC) → 板上增量特征 → 生成的 `classify()` → LED 报警（脱离电脑）

## 6. 模块 / 文件清单

仓库结构（`realtime-stall-detector/`）：

| 文件 | 职责 | 依赖 |
|---|---|---|
| `src/sources.py` | `DataSource` 接口 + `SimulatedSource` / `SerialSource` | simulator, pyserial |
| `src/simulator.py` | 物理仿真器：按场景生成 空转/启动浪涌/运行/堵转平台 + 噪声 | numpy |
| `src/features.py` | 纯函数：滑窗 → 特征向量（训练/实时/A2 共用，唯一真相源） | numpy |
| `src/collect.py` | 跑数据源 + 键盘打标 → 标注 CSV | sources, features |
| `src/train.py` | 训练决策树 + 阈值基线；评估；存模型 + 画树 | features, sklearn |
| `src/detect.py` | 实时：源→特征→树→去抖状态机→仪表盘报警（A1 主体） | sources, features, sklearn, matplotlib |
| `src/export_c.py` | A2：决策树 → 可移植 C (`if/else`) `model.h` | sklearn |
| `firmware/stall_stream.ino` | A1 固件：连续流式送电流，Uno 默认 + ESP32 `#define`，修好三个坑 | — |
| `firmware_a2/stall_onboard.ino` | A2 固件：板上增量特征 + `classify()` → LED 报警 | 生成的 model.h |
| `tests/test_pipeline.py` | 仿真数据上端到端验证（特征+训练+检测），「现在就完成」的证据 | 全部 src |
| `HARDWARE.md` | **硬件操作指南**：ESP32-S3 接线、串口自检读数、采数据步骤、测量分析、实时报警测试（开机不误报+按住秒报警） | — |
| `README.md` / `requirements.txt` | 运行说明 + 依赖 | — |

设计原则：每个模块单一职责、接口清晰、可独立测试。`features.py` 是特征定义的唯一真相源，训练、实时、A2 三处共用同一套定义，避免漂移。

## 7. 特征集

滑窗（~50–100 ms），增量计算以便移植到 Uno：

- 均值电流
- 标准差
- 最大斜率 / 一阶差分（抓「升得多快」）
- **持续高于基线的时长**（区分浪涌 vs 堵转的命门特征）
- RMS / 峰值

分类标签：`normal`（运行）、`startup`（启动浪涌瞬态）、`stall`（堵转）。模型应学到：高+持续→stall；高+短暂→startup；低→normal。

## 8. 检测状态机（去抖）

```
NORMAL(绿) ──连续 N 窗判 stall──▶ STALL(红, 报警)
STALL(红)  ──连续 M 窗判 normal──▶ NORMAL(绿)
（startup 瞬态归入 WARNING(黄)，不触发报警）
```

`N`、`M` 取 2–3，杀掉单窗毛刺误报。报警 = 仪表盘变红（A1）/ 点亮 LED（A2）。

## 9. 固件设计与三个坑修复

starter 的 `motorStallTestSetup.ino` 有三处问题，本项目固件全部修正：

1. **分流电阻**：`R_SHUNT` 改为实际装的值（电路图标 0.1Ω）；开机串口打印自检配置
2. **ADC 位数**：Uno 默认 10-bit (`ADC_MAX=1023`，去掉 `analogReadResolution(12)`)；ESP32 经 `#define USE_12BIT` 切 12-bit
3. **批间盲区**：改「采 500 点→停下来传」为**连续流式输出**，消除每批 ~477ms 的采样盲区（实时报警必需）

**ESP32-S3 ADC 约束（开发板专属）**：ADC 输入 0–3.3V、非 5V 容忍，超压烧芯片。低边采样 + R=1Ω + 电源限流 ~1.5A 保证节点电压 ≤ ~1.5V。用 ADC1（GPIO1–10，避开 WiFi 占用的 ADC2），12-bit、12dB 衰减。固件开机打印 R_shunt/ADC 配置自检。接线与安全细节见 `HARDWARE.md`。

## 10. 两阶段交付边界

- **A1（先做，保底）**：sources + simulator + features + collect + train + detect(仪表盘) + `stall_stream.ino` + tests。现在就在仿真器上跑通验证；你用自己设备烧固件采真实数据二次验证。
- **A2（后做，加分）**：`export_c.py` + `stall_onboard.ino`，**复用 A1 训好的同一棵树**，把推理搬上板，脱离电脑亮 LED。A1 稳了再做。

## 11. 验证策略

- **仿真验证（现在，headless）**：`tests/test_pipeline.py` 造一段 `空转→启动→运行→堵转→运行→停` → 训练树 → 断言留出集上**堵转召回高、启动误报≈0** → detect 逻辑跑新仿真，断言**堵转变红、启动保持绿**。产出混淆矩阵 + 仪表盘截图。
- **硬件验证（用户自有设备，赛前）**：烧 `stall_stream.ino`，自采正常/堵转数据，`--source serial` 实测实时报警。
- **A2 验证**：生成的 C 先语法编译检查；最终烧板验证需硬件。

## 12. 现在可交付 vs 需要硬件

| 现在就能做并验证（无硬件） | 需要硬件 |
|---|---|
| 仿真器、特征、训练、检测逻辑、仪表盘、测试、混淆矩阵、生成 C 的语法检查 | 烧录固件、采真实电机数据、现场实时 Demo、A2 的 LED |

## 13. Rubric 对应

| Rubric | 覆盖方式 |
|---|---|
| Ideation | 抓电流-堵转物理本质 + 点破 inrush 陷阱 |
| Execution | 实时报警、可复现、对比演示（开机不误报 vs 按住秒报警） |
| Safety | 堵转及时报警，防电机烧毁/设备损坏 |
| Human Centricity | 替工人盯设备、提前预警避免停线 |
| Presentation | 决策树可解释（画规则）+ 物理/ML 双层叙事 |

## 14. 风险与缓解

- 硬件搭建/标定耗时 → 仿真器先行，你自有设备可提前演练
- 数据漂移（不同电机/负载） → 现场快速重采 + 重训（决策树训练秒级）
- 现场硬件故障 → 仿真器作 Demo 兜底
- Uno 资源限制（A2） → 决策树导出为紧凑 `if/else`，增量特征不存整窗
