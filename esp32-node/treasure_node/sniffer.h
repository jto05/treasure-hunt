#pragma once
#include <Arduino.h>

/*
 * sniffer.h - passive per-phone signal strength (RSSI) lookup
 *
 * HOW IT WORKS
 *   After the ESP32 joins the game's Wi-Fi network, snifferBegin() turns on
 *   promiscuous mode. The Wi-Fi driver then calls a callback for every frame
 *   the radio overhears. The callback keeps only data frames sent to the Pi's
 *   access point, and stores each sender's (the phone's) latest RSSI and
 *   timestamp in a 16-entry table, replacing the oldest entry when full.
 *   getRssi() looks a MAC up in that table.
 *
 * USAGE
 *   snifferBegin();                  // in setup(), AFTER Wi-Fi connects
 *   int rssi = getRssi(phoneMac);    // e.g. -58, or 0 if not heard
 *
 * NOTES
 *   - RSSI is in dBm and negative; closer to 0 means stronger.
 *   - A phone is only heard while it transmits, so a locked screen or closed
 *     page reads as "not heard".
 *   - Readings are raw and noisy (5-10 dB swings); smooth before use.
 *   - The callback runs in the Wi-Fi task, so the table is guarded by a lock
 *     and is private to sniffer.cpp. Read it only through getRssi().
 */


// Call once, after ESP32 has joined the network
void snifferBegin();

// Pass a MAC address in to get the RSSI. Returns 0 if 
// not heard in the last 5 seconds
int getRssi(const uint8_t mac[6]);
