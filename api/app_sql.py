"""
Task 3: CRUD + Time-Series API for MySQL (Person D role)
Runs on port 5000. Configure MYSQL_* values in the project-root .env file.
Endpoints:
  POST   /api/sql/records
  GET    /api/sql/records
  GET    /api/sql/records/latest
  GET    /api/sql/records/range?start=...&end=...
  PUT    /api/sql/records/<id>
  DELETE /api/sql/records/<id>
"""

import os
from datetime import datetime
from zoneinfo import ZoneInfo

import mysql.connector
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS

if __package__:
    from .seed_data import load_seed_records
else:
    from seed_data import load_seed_records

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DATABASE", "energy_db"),
}

app = Flask(__name__)
CORS(app)


@app.route("/")
def index():
    return jsonify({
        "service": "Energy Demand SQL API",
        "records": "/api/sql/records",
    })


@app.route("/favicon.ico")
def favicon():
    return "", 204


def get_conn():
    return mysql.connector.connect(**MYSQL_CONFIG)


def normalize_timestamp(value):
    timestamp = datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
    if timestamp.tzinfo is not None:
        timestamp = timestamp.astimezone(ZoneInfo("Europe/Madrid")).replace(tzinfo=None)
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")


def serialize_record(row):
    record = dict(row)
    if isinstance(record.get("timestamp"), datetime):
        record["timestamp"] = record["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
    return record


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS locations (
            location_id INT PRIMARY KEY AUTO_INCREMENT,
            city VARCHAR(100) NOT NULL,
            country VARCHAR(100) NOT NULL,
            region VARCHAR(100),
            latitude REAL,
            longitude REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS weather (
            weather_id INT PRIMARY KEY AUTO_INCREMENT,
            location_id INT NOT NULL,
            timestamp DATETIME NOT NULL,
            temperature_c REAL,
            humidity REAL,
            wind_speed_kmh REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (location_id) REFERENCES locations(location_id),
            UNIQUE KEY uq_weather_location_timestamp (location_id, timestamp),
            KEY idx_weather_ts (timestamp)
        ) ENGINE=InnoDB
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS energy_demand (
            demand_id INT PRIMARY KEY AUTO_INCREMENT,
            location_id INT NOT NULL,
            timestamp DATETIME NOT NULL,
            demand_mwh REAL NOT NULL,
            is_weekend INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (location_id) REFERENCES locations(location_id),
            UNIQUE KEY uq_demand_location_timestamp (location_id, timestamp),
            KEY idx_demand_ts (timestamp)
        ) ENGINE=InnoDB
    """)
    cur.execute("SELECT location_id FROM locations ORDER BY location_id LIMIT 1")
    if cur.fetchone() is None:
        cur.execute(
            "INSERT INTO locations (city,country,region,latitude,longitude) VALUES (%s,%s,%s,%s,%s)",
            ("Valencia", "Spain", "Valencian Community", 39.4699, -0.3763),
        )
    conn.commit()
    cur.close()
    conn.close()


# Initialize DB on startup
init_db()

conn = get_conn()
cur = conn.cursor()
cur.execute("SELECT location_id FROM locations ORDER BY location_id LIMIT 1")
loc_id = cur.fetchone()[0]
seed_records = load_seed_records()
cur.executemany(
    "INSERT IGNORE INTO weather (location_id,timestamp,temperature_c,humidity,wind_speed_kmh) VALUES (%s,%s,%s,%s,%s)",
    [(loc_id, normalize_timestamp(row["timestamp"]), row["temperature_c"], row["humidity"], row["wind_speed_kmh"])
     for row in seed_records],
)
cur.executemany(
    "INSERT IGNORE INTO energy_demand (location_id,timestamp,demand_mwh,is_weekend) VALUES (%s,%s,%s,%s)",
    [(loc_id, normalize_timestamp(row["timestamp"]), row["demand_mwh"], row["is_weekend"])
     for row in seed_records],
)
conn.commit()
cur.close()
conn.close()
print("Seeded SQL DB with", len(seed_records), "available records.")


# ------------------------------------------------------------
# CRUD: Create
# ------------------------------------------------------------
@app.route("/api/sql/records", methods=["POST"])
def create_record():
    data = request.get_json(force=True)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO locations (city,country) VALUES (%s,%s)",
                (data.get("city", "Unknown"), data.get("country", "Unknown")))
    loc_id = cur.lastrowid
    timestamp = normalize_timestamp(data["timestamp"])
    cur.execute("INSERT INTO weather (location_id,timestamp,temperature_c,humidity,wind_speed_kmh) VALUES (%s,%s,%s,%s,%s)",
                (loc_id, timestamp, data["temperature_c"], data["humidity"], data["wind_speed_kmh"]))
    cur.execute("INSERT INTO energy_demand (location_id,timestamp,demand_mwh,is_weekend) VALUES (%s,%s,%s,%s)",
                (loc_id, timestamp, data["demand_mwh"], data.get("is_weekend", 0)))
    demand_id = cur.lastrowid
    conn.commit()
    conn.close()
    return jsonify({"status": "created", "location_id": loc_id, "demand_id": demand_id}), 201


# ------------------------------------------------------------
# CRUD: Read (all, with optional limit)
# ------------------------------------------------------------
@app.route("/api/sql/records", methods=["GET"])
def get_records():
    limit = request.args.get("limit", default=50, type=int)
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT e.demand_id, e.location_id, e.timestamp, e.demand_mwh, e.is_weekend,
               w.temperature_c, w.humidity, w.wind_speed_kmh
        FROM energy_demand e
        JOIN weather w ON w.location_id=e.location_id AND w.timestamp=e.timestamp
        ORDER BY e.timestamp DESC
        LIMIT %s
    """, (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([serialize_record(row) for row in rows])


# ------------------------------------------------------------
# Time-series: Latest record
# ------------------------------------------------------------
@app.route("/api/sql/records/latest", methods=["GET"])
def get_latest():
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT e.demand_id, e.location_id, e.timestamp, e.demand_mwh, e.is_weekend,
               w.temperature_c, w.humidity, w.wind_speed_kmh
        FROM energy_demand e
        JOIN weather w ON w.location_id=e.location_id AND w.timestamp=e.timestamp
        ORDER BY e.timestamp DESC
        LIMIT 1
    """)
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row is None:
        return jsonify({"error": "no records"}), 404
    return jsonify(serialize_record(row))


# ------------------------------------------------------------
# Time-series: Records by date range
# ------------------------------------------------------------
@app.route("/api/sql/records/range", methods=["GET"])
def get_range():
    start = request.args.get("start")
    end = request.args.get("end")
    if not start or not end:
        return jsonify({"error": "provide start and end"}), 400
    try:
        start = normalize_timestamp(start)
        end = normalize_timestamp(end)
    except ValueError:
        return jsonify({"error": "timestamps must be ISO 8601"}), 400
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT e.demand_id, e.location_id, e.timestamp, e.demand_mwh, e.is_weekend,
               w.temperature_c, w.humidity, w.wind_speed_kmh
        FROM energy_demand e
        JOIN weather w ON w.location_id=e.location_id AND w.timestamp=e.timestamp
        WHERE e.timestamp BETWEEN %s AND %s
        ORDER BY e.timestamp
    """, (start, end))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([serialize_record(row) for row in rows])


# ------------------------------------------------------------
# CRUD: Update
# ------------------------------------------------------------
@app.route("/api/sql/records/<int:demand_id>", methods=["PUT"])
def update_record(demand_id):
    data = request.get_json(force=True)
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT location_id, timestamp FROM energy_demand WHERE demand_id=%s", (demand_id,))
    record = cur.fetchone()
    if record is None:
        cur.close()
        conn.close()
        return jsonify({"error": "record not found"}), 404
    cur.execute("UPDATE energy_demand SET demand_mwh=%s, is_weekend=%s WHERE demand_id=%s",
                (data["demand_mwh"], data.get("is_weekend", 0), demand_id))
    cur.execute(
        "UPDATE weather SET temperature_c=%s, humidity=%s, wind_speed_kmh=%s "
        "WHERE location_id=%s AND timestamp=%s",
        (data["temperature_c"], data["humidity"], data["wind_speed_kmh"],
         record["location_id"], record["timestamp"]),
    )
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"status": "updated", "demand_id": demand_id})


# ------------------------------------------------------------
# CRUD: Delete
# ------------------------------------------------------------
@app.route("/api/sql/records/<int:demand_id>", methods=["DELETE"])
def delete_record(demand_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM energy_demand WHERE demand_id=%s", (demand_id,))
    if cur.rowcount == 0:
        cur.close()
        conn.close()
        return jsonify({"error": "record not found"}), 404
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"status": "deleted", "demand_id": demand_id})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
