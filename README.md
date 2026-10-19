# NASA Turbofan Predictive Maintenance & Real-Time RUL Streaming Prototype

[![CI](https://github.com/beambomb/turbofan-predictive-maintenance/actions/workflows/ci.yml/badge.svg)](https://github.com/beambomb/turbofan-predictive-maintenance/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Apache Kafka](https://img.shields.io/badge/Apache_Kafka-3.8_KRaft-231F20?style=for-the-badge&logo=apachekafka&logoColor=white)](https://kafka.apache.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![dbt](https://img.shields.io/badge/dbt-1.8-FF694B?style=for-the-badge&logo=dbt&logoColor=white)](https://getdbt.com)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com)
[![XGBoost](https://img.shields.io/badge/XGBoost-Champion-EB7532?style=for-the-badge)](https://xgboost.ai)

An end-to-end predictive maintenance and remaining useful life streaming prototype for aircraft turbofan engines, built on the NASA C-MAPSS FD001 dataset. The system integrates event-driven streaming ingestion, a warehouse feature store, machine learning tournament serving, real-time WebSocket telemetry broadcasting, and an interactive fleet decision intelligence dashboard.

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
           ├───────────────────────────────┬───────────────────────────────┐
           ▼                               ▼                               ▼
[ MODEL TOURNAMENT ]             [ SERVING & STREAMING ]         [ DECISION INTELLIGENCE ]
  Tuned XGBoost Champion           FastAPI Layered Service         Streamlit Fleet App
  RMSE 13.88 | Score 342.71        - REST API: /predict-rul        - Fleet Health Overview
  ONNX Deep Learning Runtime       - WebSocket: /ws/telemetry      - Degradation Deep Dives
                                   - Live Interactive Web Demo     - Maintenance Cost Sim
```

---

## Benchmark Results

### Official NASA C-MAPSS FD001 Test Benchmark
The primary benchmark was evaluated on the official test set (`test_FD001.txt`), comprising 100 aircraft turbofan engines operating for an unknown duration prior to failure. Predictions were generated at the final observed operational cycle of each engine and evaluated against true remaining cycles (`RUL_FD001.txt`) clipped at 125 cycles matching the training target ceiling.

| Model / Approach | RMSE | MAE | NASA Score | Source |
| :--- | :---: | :---: | :---: | :--- |
| **Our Tuned XGBoost: Feature Engineered** | **13.88** | **10.18** | **342.71** | This Repository |
| Zheng et al. 2017 LSTM Network | 16.14 | - | 338.00 | Literature |
| Heimes 2008 Recurrent Neural Network | 15.16 | - | 435.00 | Baseline Benchmark |
| Babu et al. 2016 2D Deep CNN | 18.44 | - | 1,286.00 | Literature |
| Li et al. 2018 Deep Convolutional Network | 12.61 | - | 274.00 | Advanced Sequence SOTA |

Reproduce this official benchmark locally:
```bash
python src/utils/evaluate_official_test.py
```

### Validation Experiment: Development Tournament
During model exploration, 4 architectures were trained on 80 training engines and validated against 20 hold-out training engines from `train_FD001.txt`:
* **Tuned XGBoost:** RMSE 14.39, MAE 10.92, Cumulative Score 15,235
* **Tuned LightGBM:** RMSE 14.46, MAE 10.92, Cumulative Score 15,908
* **PyTorch CNN-BiGRU:** RMSE 15.61, MAE 10.96, Cumulative Score 15,591
* **Attention-BiGRU with Asymmetric Loss:** RMSE 17.71, MAE 12.42, Cumulative Score 24,720

Note on the cumulative validation score (15,235): in this experiment, the asymmetric exponential penalty function was accumulated across **all 4,493 time steps** of the 20 engines rather than only the final cutoff cycle. When evaluated strictly at the terminal cycle of the training engines where true RUL has reached 0, the validation score was 6.11 (RMSE 2.83). However, terminal prediction on run-to-failure engines is significantly less challenging than predicting premature cutoffs in the official 100-engine test set.

---

## Fleet Decision Intelligence Dashboard

The Streamlit dashboard (`src/dashboard/app.py`) provides interactive situational awareness for airline operations and reliability engineers across three core views:

1. **Fleet Health Overview:**
   - Real-time KPI summary tracking Total Fleet, Healthy, Warning, and Critical engines.
   - Interactive Plotly status donut chart and fleet-wide RUL distribution histogram.
   - Urgency-ranked maintenance table prioritizing engines closest to critical thresholds.

2. **Engine Telemetry and Degradation Analysis:**
   - Dropdown engine selector with historical cycle trajectories.
   - Predicted RUL vs Ground Truth curve with configurable warning and critical thresholds.
   - Dual-axis thermal degradation curves tracking Low-Pressure Compressor (T24) and High-Pressure Compressor (T30) outlet temperatures.
   - Dual-axis mechanical stress curves tracking High-Pressure Compressor outlet pressure (P30) and Core Speed.

3. **Decision Intelligence and Maintenance Cost Simulator:**
   - Interactive sliders for breakdown cost, inspection cost, and alert thresholds.
   - Dynamic bar chart comparing financial exposure across Reactive (Run-to-Failure), Periodic (every 100 cycles), and Predictive Maintenance policies.
   - Sensitivity curve illustrating the trade-off between inspection frequency and breakdown prevention.

To launch the dashboard independently:
```bash
streamlit run src/dashboard/app.py
```
Access at: `http://localhost:8501`

---

## Illustrative Cost Model: Simulated Strategy Comparison

To estimate operational trade-offs, maintenance strategies were simulated across the 20 validation engines using baseline commercial aviation figures:
* **Cost of Unscheduled In-Flight Shutdown or AOG ($C_{\text{breakdown}}$):** \$150,000 (illustrative industry approximation)
* **Cost of Scheduled Depot Inspection or Overhaul ($C_{\text{inspection}}$):** \$15,000 (illustrative industry approximation)

$$\text{Total Maintenance Cost} = (N_{\text{inspections}} \times C_{\text{inspection}}) + (N_{\text{breakdowns}} \times C_{\text{breakdown}})$$

| Maintenance Policy | Policy Trigger Condition | Simulated Cost 20 Engines | Savings vs Reactive |
| :--- | :--- | :---: | :---: |
| **Run-to-Failure Reactive** | No preventative intervention | \$3,000,000 | Baseline |
| **Periodic Maintenance** | Fixed inspection every 100 cycles | \$525,000 | \$2,475,000 (82.5%) |
| **Predictive Maintenance Model** | Inspection alert when Predicted RUL ≤ 25 | **\$300,000** | **\$2,700,000 (90.0%)** |

*Disclaimer: The 90% cost reduction vs reactive failure is illustrative. It relies on the assumptions that every alert receives a timely inspection, zero false-negative failures occur, and inspections fully restore safe operation within the 20 simulated engines.*

---

## Prototype Limitations & Production Roadmap

This project is a functional engineering prototype designed to validate end-to-end data pipelines and low-latency inference. Key limitations include:
1. **Single Operating Regime FD001:** The FD001 dataset represents a single sea-level operating condition with one primary fault mode (High-Pressure Compressor degradation). Real-world flight envelopes represented in FD002 and FD004 involve multiple altitudes, Mach numbers, throttle settings, and dual fault modes.
2. **Deterministic Simulation:** Sensor inputs are generated from the C-MAPSS numerical simulation without atmospheric turbulence, intermittent telemetry drops, or transducer calibration drift.
3. **Fixed Piecewise RUL:** The 125-cycle early-life flat ceiling is a heuristic assumption that all engines share an identical early wear profile.

---

## Repository Structure

```text
├── .github/
│   └── workflows/
│       └── ci.yml
├── docker/
│   ├── Dockerfile.api
│   ├── Dockerfile.dashboard
│   └── docker-compose.yml
├── data/
│   ├── raw/
│   └── processed/
│       └── features_fd001.parquet
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
│   │   │   └── live_demo.html
│   │   └── main.py
│   ├── dashboard/
│   │   └── app.py
│   └── utils/
│       ├── download_data.py
│       └── evaluate_official_test.py
├── tests/
│   └── test_api.py
├── requirements.txt
└── README.md
```

---

## Quickstart Guide

### Option A: Complete Docker Orchestration Recommended
Spin up the entire five-tier ecosystem with a single command:
```bash
docker compose -f docker/docker-compose.yml up --build -d
```
All services become operational with preconfigured networks and healthchecks:
* **Streamlit Decision Dashboard:** `http://localhost:8501`
* **FastAPI Swagger Documentation:** `http://localhost:8000/docs`
* **WebSocket Live Telemetry Console:** `http://localhost:8000/live-demo`
* **Kafka UI Dashboard:** `http://localhost:8080`
* **PostgreSQL 16 Warehouse:** `localhost:5433` (Database: `turbofan_dw`)
* **Apache Kafka Broker:** `localhost:9092`

To shut down the cluster:
```bash
docker compose -f docker/docker-compose.yml down
```

---

### Option B: Local Development Setup

#### 1. Environment Setup
```bash
python -m venv .venv
```
Activate on Windows:
```bash
.venv\Scripts\activate
```
Activate on Linux or macOS:
```bash
source .venv/bin/activate
```
Install project dependencies:
```bash
pip install -r requirements.txt
```

#### 2. Start Core Infrastructure
```bash
docker compose -f docker/docker-compose.yml up -d postgres kafka kafka-ui
```

#### 3. Data Ingestion
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

#### 4. Data Transformation with dbt
```bash
cd src/transformation
dbt run
dbt test
cd ../..
python src/transformation/export_features.py
```

#### 5. Start Inference Server
```bash
uvicorn src.serving.main:app --host 0.0.0.0 --port 8000 --reload
```
* Interactive Swagger Documentation: `http://localhost:8000/docs`
* Real-Time WebSocket Telemetry Console: `http://localhost:8000/live-demo`

#### 6. Start Decision Intelligence Dashboard
```bash
streamlit run src/dashboard/app.py
```
Access at: `http://localhost:8501`

#### 7. Automated Testing
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
  "features": [-0.0007, -0.0004, 100.0, 641.82, ..., 0.0]
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
