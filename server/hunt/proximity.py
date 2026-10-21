import time

# NOTE: numbers to be recalibrated when testing with hardware
RSSI_AT_1M = -30 # threshold to bieing close to a node
STALE_AFTER_S = 15 # after this amount of time, singal reported as lost
PATH_LOSS_EXPONENT = 2 # apparently this varies depending if you are in or outdoors

def rssi_to_meters(rssi):
    return 10 ** ((RSSI_AT_1M - rssi) / (10 * PATH_LOSS_EXPONENT)) # got this formula from google :D

def describe(reading, now = None):
    # reading is {"rssi", "n", "received_at"} from state.py, or None"""
    if now is None:
        now = time.time()

    if reading is None or now - reading["received_at"] > STALE_AFTER_S:
        return {"status": "no_signal"}

    rssi = reading["rssi"]
    if rssi > -30:
        level = "at node"
    elif rssi > -45:
        level = "hot"
    elif rssi > -60:
        level = "warm"
    elif rssi > -75:
        level = "cool"
    else:
        level = "cold"

    return {
        "status": "ok",
        "level": level,
        "meters": round(rssi_to_meters(rssi)),
        "rssi": round(rssi),   # remove this later
    }