#include "report.h"
#include "sniffer.h" 
#include <ArduinoJson.h>
#include <HTTPClient.h>
#include <WiFi.h>

static const char *REPORT_URL = "http://10.42.0.1:8080/api/report";
static const int MAX_TRACKED = 16;

// MACs server told to track from last reply
static uint8_t tracked[MAX_TRACKED][6];
static int trackedLen = 0;

int trackedCount() { return trackedLen; }

static bool parseMac(
const char *s, uint8_t out[6]) {
  if (!s)
    return false;
  return sscanf(s, "%hhx:%hhx:%hhx:%hhx:%hhx:%hhx", &out[0], &out[1], &out[2],
                &out[3], &out[4], &out[5]) == 6;
}

bool sendReport(const char *nodeId) {
  // no network , nothign to send
  if (WiFi.status() != WL_CONNECTED)
    return false;

  // build the request body
  JsonDocument req;
  req["node"] = nodeId;
  req["uptime_ms"] = millis();
  JsonObject readings = req["readings"].to<JsonObject>();

  for (int i = 0; i < trackedLen; i++) {
    int rssi = getRssi(tracked[i]);
    if (rssi == 0)
      continue; // nuffin

      char key[18];
      snprintf(key, sizeof(key), "%02x:%02x:%02x:%02x:%02x:%02x", tracked[i][0],
               tracked[i][1], tracked[i][2], tracked[i][3], tracked[i][4],
               tracked[i][5]);
      readings[key]["rssi"] = rssi;
  }  

  String body;
  serializeJson(req, body);

  // POST to the server
  HTTPClient http;
  http.setTimeout(1000); // don't stall loop 
  http.begin(REPORT_URL);
  http.addHeader("Content-Type", "application/json");
  int code = http.POST(body);
  
  if (code == 200) {
    JsonDocument resp;
    if (deserializeJson(resp, http.getString()) == DeserializationError::Ok
        && resp["watch_macs"].is<JsonArray>()) {

      int n = 0;
      for (JsonVariant v : resp["watch_macs"].as<JsonArray>()) {
        if ( n >= MAX_TRACKED )
          break;
        if (parseMac(v.as<const char*>(), tracked[n]))
          n++;
      }
      trackedLen = n;
    }
    // if malformed reply, keep old list
  }
  http.end();
  return code == 200;
}
  

