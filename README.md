# NASA Turbofan Predictive Maintenance & Real-Time RUL Streaming Prototype

[![CI](https://github.com/beambomb/turbofan-predictive-maintenance/actions/workflows/ci.yml/badge.svg)](https://github.com/beambomb/turbofan-predictive-maintenance/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Apache Kafka](https://img.shields.io/badge/Apache_Kafka-3.8_KRaft-231F20?style=for-the-badge&logo=apachekafka&logoColor=white)](https://kafka.apache.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![dbt](https://img.shields.io/badge/dbt-1.8-FF694B?style=for-the-badge&logo=dbt&logoColor=white)](https://getdbt.com)
[![XGBoost](https://img.shields.io/badge/XGBoost-Champion-EB7532?style=for-the-badge)](https://xgboost.ai)

An end-to-end predictive maintenance (PdM) and remaining useful life (RUL) streaming prototype for aircraft turbofan engines, built on the NASA C-MAPSS FD001 dataset. The system integrates event-driven streaming ingestion, a warehouse feature store, machine learning inference serving, and real-time WebSocket telemetry broadcasting.

---

## Architecture Overview

```text
[ AIRCRAFT TELEMETRY REPLAY ]
  Sensor Event Producer
           │
           ▼ (Streaming Telemetry Frames via Kafka Topics)
  Apache Kafka 3.8 (KRaft Single-Node Mode)
           │
           ▼ (Consumer Batch Ingestion)
  PostgreSQL 16 (Time-Series Data Warehouse)
           │
           ▼ (dbt: Sensor Pruning + 5-Cycle Rolling Stats + Wear Drift)
  Feature Store (Snappy Parquet: 38 Extracted Features)
           │
           ├───────────────────────────────────────────────┐
           ▼                                               ▼
[ MODEL TOURNAMENT ]                              [ SERVING & STREAMING ]
  1. XGBoost (Tuned - Champion)                    FastAPI (Layered Architecture)
  2. LightGBM (Tuned)                              - REST API (/predict-rul)
  3. PyTorch CNN-BiGRU                             - WebSocket (/ws/telemetry/{id})
  4. Attention-BiGRU (Asymmetric Loss)             - Live Interactive Web Console
```

---

## Model Benchmark Results

Models were evaluated on hold-out validation engines from the NASA C-MAPSS FD001 sub-dataset using Root Mean Squared Error (RMSE), Mean Absolute Error (MAE), and the asymmetric NASA Scoring Function.

| Model | RMSE | MAE | Cumulative Validation Score | Final Cycle NASA Score | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **XGBoost (Tuned)** | **14.39** | **10.92** | **15,235** | **6.11** | **Champion** |
| LightGBM (Tuned) | 14.46 | 10.92 | 15,908 | 6.84 | Runner-up |
| PyTorch CNN-BiGRU | 15.61 | 10.96 | 15,591 | 8.21 | Top Deep Learning |
| Attention-BiGRU | 17.71 | 12.42 | 24,720 | 14.50 | Asymmetric Loss |

### Understanding the NASA Scoring Discrepancy
The asymmetric NASA scoring function penalizes late predictions (where predicted RUL > true RUL) exponentially more severely than early predictions ($e^{d/10}-1$ vs $e^{-d/13}-1$).
* **Literature Standard (~200 to 1,000):** Academic benchmarks (e.g., Heimes 2008, Babu et al. 2016) calculate the score strictly on the **single final cutoff window per engine** ($N=100$ predictions in `test_FD001.txt`).
* **Cumulative Validation Score (15,235):** In our continuous monitoring experiment, the score was accumulated across **all 4,493 time steps** of the 20 validation engines. Summing exponential penalties over thousands of cycles naturally yields a score in the tens of thousands.
* **Final Cutoff Verification (6.11):** When evaluated strictly at the terminal cycle across the 20 validation engines, the model achieved a score of **6.11** (RMSE 2.83).

---

## Simulated Maintenance Cost Optimization

To evaluate practical operational utility, maintenance strategies were simulated across the 20 validation engines using baseline commercial aviation figures:
* **Cost of Unscheduled In-Flight Shutdown / AOG ($C_{\text{breakdown}}$):** \$150,000
* **Cost of Scheduled Depot Inspection / Overhaul ($C_{\text{inspection}}$):** \$15,000

$$\text{Total Maintenance Cost} = (N_{\text{inspections}} \times C_{\text{inspection}}) + (N_{\text{breakdowns}} \times C_{\text{breakdown}})$$

| Maintenance Policy | Trigger Condition | Total Cost (20 Engines) | Savings vs Reactive |
| :--- | :--- | :---: | :---: |
| **Run-to-Failure (Reactive)** | No action until breakdown | \$3,000,000 | Baseline |
| **Periodic Maintenance** | Fixed inspection every 100 cycles | \$525,000 | \$2,475,000 (82.5%) |
| **Predictive Maintenance (Model)** | Inspection alert when Predicted RUL ≤ 25 | **\$300,000** | **\$2,700,000 (90.0%)** |

By triggering preventative maintenance alerts when predicted RUL drops to 25 cycles or below, all 20 engines were safely intercepted before catastrophic failure, eliminating unscheduled breakdown penalties while reducing unnecessary early inspections by \$225,000 (42.8% cost reduction) compared to fixed-interval periodic maintenance.

---

## Prototype Limitations & Production Roadmap

This project is a functional engineering prototype designed to validate end-to-end data pipelines and low-latency inference. Key limitations include:
1. **Single Operating Regime (FD001):** The FD001 dataset represents a single sea-level operating condition with one primary fault mode (High-Pressure Compressor degradation). Real-world flight envelopes (represented in FD002 and FD004) involve multiple altitudes, Mach numbers, throttle settings, and dual fault modes.
2. **Deterministic Simulation:** Sensor inputs are generated from the C-MAPSS numerical simulation without atmospheric turbulence, intermittent telemetry drops, or transducer calibration drift.
3. **Fixed Piecewise RUL:** The 125-cycle early-life flat ceiling is a heuristic assumption that all engines share an identical early wear profile.

---

## Repository Structure

```text
├── .github/
│   └── workflows/
│       └── ci.yml
├── docker/
│   └── docker-compose.yml
├── data/
│   ├── raw/
│   └── processed/
├── models/
│   ├── best_rul_model.joblib
│   └── best_rul_model.onnx
├── notebooks/
│   └── turbofan_rul_modeling.ipynb
├── src/
│   ├── ingestion/
│   │   ├── producer.py
│   │   ├── consumer.py
│   │   └── schemas.py
│   ├── transformation/
│   │   ├── models/staging/
│   │   ├── models/marts/
│   │   └── export_features.py
│   ├── serving/
│   │   ├── core/
│   │   ├── services/
│   │   ├── routers/
│   │   ├── schemas.py
│   │   ├── static/
│   │   └── main.py
│   ├── dashboard/
│   └── utils/
├── tests/
│   └── test_api.py
├── requirements.txt
└── README.md
```

---

## Quickstart Guide

### 1. Environment Setup
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Infrastructure Setup
```bash
docker compose -f docker/docker-compose.yml up -d
```
* PostgreSQL: `localhost:5433` (Database: `turbofan_dw`)
* Apache Kafka: `localhost:9092`
* Kafka-UI: `http://localhost:8080`

### 3. Data Ingestion
```bash
python src/utils/download_data.py
```
Start the consumer in the first terminal:
```bash
python -m src.ingestion.consumer --batch-size 500
```
Start the producer in a second terminal to replay 20,631 telemetry records:
```bash
python -m src.ingestion.producer --delay-ms 1
```

### 4. Data Transformation with dbt
```bash
cd src/transformation
dbt run
dbt test
cd ../..
python src/transformation/export_features.py
```

### 5. Start Inference Server
```bash
uvicorn src.serving.main:app --host 0.0.0.0 --port 8000 --reload
```
* Interactive Swagger Documentation: `http://localhost:8000/docs`
* Real-Time WebSocket Telemetry Console: `http://localhost:8000/live-demo`

### 6. Automated Testing
```bash
pytest -v tests/
```

---

## API & WebSocket Reference

### REST Endpoints

#### Server Health Check
```http
GET /health
```
Response:
```json
{
  "status": "healthy",
  "active_model": "XGBoost",
  "app_version": "1.0.0"
}
```

#### On-Demand RUL Prediction
```http
POST /predict-rul
Content-Type: application/json

{
  "engine_id": 1,
  "features": [-0.0007, -0.0004, 100.0, ..., 0.0]
}
```
Response:
```json
{
  "engine_id": 1,
  "predicted_rul": 125.0,
  "health_status": "HEALTHY",
  "recommended_action": "Operasi normal, tidak butuh tindakan perawatan",
  "inference_time_ms": 2.1,
  "model_used": "XGBoost"
}
```

### WebSocket Telemetry Stream
```text
ws://localhost:8000/ws/telemetry/{engine_id}?interval=0.5&loop=true&start_cycle=1
```
Real-time JSON frame payload:
```json
{
  "engine_id": 1,
  "cycle": 151,
  "total_cycles": 192,
  "predicted_rul": 57.16,
  "health_status": "WARNING",
  "recommended_action": "Rencanakan jadwal inspeksi dalam 15 siklus ke depan",
  "inference_time_ms": 1.4,
  "model_used": "XGBoost",
  "sensors": {
    "lpc_temp": 642.75,
    "hpc_temp": 1591.24,
    "lpt_temp": 1408.82,
    "hpc_pressure": 553.81,
    "core_speed": 9051.42,
    "fuel_flow": 47.45,
    "bypass_ratio": 8.4312,
    "bleed_enthalpy": 393.0
  }
}
```
