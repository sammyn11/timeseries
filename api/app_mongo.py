"""
Task 3: CRUD + Time-Series API for MongoDB (Person D role)
Runs on port 5001. Requires MongoDB running locally (mongodb://localhost:27017).
Endpoints mirror the SQL API:
  POST   /api/mongo/records
  GET    /api/mongo/records
  GET    /api/mongo/records/latest
  GET    /api/mongo/records/range?start=...&end=...
  PUT    /api/mongo/records/<id>
  DELETE /api/mongo/records/<id>
"""
import os
from datetime import datetime, timezone
from flask import Flask, request, jsonify
from flask_cors import CORS
from bson import ObjectId
from pymongo import MongoClient, UpdateOne
from dotenv import load_dotenv

if __package__:
    from .seed_data import load_seed_records
else:
    from seed_data import load_seed_records

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))


def normalize_timestamp(value):
    timestamp = datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    return timestamp.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

app = Flask(__name__)
CORS(app)


@app.route("/")
def index():
    return jsonify({
        "service": "Energy Demand MongoDB API",
        "records": "/api/mongo/records",
    })


@app.route("/favicon.ico")
def favicon():
    return "", 204


MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client["energy_db"]
collection = db["energy_readings"]

#Indexes for time-series queries
collection.create_index("timestamp")
collection.create_index([("location.location_id", 1), ("timestamp", 1)])

seed_records = load_seed_records()
if seed_records:
    operations = [
        UpdateOne(
            {"timestamp": normalize_timestamp(row["timestamp"]), "location.location_id": 1},
            {"$setOnInsert": {
                "location": {"location_id": 1, "city": "Valencia", "country": "Spain", "region": "Valencian Community"},
                "timestamp": normalize_timestamp(row["timestamp"]),
                "is_weekend": bool(row["is_weekend"]),
                "weather": {
                    "temperature_c": row["temperature_c"],
                    "humidity": row["humidity"],
                    "wind_speed_kmh": row["wind_speed_kmh"],
                },
                "energy": {"demand_mwh": row["demand_mwh"]},
            }},
            upsert=True,
        )
        for row in seed_records
    ]
    result = collection.bulk_write(operations, ordered=False)
    print("Ensured MongoDB seed data; added", result.upserted_count, "documents.")


def doc_to_json(doc):
    doc["_id"] = str(doc["_id"])
    return doc


# ------------------------------------------------------------
# CRUD: Create
# ------------------------------------------------------------
@app.route("/api/mongo/records", methods=["POST"])
def create_record():
    data = request.get_json(force=True)
    doc = {
        "location": {"location_id": 1, "city": "Sample City", "country": "Sample Country", "region": "Central"},
        "timestamp": normalize_timestamp(data["timestamp"]),
        "is_weekend": bool(data.get("is_weekend", 0)),
        "weather": {"temperature_c": float(data["temperature_c"]), "humidity": float(data["humidity"]), "wind_speed_kmh": float(data["wind_speed_kmh"])},
        "energy": {"demand_mwh": float(data["demand_mwh"])},
    }
    result = collection.insert_one(doc)
    return jsonify({"status": "created", "_id": str(result.inserted_id)}), 201


# ------------------------------------------------------------
# CRUD: Read (all)
# ------------------------------------------------------------
@app.route("/api/mongo/records", methods=["GET"])
def get_records():
    limit = int(request.args.get("limit", 50))
    cursor = collection.find().sort("timestamp", -1).limit(limit)
    return jsonify([doc_to_json(d) for d in cursor])


# ------------------------------------------------------------
# Time-series: Latest record
# ------------------------------------------------------------
@app.route("/api/mongo/records/latest", methods=["GET"])
def get_latest():
    doc = collection.find_one(sort=[("timestamp", -1)])
    if not doc:
        return jsonify({"error": "no records"}), 404
    return jsonify(doc_to_json(doc))


# ------------------------------------------------------------
# Time-series: Records by date range
# ------------------------------------------------------------
@app.route("/api/mongo/records/range", methods=["GET"])
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
    cursor = collection.find({"timestamp": {"$gte": start, "$lte": end}}).sort("timestamp", 1)
    return jsonify([doc_to_json(d) for d in cursor])


# ------------------------------------------------------------
# CRUD: Update
# ------------------------------------------------------------
@app.route("/api/mongo/records/<record_id>", methods=["PUT"])
def update_record(record_id):
    data = request.get_json(force=True)
    result = collection.update_one(
        {"_id": ObjectId(record_id)},
        {"$set": {
            "is_weekend": bool(data.get("is_weekend", 0)),
            "weather.temperature_c": float(data["temperature_c"]),
            "weather.humidity": float(data["humidity"]),
            "weather.wind_speed_kmh": float(data["wind_speed_kmh"]),
            "energy.demand_mwh": float(data["demand_mwh"]),
        }}
    )
    if result.matched_count == 0:
        return jsonify({"error": "record not found"}), 404
    return jsonify({"status": "updated", "_id": record_id})


# ------------------------------------------------------------
# CRUD: Delete
# ------------------------------------------------------------
@app.route("/api/mongo/records/<record_id>", methods=["DELETE"])
def delete_record(record_id):
    result = collection.delete_one({"_id": ObjectId(record_id)})
    if result.deleted_count == 0:
        return jsonify({"error": "record not found"}), 404
    return jsonify({"status": "deleted", "_id": record_id})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)