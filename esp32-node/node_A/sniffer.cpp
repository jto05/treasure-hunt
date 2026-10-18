#include "sniffer.h"
#include "esp_wifi.h"
#include <WiFi.h>

// Each entry in the table is a device being tracked
// saved in memory.
struct Entry {
  uint8_t mac[6]; // each byte in 6 byte MAC is 8-bit integer
  int8_t rssi;    // is same type as pkt->rx-ctrl.rssi
  uint32_t ms;    //
};

static Entry table[16];    // table that holds record of each device
static uint8_t apBssid[6]; // access point bssid gained from WiFi.h

// mux needed to prevent simultaenous reads/writes as
// sniffer runs in seperate thread
static portMUX_TYPE lock = portMUX_INITIALIZER_UNLOCKED;

// Runs this sniffer for every frame the Wi-Fi driver hears.
static void IRAM_ATTR sniffer(void *buf, wifi_promiscuous_pkt_type_t type) {
  if (type != WIFI_PKT_DATA)
    return; // only read data frames
  auto *pkt = (wifi_promiscuous_pkt_t *)buf;

  // only frames that are sent to the Pi
  if (memcmp(pkt->payload + 4, apBssid, 6) != 0)
    return;

  // get the device's mac address
  const uint8_t *sender = pkt->payload + 10;

  // get time
  uint32_t now = millis();

  portENTER_CRITICAL(&lock);

  // iterate through each entry in table
  Entry *slot = &table[0]; // init slot as first entry
  for (auto &e : table) {
    // if the phone is already in the table, use the slot
    if (memcmp(e.mac, sender, 6) == 0) {
      slot = &e;
      break;
    }
    // if unknown, use the slot that is the oldest 
    if (e.ms < slot->ms)
      slot = &e;
  }

  // set slot to packet data
  memcpy(slot->mac, sender, 6);
  slot->rssi = pkt->rx_ctrl.rssi;
  slot->ms = now;

  portEXIT_CRITICAL(&lock);
}

void snifferBegin() {
  // write the Pi's MAC to apBssid
  memcpy(apBssid, WiFi.BSSID(), 6);

  // call sniffer on every frame driver picks up
  esp_wifi_set_promiscuous_rx_cb(&sniffer);

  // start sniffing
  esp_wifi_set_promiscuous(true);
}

int getRssi(const uint8_t mac[6]) {
  int result = 0;
  portENTER_CRITICAL(&lock);
  for (auto &e : table) {
    if (e.ms && memcmp(e.mac, mac, 6) == 0 && millis() - e.ms < 5000)
      result = e.rssi;
  }
  portEXIT_CRITICAL(&lock);
  return result;
}
