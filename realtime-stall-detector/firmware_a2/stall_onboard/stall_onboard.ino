// firmware_a2/stall_onboard/stall_onboard.ino
// A2: read current, compute the same 6 features over a sliding window,
// run the exported tree, debounce, drive onboard LED on stall. No laptop.
// Copy model/model.h (from src/export_c.py) into this sketch folder before compiling.
#include "model.h"   // provides: int classify(const float f[6])

#define R_SHUNT   1.0f
#define ADC_PIN   4
#define ADC_BITS  12
#define ADC_VREF  3.3f
#define SAMPLE_US 1000
#define LED_PIN   2          // onboard LED (adjust per board)

#define WIN  75              // samples per window (~75 ms @ 1 kHz)
#define HOP  25
#define ENTER_N 3
#define EXIT_M  5

static const int ADC_MAX = (1 << ADC_BITS) - 1;
float buf[WIN]; int head = 0, count = 0, hopc = 0;
int stallStreak = 0, normalStreak = 0; bool alarm = false;

float readCurrent() {
  int raw = analogRead(ADC_PIN);
  return (raw * ADC_VREF / ADC_MAX) / R_SHUNT;
}

void computeFeatures(float f[6]) {
  // ordered oldest..newest into tmp
  float tmp[WIN];
  for (int i = 0; i < WIN; i++) tmp[i] = buf[(head + i) % WIN];
  float sum = 0, sumsq = 0, peak = 0, maxslope = 0;
  for (int i = 0; i < WIN; i++) {
    sum += tmp[i]; sumsq += tmp[i]*tmp[i];
    if (tmp[i] > peak) peak = tmp[i];
    if (i > 0) { float s = fabs((tmp[i]-tmp[i-1]) * 1000.0f); if (s > maxslope) maxslope = s; }
  }
  float mean = sum / WIN;
  float var = sumsq / WIN - mean*mean; if (var < 0) var = 0;
  float h1 = 0, h2 = 0; int half = WIN/2;
  for (int i = 0; i < half; i++) h1 += tmp[i];
  for (int i = half; i < WIN; i++) h2 += tmp[i];
  f[0] = mean;                 // mean
  f[1] = sqrt(var);            // std
  f[2] = sqrt(sumsq / WIN);    // rms
  f[3] = peak;                 // peak
  f[4] = maxslope;             // max_slope
  f[5] = h2/(WIN-half) - h1/half;  // half_diff
}

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);
  analogReadResolution(ADC_BITS);
  analogSetPinAttenuation(ADC_PIN, ADC_11db);
}

void loop() {
  static unsigned long next = 0;
  unsigned long now = micros();
  if ((long)(now - next) < 0) return;
  next = now + SAMPLE_US;

  buf[head] = readCurrent();
  head = (head + 1) % WIN;
  if (count < WIN) count++;
  if (count < WIN) return;

  if (++hopc < HOP) return;
  hopc = 0;

  float f[6]; computeFeatures(f);
  int cls = classify(f);   // 0=normal,1=stall,2=startup (see model.h)
  if (cls == 1) { stallStreak++; normalStreak = 0; }
  else if (cls == 0) { normalStreak++; stallStreak = 0; }
  else { stallStreak = 0; normalStreak = 0; }   // startup

  if (stallStreak >= ENTER_N) alarm = true;
  else if (alarm && normalStreak >= EXIT_M) alarm = false;

  digitalWrite(LED_PIN, alarm ? HIGH : LOW);
  Serial.print(cls); Serial.print(alarm ? " ALARM\n" : " ok\n");
}
