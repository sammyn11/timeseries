"""
Preprocessing pipeline for the energy demand dataset.
Used by both Task 1 (EDA) and Task 4 (prediction script).
"""
import os

import pandas as pd
import numpy as np


def load_data(path=None):
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    if path:
        df = pd.read_csv(path)
    else:
        data_dirs = [
            os.path.join(project_root, "data"),
            os.path.join(project_root, "api", "data"),
        ]
        combined_path = next(
            (os.path.join(data_dir, "energy_weather_4years.csv")
             for data_dir in data_dirs
             if os.path.exists(os.path.join(data_dir, "energy_weather_4years.csv"))),
            None,
        )

        if combined_path:
            df = pd.read_csv(combined_path)
        else:
            raw_data_dir = next(
                (data_dir for data_dir in data_dirs
                 if os.path.exists(os.path.join(data_dir, "energy_dataset.csv"))
                 and os.path.exists(os.path.join(data_dir, "weather_features.csv"))),
                None,
            )
            if raw_data_dir is None:
                raise FileNotFoundError(
                    "Could not find energy_dataset.csv and weather_features.csv "
                    "under data/ or api/data/."
                )

            energy = pd.read_csv(
                os.path.join(raw_data_dir, "energy_dataset.csv"),
                usecols=["time", "total load actual"],
            ).rename(columns={"time": "timestamp", "total load actual": "energy_demand_mwh"})
            weather = pd.read_csv(
                os.path.join(raw_data_dir, "weather_features.csv"),
                usecols=["dt_iso", "city_name", "temp", "humidity", "wind_speed"],
            )
            weather = weather.loc[weather["city_name"] == "Valencia"].rename(
                columns={"dt_iso": "timestamp", "temp": "temperature_k", "wind_speed": "wind_speed_ms"}
            )
            df = energy.merge(weather, on="timestamp", how="inner")
            df["temperature_c"] = df["temperature_k"] - 273.15
            df["wind_speed_kmh"] = df["wind_speed_ms"] * 3.6
            df = df.drop(columns=["temperature_k", "wind_speed_ms", "city_name"])

    df["timestamp"] = (
        pd.to_datetime(df["timestamp"], utc=True)
        .dt.tz_convert("Europe/Madrid")
        .dt.tz_localize(None)
    )
    if "is_weekend" not in df:
        df["is_weekend"] = (df["timestamp"].dt.dayofweek >= 5).astype(int)
    df = (
        df.sort_values("timestamp")
        .drop_duplicates(subset="timestamp", keep="last")
        .reset_index(drop=True)
    )
    return df


def handle_missing(df, method="ffill"):
    """
    Handle missing values.
    method: 'ffill' (forward fill - use previous value) or 'mean' (column average).
    We choose forward-fill because weather/demand change slowly hour-to-hour,
    so the previous hour's value is a better estimate than the global average.
    """
    df = df.copy()
    before = df.isna().sum().sum()

    weather_columns = ["temperature_c", "humidity", "wind_speed_kmh"]
    if method == "ffill":
        df[weather_columns] = df[weather_columns].ffill()
    elif method == "mean":
        df[weather_columns] = df[weather_columns].fillna(df[weather_columns].mean())
    else:
        raise ValueError("method must be 'ffill' or 'mean'")

    # Any remaining leading NaNs (if first row is missing) -> backward fill
    df[weather_columns] = df[weather_columns].bfill()

    after = df.isna().sum().sum()
    print(f"Missing values: {before} -> {after} (method={method})")
    return df


def add_time_features(df):
    """Add basic time-based features."""
    df = df.copy()
    df["hour"] = df["timestamp"].dt.hour
    df["dayofweek"] = df["timestamp"].dt.dayofweek
    df["month"] = df["timestamp"].dt.month
    df["is_weekend"] = (df["dayofweek"] >= 5).astype(int)
    return df


def add_lag_features(df, lags=[1, 7, 24]):
    """
    Add lagged features: demand from N hours ago.
    Lag 1 = previous hour, Lag 7 = yesterday same time, Lag 24 = 1 day ago.
    """
    df = df.copy()
    for lag in lags:
        df[f"demand_lag_{lag}h"] = df["energy_demand_mwh"].shift(lag)
    return df


def add_moving_average(df, windows=[7, 24]):
    """
    Add rolling averages using only demand observed before each timestamp.
    """
    df = df.copy()
    for w in windows:
        df[f"demand_ma_{w}h"] = (
            df["energy_demand_mwh"].shift(1).rolling(window=w, min_periods=1).mean()
        )
    return df


def preprocess(df, add_features=True):
    """Full preprocessing pipeline."""
    df = handle_missing(df, method="ffill")
    df = add_time_features(df)
    if add_features:
        df = add_lag_features(df, lags=[1, 24, 168])
        df = add_moving_average(df, windows=[7, 24])
    # Keep the hourly index intact until features are computed, then omit rows
    # without a usable target or lag history.
    df = df.dropna().reset_index(drop=True)
    return df


if __name__ == "__main__":
    df = load_data()
    print("Raw shape:", df.shape)
    print("Missing:\n", df.isna().sum())

    df_clean = preprocess(df)
    print("\nClean shape:", df_clean.shape)
    print(df_clean.head())