// DRAFT (not flashed yet): SunHawk ground-station sensor on Arduino Nano RP2040 Connect.
// Reads irradiance (reference solar cell over a shunt on A0) and panel temperature (DS18B20 on D2),
// sends JSON over WiFi (UDP) to the laptop once per second.
// Wiring: ref. cell + -> A0 with 1 ohm shunt to GND (scale CELL_W_PER_V after calibration);
//         DS18B20 data -> D2 with 4.7k pull-up to 3.3V, glued to the back of a module.
#include <WiFiNINA.h>
#include <WiFiUdp.h>
#include <OneWire.h>
#include <DallasTemperature.h>

const char* SSID = "YOUR_WIFI";          // change before flashing
const char* PASS = "YOUR_PASSWORD";
IPAddress LAPTOP(192, 168, 1, 50);       // laptop IP on the site WiFi
const int PORT = 5005;
const float CELL_W_PER_V = 1000.0 / 0.10; // calibration: 0.10 V on shunt = 1000 W/m² (example)

WiFiUDP udp;
OneWire wire(2);
DallasTemperature temp(&wire);

void setup() {
  Serial.begin(115200);
  analogReadResolution(12);
  temp.begin();
  while (WiFi.begin(SSID, PASS) != WL_CONNECTED) { delay(2000); }
  udp.begin(PORT);
}

void loop() {
  float volts = analogRead(A0) * 3.3 / 4095.0;
  float irr = volts * CELL_W_PER_V;
  temp.requestTemperatures();
  float tPanel = temp.getTempCByIndex(0);
  char msg[96];
  snprintf(msg, sizeof(msg), "{\"id\":\"ges-arduino-1\",\"irr\":%.0f,\"t_panel\":%.1f,\"t_amb\":0}", irr, tPanel);
  udp.beginPacket(LAPTOP, PORT);
  udp.write(msg);
  udp.endPacket();
  Serial.println(msg);
  delay(1000);
}
