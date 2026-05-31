// firmware_a2/stall_onboard/stall_onboard.ino
// A2 (edge ML) + demo firmware: the decision tree runs ON the microcontroller.
//
// Reads motor current, computes the SAME 6 features as src/features.py over a sliding window,
// runs the exported tree (model.h) on-chip, debounces, and lights the onboard LED on a stall.
// It ALSO streams "t_us,current_a\n" so the web dashboard works at the same time — one flash
// gives BOTH the laptop dashboard (A1) and the standalone on-board LED alarm (A2).
//
// Pull the laptop and the board still lights the LED on a stall: inference is on-chip, no PC.
//
// SETUP: copy the generated model.h into this sketch folder first:
//     python -m src.export_c --model model/tree.joblib --out model/model.h
//     cp model/model.h firmware_a2/stall_onboard/model.h
// model.h class index -> label: 0=normal, 1=stall, 2=startup.
#include <math.h>
#include "model.h"   // int classify(const float f[6])

#define R_SHUNT 0.1f

#if defined(ARDUINO_ARCH_AVR)        // Arduino Uno R3 / Nano (ATmega328)
  #define ADC_PIN  A0
  #define ADC_BITS 10
  #define ADC_VREF 1.1f
#elif defined(ARDUINO_ARCH_RENESAS)  // Arduino Uno R4 (Renesas RA4M1)
  #define ADC_PIN  A0
  #define ADC_BITS 14
  #define ADC_VREF 5.0f
#else                                 // ESP32-S3
  #define ADC_PIN  4
  #define ADC_BITS 12
  #define ADC_VREF 3.3f
#endif

#ifndef LED_BUILTIN
  #define LED_BUILTIN 2
#endif

#define SAMPLE_US   1000   // ~1 kHz (matches the rate the model was trained on)
#define OVERSAMPLE  7      // median despike
#define WIN         75     // window samples (~75 ms @ 1 kHz) — matches training window_s=0.075
#define HOP         25     // hop samples (~25 ms) — matches training hop_s=0.025
#define ENTER_N     3      // consecutive stall windows to raise alarm
#define EXIT_M      5      // consecutive normal windows to clear alarm
#define STALL_CLASS 1      // model.h: 1 = stall

static const int ADC_MAX = (1 << ADC_BITS) - 1;
float buf[WIN];
int head = 0, count = 0, hopc = 0;
int stallStreak = 0, normalStreak = 0;
bool alarm = false;

int readMedian() {
  int v[OVERSAMPLE];
  for (int i = 0; i < OVERSAMPLE; i++) v[i] = analogRead(ADC_PIN);
  for (int i = 1; i < OVERSAMPLE; i++) {
    int k = v[i], j = i - 1;
    while (j >= 0 && v[j] > k) { v[j + 1] = v[j]; j--; }
    v[j + 1] = k;
  }
  return v[OVERSAMPLE / 2];
}

float readCurrent() {
  return (readMedian() * ADC_VREF / ADC_MAX) / R_SHUNT;
}

// Mirror of src/features.compute_features: [mean, std, rms, peak, max_slope, half_diff]
void computeFeatures(float f[6]) {
  float tmp[WIN];
  for (int i = 0; i < WIN; i++) tmp[i] = buf[(head + i) % WIN];  // oldest..newest
  float sum = 0, sumsq = 0, peak = 0, maxslope = 0;
  for (int i = 0; i < WIN; i++) {
    sum += tmp[i]; sumsq += tmp[i] * tmp[i];
    if (tmp[i] > peak) peak = tmp[i];
    if (i > 0) { float s = fabs((tmp[i] - tmp[i - 1]) * 1000.0f); if (s > maxslope) maxslope = s; }
  }
  float mean = sum / WIN;
  float var = sumsq / WIN - mean * mean; if (var < 0) var = 0;
  int half = WIN / 2;
  float h1 = 0, h2 = 0;
  for (int i = 0; i < half; i++) h1 += tmp[i];
  for (int i = half; i < WIN; i++) h2 += tmp[i];
  f[0] = mean;                          // mean
  f[1] = sqrt(var);                     // std
  f[2] = sqrt(sumsq / WIN);             // rms
  f[3] = peak;                          // peak
  f[4] = maxslope;                      // max_slope
  f[5] = h2 / (WIN - half) - h1 / half; // half_diff
}

void setup() {
  Serial.begin(115200);
  pinMode(LED_BUILTIN, OUTPUT);
#if defined(ARDUINO_ARCH_AVR)
  analogReference(INTERNAL);
  for (int i = 0; i < 5; i++) { analogRead(ADC_PIN); delay(2); }
#elif defined(ARDUINO_ARCH_RENESAS)
  analogReadResolution(ADC_BITS);
#else
  analogReadResolution(ADC_BITS);
  analogSetPinAttenuation(ADC_PIN, ADC_11db);
#endif
  delay(200);
  Serial.print("# stall_onboard R_SHUNT="); Serial.print(R_SHUNT, 3);
  Serial.print(" ADC_BITS="); Serial.print(ADC_BITS);
  Serial.print(" WIN="); Serial.print(WIN);
  Serial.println(" (edge ML: tree runs on-chip, LED on stall)");
}

void loop() {
  static unsigned long next = 0;
  unsigned long now = micros();
  if ((long)(now - next) < 0) return;
  next = now + SAMPLE_US;

  float cur = readCurrent();
  Serial.print(now); Serial.print(","); Serial.println(cur, 4);  // stream for the dashboard

  buf[head] = cur;
  head = (head + 1) % WIN;
  if (count < WIN) { count++; return; }

  if (++hopc < HOP) return;
  hopc = 0;

  float f[6];
  computeFeatures(f);
  int cls = classify(f);                  // on-chip inference
  if (cls == STALL_CLASS)       { stallStreak++; normalStreak = 0; }
  else if (cls == 0)            { normalStreak++; stallStreak = 0; }  // normal
  else                          { stallStreak = 0; normalStreak = 0; } // startup

  if (stallStreak >= ENTER_N)               alarm = true;
  else if (alarm && normalStreak >= EXIT_M) alarm = false;
  digitalWrite(LED_BUILTIN, alarm ? HIGH : LOW);
}
