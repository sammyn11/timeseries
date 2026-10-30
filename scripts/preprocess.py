"""
Preprocessing pipeline for the energy demand dataset.
Used by both Task 1 (EDA) and Task 4 (prediction script).
"""
import pandas as pd
import numpy as np


def load_data(path="data/energy_weather_4years.csv"):
    df = pd.read_csv(path, parse_dates=["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
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

    if method == "ffill":
        df[["temperature_c", "humidity"]] = df[["temperature_c", "humidity"]].ffill()
    elif method == "mean":
        df["temperature_c"] = df["temperature_c"].fillna(df["temperature_c"].mean())
        df["humidity"] = df["humidity"].fillna(df["humidity"].mean())

    # Any remaining leading NaNs (if first row is missing) -> backward fill
    df[["temperature_c", "humidity"]] = df[["temperature_c", "humidity"]].bfill()

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
    Add rolling moving averages of demand.
    Window 7 = 7-hour average, Window 24 = 24-hour (1 day) average.
    """
    df = df.copy()
    for w in windows:
        df[f"demand_ma_{w}h"] = (
            df["energy_demand_mwh"].rolling(window=w, min_periods=1).mean()
        )
    return df


def preprocess(df, add_features=True):
    """Full preprocessing pipeline."""
    df = handle_missing(df, method="ffill")
    df = add_time_features(df)
    if add_features:
        df = add_lag_features(df, lags=[1, 24, 168])
        df = add_moving_average(df, windows=[7, 24])
    # Drop rows with NaNs created by lag/shift (first 24 rows)
    df = df.dropna().reset_index(drop=True)
    return df


if __name__ == "__main__":
    df = load_data()
    print("Raw shape:", df.shape)
    print("Missing:\n", df.isna().sum())

    df_clean = preprocess(df)
    print("\nClean shape:", df_clean.shape)
    print(df_clean.head())