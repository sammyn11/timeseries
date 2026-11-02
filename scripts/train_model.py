"""
Task: Model Training + Hyperparameter Tuning (Person B role)
Trains Linear Regression to predict energy demand.
Compares 2 experiments in an experiment table.
"""
import os
import pandas as pd
import numpy as np
import joblib
from sklearn.linear_model import LinearRegression
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from preprocess import load_data, preprocess

os.makedirs("models", exist_ok=True)
os.makedirs("experiments", exist_ok=True)


df = load_data()
df = preprocess(df, add_features=True)


feature_cols = ["hour", "dayofweek", "month", "is_weekend",
                "temperature_c", "humidity", "wind_speed_kmh",
                "demand_lag_1h", "demand_lag_24h", "demand_lag_168h",
                "demand_ma_7h", "demand_ma_24h"]
X = df[feature_cols]
y = df["energy_demand_mwh"]


split = int(0.8 * len(X))
X_train, X_test = X.iloc[:split], X.iloc[split:]
y_train, y_test = y.iloc[:split], y.iloc[split:]

print("Train:", len(X_train), "rows | Test:", len(X_test), "rows\n")


model1 = LinearRegression()
model1.fit(X_train, y_train)
pred1 = model1.predict(X_test)
exp1 = {
    "experiment": 1,
    "model": "LinearRegression",
    "scaling": "None",
    "features": "raw + lags + MA",
    "hyperparams": "default",
    "MAE": round(mean_absolute_error(y_test, pred1), 2),
    "RMSE": round(np.sqrt(mean_squared_error(y_test, pred1)), 2),
    "R2": round(r2_score(y_test, pred1), 4),
}


pipe = Pipeline([
    ("scaler", StandardScaler()),
    ("ridge", Ridge())
])
param_grid = {"ridge__alpha": [0.01, 0.1, 1.0, 10.0, 100.0]}
time_series_cv = TimeSeriesSplit(n_splits=3)
grid = GridSearchCV(
    pipe,
    param_grid,
    cv=time_series_cv,
    scoring="neg_mean_absolute_error",
    n_jobs=-1,
)
grid.fit(X_train, y_train)
pred2 = grid.predict(X_test)
exp2 = {
    "experiment": 2,
    "model": "Ridge + StandardScaler",
    "scaling": "StandardScaler",
    "features": "raw + lags + MA",
    "hyperparams": "alpha=" + str(grid.best_params_["ridge__alpha"]),
    "MAE": round(mean_absolute_error(y_test, pred2), 2),
    "RMSE": round(np.sqrt(mean_squared_error(y_test, pred2)), 2),
    "R2": round(r2_score(y_test, pred2), 4),
}


exp_df = pd.DataFrame([exp1, exp2])
print("=== EXPERIMENT TABLE ===")
print(exp_df.to_string(index=False))
exp_df.to_csv("experiments/experiment_results.csv", index=False)


best = exp1 if exp1["MAE"] < exp2["MAE"] else exp2
print("\nBest experiment:", best["experiment"], "(MAE=" + str(best["MAE"]) + ")")
best_model = model1 if best["experiment"] == 1 else grid.best_estimator_
joblib.dump(best_model, "models/energy_demand_model.pkl")
print("Saved best model to models/energy_demand_model.pkl")