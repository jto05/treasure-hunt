#pragma once
#include <Arduino.h>

// Reports RSSI for every MAC the Pi asked us to track, then updates
// list from the Pi's reply. Returns true if the Pi answered with
// HTTP 200.
bool sendReport(const char* nodeId);

// for logging
int trackedCount();


