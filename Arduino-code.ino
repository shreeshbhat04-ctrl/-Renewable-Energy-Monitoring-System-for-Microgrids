/* --- ESP8266 : lora_fastapi_gateway.ino --- */
#include <SPI.h>
#include <LoRa.h>
#include <ESP8266WiFi.h>
#include <BlynkSimpleEsp8266.h>
#include <ArduinoJson.h>
#include <ESP8266HTTPClient.h>

#define LORA_SS   15   // D8
#define LORA_RST  16   // D0
#define LORA_DIO0  2   // D4

char ssid[] = "YOUR_WIFI";
char pass[] = "YOUR_PASS";
char auth[] = "YOUR_BLYNK_TOKEN";
String fastapiURL = "http://<SERVER_IP>:8000/predict";

void setup() {
  Serial.begin(9600);
  Blynk.begin(auth, ssid, pass);

  LoRa.setPins(LORA_SS, LORA_RST, LORA_DIO0);
  while (!LoRa.begin(433E6)) { delay(500); }
  pinMode(D1, OUTPUT);  // relay if required
}

void loop() {
  Blynk.run();

  int packetSize = LoRa.parsePacket();
  if (packetSize) {
    String line = "";
    while (LoRa.available()) line += (char)LoRa.read();
    line.trim();

    float v,i,p,t;
    sscanf(line.c_str(), "%f,%f,%f,%f", &v,&i,&p,&t);

    // ---- Send to FastAPI ----
    if (WiFi.status() == WL_CONNECTED) {
      HTTPClient http;
      http.begin(fastapiURL);
      http.addHeader("Content-Type", "application/json");

      StaticJsonDocument<200> doc;
      doc["Voltage"] = v;
      doc["Current"] = i;
      doc["Power"]   = p;
      doc["Battery_Temperature"] = t;
      String out;  serializeJson(doc, out);
      int code = http.POST(out);

      if (code == HTTP_CODE_OK) {
        StaticJsonDocument<256> resp;
        if (!deserializeJson(resp, http.getString())) {
          const char* prediction = resp["prediction"];
          Blynk.virtualWrite(V1,v); Blynk.virtualWrite(V2,i);
          Blynk.virtualWrite(V3,p); Blynk.virtualWrite(V4,t);
          Blynk.virtualWrite(V5,prediction);
          digitalWrite(D1, String(prediction)=="Stable");
        }
      }
      http.end();
    }
  }
}
