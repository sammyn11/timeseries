# MongoDB Collection Design (NoSQL)

## Collection: `energy_readings`

Unlike SQL, we store weather + demand together in one document per timestamp
because they are always queried together for forecasting. This avoids joins.

### Sample Document

{
  "_id": ObjectId("..."),
  "location": {
    "location_id": 1,
    "city": "Sample City",
    "country": "Sample Country",
    "region": "Central",
    "coords": { "lat": 40.7128, "lon": -74.0060 }
  },
  "timestamp": ISODate("2023-06-15T14:00:00Z"),
  "is_weekend": false,
  "weather": {
    "temperature_c": 24.5,
    "humidity": 58.0,
    "wind_speed_kmh": 12.0
  },
  "energy": {
    "demand_mwh": 1120.40
  },
  "created_at": ISODate("2023-06-15T14:00:05Z")
}

### Indexes (important for time-series queries)
db.energy_readings.createIndex({ "timestamp": 1 });
db.energy_readings.createIndex({ "location.location_id": 1, "timestamp": 1 });

### Design Rationale
- **Embedded model:** weather and energy are embedded in the same document so a
  single read returns everything needed for a prediction (no joins).
- **Timestamp indexed:** supports fast "latest record" and "date range" queries.
- **Flexible schema:** easy to add new sensor fields later without migrations.