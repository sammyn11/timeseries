import sys
import requests

BASE_SQL = "http://127.0.0.1:5000"
BASE_MONGO = "http://127.0.0.1:5001"

SAMPLE_RECORD = {
    "timestamp": "2020-01-22 10:00:00",
    "temperature_c": 5.0,
    "humidity": 60.0,
    "wind_speed_kmh": 3.0,
    "demand_mwh": 950.0,
    "is_weekend": 0,
}

RESULTS = []


def check(name, ok, detail=""):
    status = "PASS" if ok else "FAIL"
    RESULTS.append((name, status, detail))
    print(f"[{status}] {name}" + (f" - {detail}" if detail else ""))


def get_json(resp):
    try:
        return resp.json()
    except Exception:
        return None


def test_sql():
    base = BASE_SQL
    print(f"\n=== Testing SQL API at {base} ===")

    # --- GET latest ---
    latest_id = None
    try:
        r = requests.get(f"{base}/api/sql/records/latest", timeout=5)
        data = get_json(r)
        check("SQL GET latest", r.status_code == 200 and data and "demand_id" in data,
              f"HTTP {r.status_code}")
        latest_id = data["demand_id"] if data else None
    except Exception as e:
        check("SQL GET latest", False, f"unreachable: {e}")

    # --- GET all ---
    try:
        r = requests.get(f"{base}/api/sql/records?limit=3", timeout=5)
        data = get_json(r)
        check("SQL GET all", r.status_code == 200 and isinstance(data, list) and len(data) == 3,
              f"HTTP {r.status_code}, rows={len(data) if isinstance(data, list) else 0}")
    except Exception as e:
        check("SQL GET all", False, str(e))

    # --- GET date range ---
    try:
        latest = requests.get(f"{base}/api/sql/records/latest", timeout=5)
        latest_data = get_json(latest)
        date = latest_data["timestamp"][:10] if latest_data else None
        r = requests.get(
            f"{base}/api/sql/records/range",
            params={
                "start": f"{date} 00:00:00" if date else "",
                "end": f"{date} 23:59:59" if date else "",
            },
            timeout=5,
        )
        data = get_json(r)
        check("SQL GET date range", r.status_code == 200 and isinstance(data, list) and len(data) > 0,
              f"HTTP {r.status_code}, rows={len(data) if isinstance(data, list) else 0}")
    except Exception as e:
        check("SQL GET date range", False, str(e))

    # --- GET date range missing params (expect 400) ---
    try:
        r = requests.get(f"{base}/api/sql/records/range", timeout=5)
        check("SQL GET range missing params -> 400", r.status_code == 400, f"HTTP {r.status_code}")
    except Exception as e:
        check("SQL GET range missing params -> 400", False, str(e))

    # --- POST create ---
    created_id = None
    try:
        r = requests.post(f"{base}/api/sql/records", json=SAMPLE_RECORD, timeout=5)
        data = get_json(r)
        ok = r.status_code == 201 and data and data.get("status") == "created"
        check("SQL POST create", ok, f"HTTP {r.status_code}, body={data}")
        created_id = data.get("demand_id") if data else None
    except Exception as e:
        check("SQL POST create", False, str(e))

    # --- PUT update (target the record created by this test) ---
    try:
        if created_id:
            upd = {"demand_mwh": 9999.0, "temperature_c": 10.0, "humidity": 50.0,
                   "wind_speed_kmh": 5.0, "is_weekend": 1}
            r = requests.put(f"{base}/api/sql/records/{created_id}", json=upd, timeout=5)
            data = get_json(r)
            check("SQL PUT update", r.status_code == 200 and data and data.get("status") == "updated",
                  f"HTTP {r.status_code}, body={data}")
        else:
            check("SQL PUT update", False, "no latest id to update")
    except Exception as e:
        check("SQL PUT update", False, str(e))

    # --- DELETE the record created by this test ---
    try:
        if created_id:
            r = requests.delete(f"{base}/api/sql/records/{created_id}", timeout=5)
            data = get_json(r)
            check("SQL DELETE created record", r.status_code == 200 and data and data.get("status") == "deleted",
                  f"HTTP {r.status_code}, body={data}")
        else:
            check("SQL DELETE created record", False, "could not resolve id")
    except Exception as e:
        check("SQL DELETE created record", False, str(e))

    # --- DELETE nonexistent (expect 404) ---
    try:
        r = requests.delete(f"{base}/api/sql/records/999999", timeout=5)
        check("SQL DELETE nonexistent -> 404", r.status_code == 404, f"HTTP {r.status_code}")
    except Exception as e:
        check("SQL DELETE nonexistent -> 404", False, str(e))


def test_mongo():
    base = BASE_MONGO
    print(f"\n=== Testing MongoDB API at {base} ===")

    # Quick reachability
    try:
        r = requests.get(f"{base}/api/mongo/records/latest", timeout=3)
        reachable = r.status_code in (200, 404)  # 404 means server up but empty
    except Exception:
        reachable = False

    if not reachable:
        print("MongoDB API not reachable (is app_mongo.py running on port 5001?). Skipping Mongo tests.")
        for name in ["Mongo GET latest", "Mongo GET all", "Mongo GET date range",
                     "Mongo POST create", "Mongo PUT update", "Mongo DELETE"]:
            check(name, False, "server unreachable")
        return

    # --- GET latest ---
    latest_id = None
    latest_timestamp = None
    try:
        r = requests.get(f"{base}/api/mongo/records/latest", timeout=5)
        data = get_json(r)
        check("Mongo GET latest", r.status_code == 200 and data and "_id" in data,
              f"HTTP {r.status_code}")
        latest_id = data.get("_id") if data else None
        latest_timestamp = data.get("timestamp") if data else None
    except Exception as e:
        check("Mongo GET latest", False, f"unreachable: {e}")

    # --- GET all ---
    try:
        r = requests.get(f"{base}/api/mongo/records?limit=3", timeout=5)
        data = get_json(r)
        check("Mongo GET all", r.status_code == 200 and isinstance(data, list),
              f"HTTP {r.status_code}, rows={len(data) if isinstance(data, list) else 0}")
    except Exception as e:
        check("Mongo GET all", False, str(e))

    # --- GET date range ---
    try:
        date = latest_timestamp[:10] if latest_timestamp else None
        separator = "T" if latest_timestamp and "T" in latest_timestamp else " "
        suffix = "Z" if separator == "T" else ""
        r = requests.get(
            f"{base}/api/mongo/records/range",
            params={
                "start": f"{date}{separator}00:00:00{suffix}" if date else "",
                "end": f"{date}{separator}23:59:59{suffix}" if date else "",
            },
            timeout=5,
        )
        data = get_json(r)
        check("Mongo GET date range", r.status_code == 200 and isinstance(data, list) and len(data) > 0,
              f"HTTP {r.status_code}, rows={len(data) if isinstance(data, list) else 0}")
    except Exception as e:
        check("Mongo GET date range", False, str(e))

    # --- POST create ---
    created_id = None
    try:
        r = requests.post(f"{base}/api/mongo/records", json=SAMPLE_RECORD, timeout=5)
        data = get_json(r)
        ok = r.status_code == 201 and data and "_id" in data
        check("Mongo POST create", ok, f"HTTP {r.status_code}, body={data}")
        created_id = data.get("_id") if data else None
    except Exception as e:
        check("Mongo POST create", False, str(e))

    # --- PUT update ---
    target_id = created_id
    try:
        if target_id:
            upd = {"demand_mwh": 8888.0, "temperature_c": 12.0, "humidity": 55.0,
                   "wind_speed_kmh": 4.0, "is_weekend": 0}
            r = requests.put(f"{base}/api/mongo/records/{target_id}", json=upd, timeout=5)
            data = get_json(r)
            check("Mongo PUT update", r.status_code == 200 and data and data.get("status") == "updated",
                  f"HTTP {r.status_code}, body={data}")
        else:
            check("Mongo PUT update", False, "no id to update")
    except Exception as e:
        check("Mongo PUT update", False, str(e))

    # --- DELETE created record ---
    if created_id:
        try:
            r = requests.delete(f"{base}/api/mongo/records/{created_id}", timeout=5)
            data = get_json(r)
            check("Mongo DELETE created record", r.status_code == 200 and data and data.get("status") == "deleted",
                  f"HTTP {r.status_code}, body={data}")
        except Exception as e:
            check("Mongo DELETE created record", False, str(e))

    # --- DELETE nonexistent (expect 404) ---
    try:
        r = requests.delete(f"{base}/api/mongo/records/000000000000000000000000", timeout=5)
        check("Mongo DELETE nonexistent -> 404", r.status_code == 404, f"HTTP {r.status_code}")
    except Exception as e:
        check("Mongo DELETE nonexistent -> 404", False, str(e))


def print_summary():
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    total = len(RESULTS)
    passed = sum(1 for _, s, _ in RESULTS if s == "PASS")
    for name, status, detail in RESULTS:
        print(f"  {status:4} {name}")
    print(f"\n{passed}/{total} checks passed")
    if passed == total:
        print("All CRUD checks passed!")
    else:
        print("Some checks failed - see details above.")
        sys.exit(1)


if __name__ == "__main__":
    test_sql()
    test_mongo()
    print_summary()
