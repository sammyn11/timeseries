# Energy Demand Forecasting — Time Series Formative 1

Group project: creating an end-to-end time-series pipeline covering EDA, preprocessing,
SQL & MongoDB databases, CRUD API endpoints, and a prediction script.

## Dataset
**https://www.kaggle.com/datasets/nicholasjhana/energy-consumption-generation-prices-and-weather**
`api/data/energy_dataset.csv` and `api/data/weather_features.csv` — timestamp, temperature, humidity, wind speed,
energy demand (MWh), is_weekend.

Chosen because it has a clear timestamp, a meaningful prediction target
(energy demand), and multiple measurable variables over time — exactly what
the assignment requires.

## Repository Structure
```
TimeSeries_Project/
├── scripts/                      # Python scripts
│   ├── preprocess.py             # Cleaning + lag + moving-average features
│   ├── eda_task1.py              # Task 1: 5 analytical questions + charts
│   ├── train_model.py            # Model training + experiment table
│   └── predict.py                # Task 4: end-to-end prediction script
├── api/                          # Task 3: CRUD APIs
│   ├── app_sql.py                # SQL API (port 5000)
│   ├── app_mongo.py              # MongoDB API (port 5001)
│   ├── seed_data.py              # Shared real-data loading for API seeding
│   ├── test_crud.py              # CRUD endpoint checks
│   └── data/                     # Original Kaggle dataset files
│       ├── energy_dataset.csv
│       └── weather_features.csv
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
pip install flask flask-cors pandas scikit-learn joblib matplotlib pymongo mysql-connector-python python-dotenv
```

### 2. Task 1 — Exploratory Data Analysis
Produces 5 charts in `outputs/charts/` and prints interpretations.
```bash
python scripts/eda_task1.py
```

### 3. Task 2 — Databases
- SQL: run `database/schema.sql` in MySQL Workbench or with `mysql -u root -p < database/schema.sql` (3 tables: locations, weather, energy_demand)
- MongoDB: `database/mongo_design.md` (embedded collection design + sample doc)

### 4. Train the model (+ experiment table)
```bash
python scripts/train_model.py
```
Saves `models/energy_demand_model.pkl` and
`experiments/experiment_results.csv`.

### 5. Task 3 — Run the APIs (separate terminals)
Add your MySQL connection settings to the project-root `.env` file using
`.env.example` as a guide. Run the SQL schema once before starting the API.
```bash
#SQL API on port 5000
python api/app_sql.py

#MongoDB API on port 5001 (requires MongoDB running)
python api/app_mongo.py
```
The MongoDB API reads `MONGO_URI` from the project-root `.env` file. If it is
not set, it connects to `mongodb://localhost:27017/`.

Endpoints (both databases):
- `POST   /api/<db>/records`        — create
- `GET    /api/<db>/records`        — read all
- `GET    /api/<db>/records/latest` — latest record
- `GET    /api/<db>/records/range?start=..&end=..` — date range
- `PUT    /api/<db>/records/<id>`   — update
- `DELETE /api/<db>/records/<id>`   — delete

### CRUD API Tests
Start both APIs, then run the test suite from the project root:
```bash
python api/test_crud.py
```
The suite checks SQL and MongoDB create, read, update, delete, latest-record,
and date-range behavior. Configure and start both database APIs before running it.

### 6. Task 4 — Prediction script
```bash
python scripts/predict.py
```
Fetches the latest record, preprocesses it, loads the trained model, and prints
a demand forecast.

## Team Roles
| Role | Responsibility | Files |
|------|---------------|-------|
| Task 1| Data + EDA | `scripts/eda_task1.py`, `outputs/charts/` |
| Task 2 | Model + tuning | `scripts/train_model.py`, `models/`, `experiments/` |
| Task 3 | Databases | `database/schema.sql`, `database/mongo_design.md` |
| Task 4 | API + prediction script | `api/`, `scripts/predict.py` |

Each member made commits with clear messages (e.g. "added missing-value handling",
"built SQL CRUD endpoints").