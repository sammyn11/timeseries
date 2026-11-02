import os

import pandas as pd


def load_seed_records(limit=500):
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    energy_path = os.path.join(data_dir, "energy_dataset.csv")
    weather_path = os.path.join(data_dir, "weather_features.csv")

    energy = pd.read_csv(energy_path, usecols=["time", "total load actual"])
    energy = energy.rename(columns={"time": "timestamp", "total load actual": "demand_mwh"})

    weather = pd.read_csv(
        weather_path,
        usecols=["dt_iso", "city_name", "temp", "humidity", "wind_speed"],
    )
    weather = weather.loc[weather["city_name"] == "Valencia"].rename(
        columns={
            "dt_iso": "timestamp",
            "temp": "temperature_k",
            "wind_speed": "wind_speed_ms",
        }
    )

    records = energy.merge(weather, on="timestamp", how="inner")
    records["temperature_c"] = records["temperature_k"] - 273.15
    records["wind_speed_kmh"] = records["wind_speed_ms"] * 3.6
    records = records.dropna(
        subset=["demand_mwh", "temperature_c", "humidity", "wind_speed_kmh"]
    ).sort_values("timestamp").tail(limit)
    records["is_weekend"] = (
        pd.to_datetime(records["timestamp"]).dt.dayofweek >= 5
    ).astype(int)

    return records[
        ["timestamp", "temperature_c", "humidity", "wind_speed_kmh", "demand_mwh", "is_weekend"]
    ].to_dict("records")