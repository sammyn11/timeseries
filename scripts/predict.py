"""
Task 4: Prediction / Forecast Script (Person D role)
End-to-end:
  A. Fetch a time-series record from the API
  B. Preprocess it (same pipeline as Task 1)
  C. Load the trained model
  D. Make a prediction / forecast
"""
import os
import sys
import requests
import pandas as pd
import joblib

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from preprocess import load_data, handle_missing, add_time_features, add_lag_features, add_moving_average

API_BASE = "http://127.0.0.1:5000"   # SQL API (switch to 5001 for MongoDB API)
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "models", "energy_demand_model.pkl")
MODEL_PATH = os.path.abspath(MODEL_PATH)


def fetch_latest_record():
    """A. Fetch the latest record from the API."""
    url = API_BASE + "/api/sql/records/latest"
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        print("Fetched from API:", data)
        return data
    except Exception as e:
        print("API not reachable (" + str(e) + ") - falling back to local CSV latest row.")
        df = load_data()
        row = df.iloc[-1]
        return {
            "timestamp": str(row["timestamp"]),
            "temperature_c": row["temperature_c"],
            "humidity": row["humidity"],
            "wind_speed_kmh": row["wind_speed_kmh"],
            "energy_demand_mwh": row["energy_demand_mwh"],
            "is_weekend": int(row["is_weekend"]),
        }


def preprocess_record(record, history_df):
    """
    B. Preprocess the single record using the same pipeline as Task 1.
    We need recent history to compute lags and moving averages.
    """
    df = history_df.copy()
    # Append the new record so lags/MA can be computed
    new_row = pd.DataFrame([record])
    new_row["timestamp"] = pd.to_datetime(new_row["timestamp"])
    df = pd.concat([df, new_row], ignore_index=True)

    df = handle_missing(df, method="ffill")
    df = add_time_features(df)
    df = add_lag_features(df, lags=[1, 24, 168])
    df = add_moving_average(df, windows=[7, 24])

    # The last row is our record to predict
    row = df.iloc[[-1]].copy()
    return row


def predict(record, history_df):
    """C & D. Load model and make prediction."""
    if not os.path.exists(MODEL_PATH):
        print("Model not found. Run train_model.py first.")
        return None

    model = joblib.load(MODEL_PATH)
    print("Loaded model from", MODEL_PATH)

    row = preprocess_record(record, history_df)

    feature_cols = ["hour", "dayofweek", "month", "is_weekend",
                    "temperature_c", "humidity", "wind_speed_kmh",
                    "demand_lag_1h", "demand_lag_24h", "demand_lag_168h",
                    "demand_ma_7h", "demand_ma_24h"]

    X = row[feature_cols]
    prediction = model.predict(X)[0]
    actual = record.get("energy_demand_mwh", None)

    print("\n=== PREDICTION RESULT ===")
    print("Timestamp:", row["timestamp"].iloc[0])
    print("Temperature:", row["temperature_c"].iloc[0], "C")
    print("Predicted energy demand: " + str(round(prediction, 2)) + " MWh")
    if actual is not None:
        print("Actual demand: " + str(round(actual, 2)) + " MWh")
        print("Error: " + str(round(abs(prediction - actual), 2)) + " MWh")
    return prediction


if __name__ == "__main__":
    history = load_data()
    record = fetch_latest_record()
    predict(record, history)