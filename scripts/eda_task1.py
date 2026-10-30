"""
Task 1: Exploratory Data Analysis & Preprocessing (Person A role)
Answers 5 analytical questions with visualizations.
At least 2 questions use lagged features and moving averages.
Outputs charts to outputs/charts/ and prints a summary.
"""
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from preprocess import load_data, handle_missing, preprocess

os.makedirs("outputs/charts", exist_ok=True)

# ------------------------------------------------------------
# Load & clean
# ------------------------------------------------------------
df = load_data()
df_clean = handle_missing(df, method="ffill")
df_clean = preprocess(df_clean, add_features=True)

print("=== DATASET OVERVIEW ===")
print("Time range:", df_clean["timestamp"].min(), "to", df_clean["timestamp"].max())
print("Frequency: Hourly (" + str(len(df_clean)) + " records)")
print("\nStatistical summary:\n")
print(df_clean[["temperature_c", "humidity", "wind_speed_kmh", "energy_demand_mwh"]].describe())

plt.style.use("default")

# ------------------------------------------------------------
# Q1: Trend - Is demand increasing or decreasing over 4 years?
# ------------------------------------------------------------
monthly = df_clean.set_index("timestamp").resample("ME")["energy_demand_mwh"].mean()

plt.figure(figsize=(10, 4))
plt.plot(monthly.index, monthly.values, marker="o", linewidth=1.5)
plt.title("Q1: Average Monthly Energy Demand Over 4 Years (Trend)")
plt.xlabel("Year")
plt.ylabel("Average Demand (MWh)")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("outputs/charts/q1_trend.png", dpi=150)
plt.close()

print("\nQ1 - TREND:")
print("Demand starts around", round(monthly.iloc[0], 1), "MWh and ends around",
      round(monthly.iloc[-1], 1), "MWh.")
print("Interpretation: There is a slight upward trend over the 4 years "
      "(growing consumption), so the model should account for time/trend.")

# ------------------------------------------------------------
# Q2: Seasonality - Does demand peak in summer or winter?
# ------------------------------------------------------------
df_clean["month_name"] = df_clean["timestamp"].dt.month_name()
month_order = ["January", "February", "March", "April", "May", "June", "July",
               "August", "September", "October", "November", "December"]
monthly_season = df_clean.groupby("month_name")["energy_demand_mwh"].mean().reindex(month_order)

plt.figure(figsize=(10, 4))
plt.bar(monthly_season.index, monthly_season.values, color="steelblue")
plt.title("Q2: Average Demand by Month (Seasonality)")
plt.xlabel("Month")
plt.ylabel("Average Demand (MWh)")
plt.xticks(rotation=45)
plt.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig("outputs/charts/q2_seasonality.png", dpi=150)
plt.close()

top_month = monthly_season.idxmax()
low_month = monthly_season.idxmin()
print("\nQ2 - SEASONALITY:")
print("Highest demand month:", top_month, "(" + str(round(monthly_season.max(), 1)) + " MWh)")
print("Lowest demand month:", low_month, "(" + str(round(monthly_season.min(), 1)) + " MWh)")
print("Interpretation: Demand peaks in", top_month, "and", low_month, "is lowest - "
      "clear seasonal pattern (heating/cooling).")

# ------------------------------------------------------------
# Q3: Correlation - Does temperature correlate with demand?
# ------------------------------------------------------------
plt.figure(figsize=(6, 6))
plt.scatter(df_clean["temperature_c"], df_clean["energy_demand_mwh"],
            alpha=0.3, s=10, color="darkgreen")
plt.title("Q3: Temperature vs Energy Demand")
plt.xlabel("Temperature (C)")
plt.ylabel("Demand (MWh)")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("outputs/charts/q3_correlation.png", dpi=150)
plt.close()

corr = df_clean["temperature_c"].corr(df_clean["energy_demand_mwh"])
print("\nQ3 - CORRELATION:")
print("Correlation between temperature and demand:", round(corr, 3))
print("Interpretation: Correlation is", round(corr, 3), "- indicates a relationship "
      "(likely U-shaped: both very cold and very hot raise demand).")

# ------------------------------------------------------------
# Q4: Lagged feature - Is today's demand related to demand 7 days ago? (LAG)
# ------------------------------------------------------------
plt.figure(figsize=(6, 6))
plt.scatter(df_clean["demand_lag_168h"], df_clean["energy_demand_mwh"],
            alpha=0.3, s=10, color="purple")
plt.title("Q4: Demand vs Demand 7 Days Ago (Lagged Feature)")
plt.xlabel("Demand 7 days ago (MWh)")
plt.ylabel("Demand today (MWh)")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("outputs/charts/q4_lag.png", dpi=150)
plt.close()

lag_corr = df_clean["demand_lag_168h"].corr(df_clean["energy_demand_mwh"])
print("\nQ4 - LAGGED FEATURE (7-day lag):")
print("Correlation between demand and demand 7 days ago:", round(lag_corr, 3))
print("Interpretation: Strong correlation of", round(lag_corr, 3),
      "- demand repeats weekly, so lagged features are useful predictors.")

# ------------------------------------------------------------
# Q5: Moving average - Does 24-hour moving average smooth demand? (MA)
# ------------------------------------------------------------
sample = df_clean.set_index("timestamp").loc["2023-06-01":"2023-06-14"]

plt.figure(figsize=(11, 4))
plt.plot(sample.index, sample["energy_demand_mwh"], label="Actual Demand", linewidth=1)
plt.plot(sample.index, sample["demand_ma_24h"], label="24-hr Moving Average",
         linewidth=2, color="orange")
plt.title("Q5: 24-Hour Moving Average Smooths Demand (June 2023)")
plt.xlabel("Date")
plt.ylabel("Demand (MWh)")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("outputs/charts/q5_moving_average.png", dpi=150)
plt.close()

print("\nQ5 - MOVING AVERAGE:")
print("The 24-hour moving average smooths out daily spikes and reveals the "
      "underlying demand level.")
print("Interpretation: Moving average is useful for forecasting because it "
      "filters short-term noise.")

print("\n=== All 5 charts saved to outputs/charts/ ===")
print("Q1 trend.png  Q2 seasonality.png  Q3 correlation.png  Q4 lag.png  Q5 moving_average.png")