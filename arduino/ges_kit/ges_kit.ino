// SunHawk desk thermal kit - Arduino Nano RP2040 Connect (core: Arduino Mbed OS Nano Boards)
//
// Reads:  MLX90640 thermal camera (32x24, I2C 0x33)      -> UDP port 5006, binary, 2 packets per frame
//         INA219 panel voltage/current (I2C 0x40)          -> UDP port 5005, JSON once per second
//         2x DS18B20 panel temperatures (OneWire on D2)
//         reference solar cell on A0 over a 1 ohm shunt (irradiance)
// Serial (115200) prints an I2C scan at boot and all readings every second: use it for the first-day tests.
//
// Wiring (all 3.3 V, powered from a USB powerbank):
//   MLX90640 + INA219: VIN -> 3V3, GND -> GND, SDA -> A4, SCL -> A5 (same I2C bus)
//   INA219: VIN+ -> panel +, VIN- -> load resistor -> panel -; panel - also to GND
//   DS18B20 x2: red -> 3V3, black -> GND, yellow -> D2, 4.7k between D2 and 3V3
//   Reference cell: + -> A0, - -> GND, 1 ohm resistor between A0 and GND
//
// Libraries: WiFiNINA, Adafruit MLX90640, Adafruit INA219, OneWire, DallasTemperature

#include <WiFiNINA.h>
#include <WiFiUdp.h>
#include <Wire.h>
#include <Adafruit_MLX90640.h>
#include <Adafruit_INA219.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include "arduino_secrets.h"   // SECRET_SSID, SECRET_PASS, LAPTOP_IP (copy arduino_secrets.h.example)

const int SENSOR_PORT = 5005;
const int THERMAL_PORT = 5006;
const float CELL_W_PER_V = 1000.0 / 0.10;   // calibrate on day 1: shunt volts at known sun -> W/m²
const int PIXELS = 32 * 24;

WiFiUDP udp;
IPAddress laptop;
Adafruit_MLX90640 mlx;
Adafruit_INA219 ina;
OneWire oneWire(2);
DallasTemperature ds(&oneWire);

bool mlxOk = false, inaOk = false;
float frame[PIXELS];
int16_t packet[2 + PIXELS / 2];   // header (4 bytes) + half a frame as int16 (°C x 100)
uint8_t frameNo = 0;
unsigned long lastSensor = 0;

void i2cScan() {
  Serial.print("I2C devices:");
  for (uint8_t a = 1; a < 127; a++) {
    Wire.beginTransmission(a);
    if (Wire.endTransmission() == 0) { Serial.print(" 0x"); Serial.print(a, HEX); }
  }
  Serial.println("   (expected: 0x33 MLX90640, 0x40 INA219; 0x60/0x6A are on-board chips)");
}

void connectWifi() {
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print("WiFi connecting to "); Serial.println(SECRET_SSID);
    WiFi.begin(SECRET_SSID, SECRET_PASS);
    delay(3000);
  }
  Serial.print("WiFi OK, my IP: "); Serial.println(WiFi.localIP());
}

void setup() {
  Serial.begin(115200);
  unsigned long t0 = millis();
  while (!Serial && millis() - t0 < 3000) {}   // works with or without a USB monitor
  Wire.begin();
  Wire.setClock(400000);
  i2cScan();

  mlxOk = mlx.begin(MLX90640_I2CADDR_DEFAULT, &Wire);
  if (mlxOk) {
    mlx.setMode(MLX90640_CHESS);
    mlx.setResolution(MLX90640_ADC_18BIT);
    mlx.setRefreshRate(MLX90640_4_HZ);   // 4 Hz sub-pages = ~2 full frames per second
  }
  inaOk = ina.begin();
  ds.begin();
  ds.setResolution(10);                  // 0.25 °C, ~190 ms conversion
  ds.setWaitForConversion(false);
  ds.requestTemperatures();
  analogReadResolution(12);
  Serial.print("MLX90640: "); Serial.println(mlxOk ? "OK" : "NOT FOUND");
  Serial.print("INA219:   "); Serial.println(inaOk ? "OK" : "NOT FOUND");
  Serial.print("DS18B20:  "); Serial.print(ds.getDeviceCount()); Serial.println(" found (expected 2)");

  laptop.fromString(LAPTOP_IP);
  connectWifi();
  udp.begin(SENSOR_PORT);
}

void sendThermal() {
  if (!mlxOk || mlx.getFrame(frame) != 0) return;
  for (int part = 0; part < 2; part++) {
    uint8_t *h = (uint8_t *)packet;
    h[0] = 'T'; h[1] = 'H'; h[2] = frameNo; h[3] = part;
    for (int i = 0; i < PIXELS / 2; i++) packet[2 + i] = (int16_t)(frame[part * PIXELS / 2 + i] * 100.0);
    udp.beginPacket(laptop, THERMAL_PORT);
    udp.write((uint8_t *)packet, sizeof(packet));
    udp.endPacket();
  }
  frameNo++;
}

void sendSensors() {
  float volts = analogRead(A0) * 3.3 / 4095.0;
  float irr = volts * CELL_W_PER_V;
  float t1 = ds.getTempCByIndex(0), t2 = ds.getTempCByIndex(1);
  ds.requestTemperatures();               // result is read on the next call, one second later
  float v = inaOk ? ina.getBusVoltage_V() : -1;
  float i = inaOk ? ina.getCurrent_mA() / 1000.0 : -1;
  float tmax = -100;
  for (int k = 0; k < PIXELS; k++) tmax = max(tmax, frame[k]);
  char msg[200];
  snprintf(msg, sizeof(msg),
           "{\"id\":\"ges-arduino-1\",\"irr\":%.0f,\"t_panel\":%.2f,\"t_panel2\":%.2f,\"v\":%.2f,\"i\":%.3f,\"p\":%.2f,\"t_max\":%.1f}",
           irr, t1, t2, v, i, v * i, tmax);
  udp.beginPacket(laptop, SENSOR_PORT);
  udp.write((const uint8_t *)msg, strlen(msg));
  udp.endPacket();
  Serial.println(msg);
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) connectWifi();
  sendThermal();                          // blocks ~0.5 s while the camera fills a frame
  if (millis() - lastSensor >= 1000) {
    lastSensor = millis();
    sendSensors();
  }
}
