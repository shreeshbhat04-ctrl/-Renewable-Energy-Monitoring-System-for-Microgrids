#define BLYNK_TEMPLATE_ID "<Your template id>"
#define BLYNK_TEMPLATE_NAME "microgrids predictor"

#include <ESP8266WiFi.h>
#include <BlynkSimpleEsp8266.h>
#include <DHT.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>
#include <ArduinoJson.h>

// -------- WiFi & Blynk --------
char auth[] = " your auth token";
const char* ssid = "ssid";
const char* pass = "password";

// -------- Pins --------
#define RELAY1_PIN D1
#define RELAY3_PIN D2
#define DHTPIN     D5
#define DHTTYPE    DHT11

DHT dht(DHTPIN, DHTTYPE);
BlynkTimer timer;

// -------- ML Server --------
const char* ML_SERVER = "http://10.249.16.206:8000/predict";

// -------- Flags --------
bool manualRelay1 = false;
bool manualRelay3 = false;
bool stableMode   = true;   // V10 switch: true = stable grid

// ---- Blynk manual relay controls ----
BLYNK_WRITE(V20) {
  manualRelay1 = param.asInt();
  digitalWrite(RELAY1_PIN, manualRelay1 ? LOW : HIGH);
}
BLYNK_WRITE(V21) {
  manualRelay3 = param.asInt();
  digitalWrite(RELAY3_PIN, manualRelay3 ? LOW : HIGH);
}

// ---- Blynk V10: choose stable / unstable PZEM defaults ----
BLYNK_WRITE(V10) {
  stableMode = param.asInt();   // 1 = stable, 0 = unstable
}

// -------- Send Sensor Readings & ML Prediction --------
void sendReadings() {
  // 1️⃣ Live DHT11
  float temp = dht.readTemperature();
  float hum  = dht.readHumidity();
  if (!isnan(temp)) Blynk.virtualWrite(V4, temp);
  if (!isnan(hum))  Blynk.virtualWrite(V6, hum);

  // 2️⃣ PZEM defaults based on V10
  float voltage, current, power;
  if (stableMode) {
    voltage = 230.0;
    current = 0.8;
    power   = 184.0;
  } else {
    // Example “unstable” scenario – tweak as needed
    voltage = 180.0;
    current = 4.5;
    power   = 810.0;
  }

  Blynk.virtualWrite(V1, voltage);
  Blynk.virtualWrite(V2, current);
  Blynk.virtualWrite(V3, power);

  // 3️⃣ Send to ML server if Wi-Fi OK
  if (WiFi.status() == WL_CONNECTED) {
    WiFiClient client;
    HTTPClient http;

    http.begin(client, ML_SERVER);
    http.addHeader("Content-Type", "application/json");

    String payload = "{\"Voltage\":" + String(voltage,1) +
                     ",\"Current\":" + String(current,2) +
                     ",\"Power\":"   + String(power,1) +
                     ",\"Battery_Temperature\":" + String(isnan(temp)?25.0:temp,1) + "}";

    Serial.print("[HTTP] POST payload: ");
    Serial.println(payload);

    int httpCode = http.POST(payload);
    if (httpCode > 0) {
      Serial.printf("[HTTP] Response code: %d\n", httpCode);
      if (httpCode == HTTP_CODE_OK) {
        String response = http.getString();
        Serial.println("[HTTP] Server response: " + response);

        StaticJsonDocument<256> doc;
        if (!deserializeJson(doc, response)) {
          const char* status = doc["predicted_grid_status"];
          float ps = doc["probability_stable"]   | 0.0;
          float pu = doc["probability_unstable"] | 0.0;

          Blynk.virtualWrite(V5, status);
          Blynk.virtualWrite(V6, ps);
          Blynk.virtualWrite(V7, pu);

          if (!manualRelay1) digitalWrite(RELAY1_PIN, strcmp(status,"Stable")==0 ? LOW : HIGH);
          if (!manualRelay3) digitalWrite(RELAY3_PIN, strcmp(status,"Unstable")==0 ? LOW : HIGH);
        }
      }
    } else {
      Serial.printf("[HTTP] POST failed, error: %s\n", http.errorToString(httpCode).c_str());
    }
    http.end();
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(RELAY1_PIN, OUTPUT);
  pinMode(RELAY3_PIN, OUTPUT);
  digitalWrite(RELAY1_PIN, HIGH);
  digitalWrite(RELAY3_PIN, HIGH);

  dht.begin();
  Blynk.begin(auth, ssid, pass);

  timer.setInterval(5000L, sendReadings);
}

void loop() {
  Blynk.run();
  timer.run();
}
