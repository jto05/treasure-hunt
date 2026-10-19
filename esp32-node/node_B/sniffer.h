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
 *   snifferBegin();                        // in setup(), AFTER Wi-Fi connects
 *   int n;
 *   int rssi = getRssi(phoneMac, &n);      // e.g. -58, or 0 if not heard
 *                                           // n = packets heard since the
 *                                           // last call for this MAC -- the
 *                                           // server uses it to weight how
 *                                           // much to trust this sample
 *                                           // (see RSSI_SMOOTHING_K server-side)
 *
 * NOTES
 *   - RSSI is in dBm and negative; closer to 0 means stronger.
 *   - A phone is only heard while it transmits, so a locked screen or closed
 *     page reads as "not heard".
 *   - RSSI itself is still raw and noisy here (5-10 dB swings) -- smoothing
 *     across reports happens server-side, using the packet count below.
 *   - The callback runs in the Wi-Fi task, so the table is guarded by a lock
 *     and is private to sniffer.cpp. Read it only through getRssi().
 */


// Call once, after ESP32 has joined the network
void snifferBegin();

// Pass a MAC address in to get the RSSI and packet count. Returns rssi=0
// if not heard in the last 5 seconds. *count is packets seen since the
// last call for this MAC (reset to 0 on read), 0 if none/not heard.
int getRssi(const uint8_t mac[6], int *count);
