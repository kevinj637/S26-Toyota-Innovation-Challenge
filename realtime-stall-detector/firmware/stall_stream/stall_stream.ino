// firmware/stall_stream/stall_stream.ino
// A1: stream motor current as "t_us,current_a\n".
// Portable across Arduino Uno/Nano (AVR) and ESP32-S3 — the board is detected automatically.
//
//   Arduino Uno/Nano (ATmega328): 10-bit ADC on A0, INTERNAL 1.1V reference.
//     Small shunt voltages (tens of mV) need the 1.1V ref for usable resolution;
//     the default 5V ref would put the whole signal in ~10 ADC counts. 5V tolerant — safe.
//   ESP32-S3: 12-bit ADC on GPIO4 (ADC1), ~3.3V range. Keep the ADC node < 3.3V (NOT 5V tolerant).
//
// SAFETY: low-side shunt + current-limited supply. On ESP32-S3 the ADC node must never exceed
// 3.3V. On AVR with a 0.1 ohm shunt and sub-amp currents the node is only tens of mV, so safe.

#define R_SHUNT   0.1f     // ohms — MUST match the resistor you installed

#if defined(ARDUINO_ARCH_AVR)        // Arduino Uno R3 / Nano (ATmega328)
  #define ADC_PIN  A0
  #define ADC_BITS 10
  #define ADC_VREF 1.1f               // INTERNAL bandgap reference (~1.1V)
#elif defined(ARDUINO_ARCH_RENESAS)  // Arduino Uno R4 Minima / WiFi (Renesas RA4M1)
  #define ADC_PIN  A0
  #define ADC_BITS 14                 // R4 ADC supports up to 14-bit — compensates for the 5V ref
  #define ADC_VREF 5.0f               // default reference = AVCC (5V)
#else                                 // ESP32-S3 (and other 12-bit cores)
  #define ADC_PIN  4                  // GPIO4 = ADC1_CH3
  #define ADC_BITS 12
  #define ADC_VREF 3.3f
#endif

#define SAMPLE_US 1000     // ~1 kHz

static const int ADC_MAX = (1 << ADC_BITS) - 1;

void setup() {
  Serial.begin(115200);
#if defined(ARDUINO_ARCH_AVR)
  analogReference(INTERNAL);          // 1.1V reference on ATmega328 (Uno/Nano)
  for (int i = 0; i < 5; i++) { analogRead(ADC_PIN); delay(2); }  // let the ref settle
#elif defined(ARDUINO_ARCH_RENESAS)
  analogReadResolution(ADC_BITS);     // 14-bit on Uno R4; default 5V reference
#else
  analogReadResolution(ADC_BITS);
  analogSetPinAttenuation(ADC_PIN, ADC_11db);  // ~0-3.3V (newer cores: ADC_ATTEN_DB_12)
#endif
  delay(200);
  Serial.print("# stall_stream R_SHUNT="); Serial.print(R_SHUNT, 3);
  Serial.print(" ADC_BITS="); Serial.print(ADC_BITS);
  Serial.print(" PIN="); Serial.print(ADC_PIN);
  Serial.print(" VREF="); Serial.println(ADC_VREF, 2);
}

void loop() {
  static unsigned long next = 0;
  unsigned long now = micros();
  if ((long)(now - next) >= 0) {
    next = now + SAMPLE_US;
    int raw = analogRead(ADC_PIN);
    float v = (raw * ADC_VREF) / ADC_MAX;
    float current = v / R_SHUNT;
    Serial.print(now); Serial.print(","); Serial.println(current, 4);
  }
}
