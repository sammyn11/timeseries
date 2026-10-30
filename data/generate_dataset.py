"""
Generate a synthetic 4-year energy demand + weather dataset.
This mimics a Kaggle-style time-series dataset with:
  - A clear timestamp column
  - A prediction target (energy demand in MWh)
  - Multiple measurable variables over time (temperature, humidity, wind)
"""
import pandas as pd
import numpy as np

np.random.seed(42)

# 4 years of hourly data: 2020-01-01 to 2023-12-31
dates = pd.date_range(start="2020-01-01", end="2023-12-31 23:00", freq="h")
n = len(dates)

hour = dates.hour
dayofweek = dates.dayofweek  # 0=Mon ... 6=Sun
month = dates.month
is_weekend = (dayofweek >= 5).astype(int)

# --- Weather: seasonal temperature (colder in winter, hotter in summer) ---
# month 12/1/2 = winter, 6/7/8 = summer
seasonal_temp = 15 - 10 * np.cos(2 * np.pi * (month - 1) / 12)  # roughly 5..25 C
daily_temp_variation = 5 * np.sin(2 * np.pi * hour / 24)         # warmer in afternoon
temperature = seasonal_temp + daily_temp_variation + np.random.normal(0, 2, n)

humidity = 70 - 0.5 * temperature + np.random.normal(0, 5, n)
humidity = np.clip(humidity, 20, 100)

wind_speed = 5 + 3 * np.sin(2 * np.pi * (month - 3) / 12) + np.random.normal(0, 1.5, n)
wind_speed = np.clip(wind_speed, 0, 20)

# --- Energy demand: base + daily cycle + weekly + seasonal + temp effect ---
base_demand = 800
daily_cycle = 200 * np.sin(2 * np.pi * (hour - 6) / 24)        # peak mid-afternoon
weekly_effect = np.where(is_weekend == 1, -100, 0)             # lower on weekends
seasonal_effect = 150 * np.cos(2 * np.pi * (month - 1) / 12)   # higher in winter/summer

# Temperature effect: U-shaped (very cold or very hot -> more heating/cooling)
temp_effect = 10 * np.abs(temperature - 18)

# Slight upward trend over the 4 years
trend = np.linspace(0, 80, n)

energy_demand = (
    base_demand + daily_cycle + weekly_effect + seasonal_effect
    + temp_effect + trend + np.random.normal(0, 25, n)
)
energy_demand = np.clip(energy_demand, 200, None)

df = pd.DataFrame({
    "timestamp": dates,
    "temperature_c": temperature.round(2),
    "humidity": humidity.round(2),
    "wind_speed_kmh": wind_speed.round(2),
    "energy_demand_mwh": energy_demand.round(2),
    "is_weekend": is_weekend,
})

# Introduce a few missing values (~1%) so we can demonstrate handling
missing_idx = np.random.choice(n, size=int(0.01 * n), replace=False)
df.loc[missing_idx[:len(missing_idx)//2], "temperature_c"] = np.nan
df.loc[missing_idx[len(missing_idx)//2:], "humidity"] = np.nan

df.to_csv("C:/Users/user/TimeSeries_Project/data/energy_weather_4years.csv", index=False)
print(f"Generated {len(df)} rows saved to data/energy_weather_4years.csv")
print(df.head())
print("\nMissing values:\n", df.isna().sum())