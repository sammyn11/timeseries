"""
Task 3: CRUD + Time-Series API for SQL (Person D role)
Runs on port 5000. Uses SQLite so it runs without a MySQL server;
swap the connection string to MySQL when deploying.
Endpoints:
  POST   /api/sql/records
  GET    /api/sql/records
  GET    /api/sql/records/latest
  GET    /api/sql/records/range?start=...&end=...
  PUT    /api/sql/records/<id>
  DELETE /api/sql/records/<id>
"""
import sqlite3
from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "database", "energy.db")
DB_PATH = os.path.abspath(DB_PATH)


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.executescript("""
        DROP TABLE IF EXISTS energy_demand;
        DROP TABLE IF EXISTS weather;
        DROP TABLE IF EXISTS locations;

        CREATE TABLE locations (
            location_id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT NOT NULL,
            country TEXT NOT NULL,
            region TEXT,
            latitude REAL,
            longitude REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE weather (
            weather_id INTEGER PRIMARY KEY AUTOINCREMENT,
            location_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            temperature_c REAL,
            humidity REAL,
            wind_speed_kmh REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (location_id) REFERENCES locations(location_id),
            UNIQUE (location_id, timestamp)
        );
        CREATE TABLE energy_demand (
            demand_id INTEGER PRIMARY KEY AUTOINCREMENT,
            location_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            demand_mwh REAL NOT NULL,
            is_weekend INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (location_id) REFERENCES locations(location_id),
            UNIQUE (location_id, timestamp)
        );
    """)
    cur.execute("INSERT INTO locations (city,country,region,latitude,longitude) VALUES (?,?,?,?,?)",
                ("Sample City", "Sample Country", "Central", 40.7128, -74.0060))
    conn.commit()
    conn.close()


# Initialize DB on startup
init_db()

# Seed with CSV data if present
CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "energy_weather_4years.csv")
CSV_PATH = os.path.abspath(CSV_PATH)
if os.path.exists(CSV_PATH):
    import pandas as pd
    df = pd.read_csv(CSV_PATH)
    # Insert a sample subset (first 500 rows) to keep it light
    sample = df.head(500)
    conn = get_conn()
    loc_id = 1
    for _, r in sample.iterrows():
        conn.execute("INSERT OR IGNORE INTO weather (location_id,timestamp,temperature_c,humidity,wind_speed_kmh) VALUES (?,?,?,?,?)",
                     (loc_id, str(r["timestamp"]), r["temperature_c"], r["humidity"], r["wind_speed_kmh"]))
        conn.execute("INSERT OR IGNORE INTO energy_demand (location_id,timestamp,demand_mwh,is_weekend) VALUES (?,?,?,?)",
                     (loc_id, str(r["timestamp"]), r["energy_demand_mwh"], int(r["is_weekend"])))
    conn.commit()
    conn.close()
    print("Seeded SQL DB with", len(sample), "rows.")


# ------------------------------------------------------------
# CRUD: Create
# ------------------------------------------------------------
@app.route("/api/sql/records", methods=["POST"])
def create_record():
    data = request.get_json(force=True)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO locations (city,country) VALUES (?,?)",
                (data.get("city", "Unknown"), data.get("country", "Unknown")))
    loc_id = cur.lastrowid
    cur.execute("INSERT INTO weather (location_id,timestamp,temperature_c,humidity,wind_speed_kmh) VALUES (?,?,?,?,?)",
                (loc_id, data["timestamp"], data["temperature_c"], data["humidity"], data["wind_speed_kmh"]))
    cur.execute("INSERT INTO energy_demand (location_id,timestamp,demand_mwh,is_weekend) VALUES (?,?,?,?)",
                (loc_id, data["timestamp"], data["demand_mwh"], data.get("is_weekend", 0)))
    conn.commit()
    conn.close()
    return jsonify({"status": "created", "location_id": loc_id}), 201


# ------------------------------------------------------------
# CRUD: Read (all, with optional limit)
# ------------------------------------------------------------
@app.route("/api/sql/records", methods=["GET"])
def get_records():
    limit = request.args.get("limit", default=50, type=int)
    conn = get_conn()
    rows = conn.execute("""
        SELECT e.demand_id, e.location_id, e.timestamp, e.demand_mwh, e.is_weekend,
               w.temperature_c, w.humidity, w.wind_speed_kmh
        FROM energy_demand e
        JOIN weather w ON w.location_id=e.location_id AND w.timestamp=e.timestamp
        ORDER BY e.timestamp DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


# ------------------------------------------------------------
# Time-series: Latest record
# ------------------------------------------------------------
@app.route("/api/sql/records/latest", methods=["GET"])
def get_latest():
    conn = get_conn()
    row = conn.execute("""
        SELECT e.demand_id, e.location_id, e.timestamp, e.demand_mwh, e.is_weekend,
               w.temperature_c, w.humidity, w.wind_speed_kmh
        FROM energy_demand e
        JOIN weather w ON w.location_id=e.location_id AND w.timestamp=e.timestamp
        ORDER BY e.timestamp DESC
        LIMIT 1
    """).fetchone()
    conn.close()
    if row is None:
        return jsonify({"error": "no records"}), 404
    return jsonify(dict(row))


# ------------------------------------------------------------
# Time-series: Records by date range
# ------------------------------------------------------------
@app.route("/api/sql/records/range", methods=["GET"])
def get_range():
    start = request.args.get("start")
    end = request.args.get("end")
    if not start or not end:
        return jsonify({"error": "provide start and end"}), 400
    conn = get_conn()
    rows = conn.execute("""
        SELECT e.demand_id, e.location_id, e.timestamp, e.demand_mwh, e.is_weekend,
               w.temperature_c, w.humidity, w.wind_speed_kmh
        FROM energy_demand e
        JOIN weather w ON w.location_id=e.location_id AND w.timestamp=e.timestamp
        WHERE e.timestamp BETWEEN ? AND ?
        ORDER BY e.timestamp
    """, (start, end)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


# ------------------------------------------------------------
# CRUD: Update
# ------------------------------------------------------------
@app.route("/api/sql/records/<int:demand_id>", methods=["PUT"])
def update_record(demand_id):
    data = request.get_json(force=True)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE energy_demand SET demand_mwh=?, is_weekend=? WHERE demand_id=?",
                (data["demand_mwh"], data.get("is_weekend", 0), demand_id))
    if cur.rowcount == 0:
        conn.close()
        return jsonify({"error": "record not found"}), 404
    cur.execute("UPDATE weather SET temperature_c=?, humidity=?, wind_speed_kmh=? WHERE weather_id=(SELECT weather_id FROM weather WHERE timestamp=(SELECT timestamp FROM energy_demand WHERE demand_id=?))",
                (data["temperature_c"], data["humidity"], data["wind_speed_kmh"], demand_id))
    conn.commit()
    conn.close()
    return jsonify({"status": "updated", "demand_id": demand_id})


# ------------------------------------------------------------
# CRUD: Delete
# ------------------------------------------------------------
@app.route("/api/sql/records/<int:demand_id>", methods=["DELETE"])
def delete_record(demand_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM energy_demand WHERE demand_id=?", (demand_id,))
    if cur.rowcount == 0:
        conn.close()
        return jsonify({"error": "record not found"}), 404
    conn.commit()
    conn.close()
    return jsonify({"status": "deleted", "demand_id": demand_id})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)