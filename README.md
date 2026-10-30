# Energy Demand Forecasting — Time Series Formative 1

Group project: end-to-end time-series pipeline covering EDA, preprocessing,
SQL & MongoDB databases, CRUD API endpoints, and a prediction script.

## Dataset
**Energy demand + weather (4 years of hourly data)**
`data/energy_weather_4years.csv` — timestamp, temperature, humidity, wind speed,
energy demand (MWh), is_weekend.

Chosen because it has a clear timestamp, a meaningful prediction target
(energy demand), and multiple measurable variables over time — exactly what
the assignment requires.

## Repository Structure
```
TimeSeries_Project/
├── data/                         # Raw dataset + generator
│   ├── energy_weather_4years.csv
│   └── generate_dataset.py
├── scripts/                      # Python scripts
│   ├── preprocess.py             # Cleaning + lag + moving-average features
│   ├── eda_task1.py              # Task 1: 5 analytical questions + charts
│   ├── train_model.py            # Model training + experiment table
│   └── predict.py                # Task 4: end-to-end prediction script
├── api/                          # Task 3: CRUD APIs
│   ├── app_sql.py                # SQL API (port 5000)
│   └── app_mongo.py              # MongoDB API (port 5001)
├── database/                     # Task 2: Database design
│   ├── schema.sql                # SQL schema (3 tables)
│   └── mongo_design.md           # MongoDB collection design
├── models/                       # Trained model (.pkl)
├── experiments/                  # Experiment results CSV
├── outputs/charts/               # EDA visualizations (5 charts)
└── README.md
```

## How to Run

### 1. Install requirements
```bash
pip install flask flask-cors pandas scikit-learn joblib matplotlib pymongo
```

### 2. Generate / inspect the dataset
```bash
python data/generate_dataset.py
```

### 3. Task 1 — Exploratory Data Analysis
Produces 5 charts in `outputs/charts/` and prints interpretations.
```bash
python scripts/eda_task1.py
```

### 4. Task 2 — Databases
- SQL: `database/schema.sql` (3 tables: locations, weather, energy_demand)
- MongoDB: `database/mongo_design.md` (embedded collection design + sample doc)

### 5. Train the model (+ experiment table)
```bash
python scripts/train_model.py
```
Saves `models/energy_demand_model.pkl` and
`experiments/experiment_results.csv`.

### 6. Task 3 — Run the APIs (separate terminals)
```bash
# SQL API on port 5000
python api/app_sql.py

# MongoDB API on port 5001 (requires MongoDB running)
python api/app_mongo.py
```

Endpoints (both databases):
- `POST   /api/<db>/records`        — create
- `GET    /api/<db>/records`        — read all
- `GET    /api/<db>/records/latest` — latest record
- `GET    /api/<db>/records/range?start=..&end=..` — date range
- `PUT    /api/<db>/records/<id>`   — update
- `DELETE /api/<db>/records/<id>`   — delete

### 7. Task 4 — Prediction script
```bash
python scripts/predict.py
```
Fetches the latest record, preprocesses it, loads the trained model, and prints
a demand forecast.

## Team Roles
| Role | Responsibility | Files |
|------|---------------|-------|
| Person A | Data + EDA | `scripts/eda_task1.py`, `outputs/charts/` |
| Person B | Model + tuning | `scripts/train_model.py`, `models/`, `experiments/` |
| Person C | Databases | `database/schema.sql`, `database/mongo_design.md` |
| Person D | API + prediction script | `api/`, `scripts/predict.py` |

Each member made 4+ commits with clear messages (e.g. "added missing-value handling",
"built SQL CRUD endpoints").