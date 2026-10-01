#include <WiFi.h>
#include "sniffer.h"
#include "report.h"

#ifndef LED_BUILTIN
#define LED_BUILTIN 2
#endif


const char* WIFI_SSID = "TreasureHunt";
const int STATUS_LED = 2;
const char* NODE = "A"; // change to specific node before flashing

void connectWifi() {
  Serial.printf("Connecting to %s", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID);

  while ( WiFi.status() != WL_CONNECTED ) {
    digitalWrite(STATUS_LED, !digitalRead(STATUS_LED)); // blink while attempting connect
    Serial.print(".");
    delay(300);
  }
  Serial.println(); 

  // display solid color when connected
  digitalWrite(STATUS_LED, HIGH); 
  Serial.print("Connected!!!! IP: ");
  Serial.println(WiFi.localIP());
  Serial.print("MAC: ");
  Serial.println(WiFi.macAddress());
  Serial.printf("Channel: %d\n", WiFi.channel());

}

void setup() {
  Serial.begin(115200);
  pinMode(STATUS_LED, OUTPUT);
  connectWifi();
  
  snifferBegin();
}

void loop() {
  // reconnect loop
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFI disconnected, reconnecting...");
    WiFi.reconnect();

    // blink when reconnecting
    while (WiFi.status() != WL_CONNECTED) {
      digitalWrite(STATUS_LED, !digitalRead(STATUS_LED));
      delay(300);
    }

    // display solid when connected
    digitalWrite(STATUS_LED, HIGH);
    Serial.println("Reconnected");
  }

  // report
  static uint32_t last = 0;
  if (millis() - last >= 1000) {
    last = millis();
    bool ok = sendReport(NODE);
    Serial.printf("sent=%s tracking=%d\n", ok ? "ok" : "FAILED", trackedCount());
  }

}
