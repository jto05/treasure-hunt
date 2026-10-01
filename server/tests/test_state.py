import time

from hunt.state import GameStore


def make_store(treasure_macs=()):
    return GameStore(treasure_macs=treasure_macs)


# --- register_team / known_macs ---

def test_register_team_returns_token():
    store = make_store()
    token = store.register_team("Red Rockets", "A4:5E:60:12:34:56")
    assert isinstance(token, str) and len(token) > 0


def test_register_team_lowercases_mac():
    store = make_store()
    store.register_team("Red Rockets", "A4:5E:60:12:34:56")
    assert store.known_macs() == {"a4:5e:60:12:34:56"}


def test_register_team_with_no_mac_is_not_in_known_macs():
    store = make_store()
    store.register_team("Red Rockets", None)
    assert store.known_macs() == set()


def test_known_macs_reflects_multiple_teams():
    store = make_store()
    store.register_team("Red", "a4:5e:60:12:34:56")
    store.register_team("Blue", "3c:22:fb:ab:cd:ef")
    assert store.known_macs() == {"a4:5e:60:12:34:56", "3c:22:fb:ab:cd:ef"}


def test_known_macs_empty_when_no_teams_registered():
    store = make_store()
    assert store.known_macs() == set()


# --- record_report / get_readings ---

def test_record_report_stores_reading():
    store = make_store()
    store.record_report("B", {"a4:5e:60:12:34:56": {"rssi": -58, "n": 14}}, now=1000.0)
    assert store.get_readings("B") == {
        "a4:5e:60:12:34:56": {"rssi": -58, "n": 14, "received_at": 1000.0}
    }


def test_record_report_lowercases_mac_keys():
    store = make_store()
    store.record_report("B", {"A4:5E:60:12:34:56": {"rssi": -58, "n": 14}}, now=1000.0)
    assert "a4:5e:60:12:34:56" in store.get_readings("B")


def test_record_report_ignores_treasure_macs():
    store = make_store(treasure_macs=["8c:aa:b5:37:8c:04"])
    store.record_report("B", {
        "8c:aa:b5:37:8c:04": {"rssi": -40, "n": 20},
        "a4:5e:60:12:34:56": {"rssi": -58, "n": 14},
    }, now=1000.0)
    readings = store.get_readings("B")
    assert "8c:aa:b5:37:8c:04" not in readings
    assert "a4:5e:60:12:34:56" in readings


def test_record_report_ignores_treasure_mac_case_insensitively():
    # config.json and the ESP32's JSON body might not agree on case
    store = make_store(treasure_macs=["8C:AA:B5:37:8C:04"])
    store.record_report("B", {"8c:aa:b5:37:8c:04": {"rssi": -40, "n": 20}}, now=1000.0)
    assert store.get_readings("B") == {}


def test_record_report_empty_readings_is_a_no_op():
    # a treasure with nothing to report yet is a valid state, not an error
    store = make_store()
    store.record_report("B", {}, now=1000.0)
    assert store.get_readings("B") == {}


def test_record_report_separates_nodes():
    store = make_store()
    store.record_report("A", {"a4:5e:60:12:34:56": {"rssi": -50, "n": 1}}, now=1000.0)
    store.record_report("B", {"3c:22:fb:ab:cd:ef": {"rssi": -70, "n": 1}}, now=1000.0)
    assert "a4:5e:60:12:34:56" in store.get_readings("A")
    assert "a4:5e:60:12:34:56" not in store.get_readings("B")
    assert "3c:22:fb:ab:cd:ef" in store.get_readings("B")


def test_record_report_overwrites_previous_reading_for_same_mac():
    store = make_store()
    store.record_report("B", {"a4:5e:60:12:34:56": {"rssi": -58, "n": 14}}, now=1000.0)
    store.record_report("B", {"a4:5e:60:12:34:56": {"rssi": -30, "n": 5}}, now=1005.0)
    reading = store.get_readings("B")["a4:5e:60:12:34:56"]
    assert reading == {"rssi": -30, "n": 5, "received_at": 1005.0}


def test_record_report_handles_missing_n():
    store = make_store()
    store.record_report("B", {"a4:5e:60:12:34:56": {"rssi": -58}}, now=1000.0)
    assert store.get_readings("B")["a4:5e:60:12:34:56"]["n"] is None


def test_get_readings_for_unreported_node_is_empty_dict():
    store = make_store()
    assert store.get_readings("C") == {}


def test_record_report_uses_wall_clock_when_now_not_given():
    store = make_store()
    before = time.time()
    store.record_report("B", {"a4:5e:60:12:34:56": {"rssi": -58, "n": 14}})
    after = time.time()
    received_at = store.get_readings("B")["a4:5e:60:12:34:56"]["received_at"]
    assert before <= received_at <= after
