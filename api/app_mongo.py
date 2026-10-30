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
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId

app = Flask(__name__)
CORS(app)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)
db = client["energy_db"]
collection = db["energy_readings"]

# Indexes for time-series queries
collection.create_index("timestamp")
collection.create_index([("location.location_id", 1), ("timestamp", 1)])

# Seed if empty
CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "energy_weather_4years.csv")
if collection.count_documents({}) == 0 and os.path.exists(CSV_PATH):
    import pandas as pd
    df = pd.read_csv(CSV_PATH).head(500)
    docs = []
    for _, r in df.iterrows():
        docs.append({
            "location": {"location_id": 1, "city": "Sample City", "country": "Sample Country", "region": "Central"},
            "timestamp": str(r["timestamp"]),
            "is_weekend": bool(r["is_weekend"]),
            "weather": {"temperature_c": float(r["temperature_c"]), "humidity": float(r["humidity"]), "wind_speed_kmh": float(r["wind_speed_kmh"])},
            "energy": {"demand_mwh": float(r["energy_demand_mwh"])},
        })
    collection.insert_many(docs)
    print("Seeded MongoDB with", len(docs), "documents.")


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
        "timestamp": data["timestamp"],
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