# NASA Turbofan Predictive Maintenance & Real-Time RUL Estimation Platform

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Apache Kafka](https://img.shields.io/badge/Apache_Kafka-3.8_KRaft-231F20?style=for-the-badge&logo=apachekafka&logoColor=white)](https://kafka.apache.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![dbt](https://img.shields.io/badge/dbt-1.8-FF694B?style=for-the-badge&logo=dbt&logoColor=white)](https://getdbt.com)
[![XGBoost](https://img.shields.io/badge/XGBoost-Champion-EB7532?style=for-the-badge)](https://xgboost.ai)
[![Pytest](https://img.shields.io/badge/Tests-6%2F6_Passing-brightgreen?style=for-the-badge&logo=pytest&logoColor=white)](https://pytest.org)

Platform Predictive Maintenance end-to-end kelas industri untuk memantau degradasi mesin turbofan pesawat terbang dan memprediksi Remaining Useful Life secara real-time berdasarkan dataset NASA C-MAPSS FD001.

---

## Arsitektur Sistem

```text
[ SIMULASI TRANSMISI PESAWAT ]
  Telemetry Replay (Producer)
           │
           ▼ (Streaming Telemetri Sensor per Siklus)
  Apache Kafka (KRaft Single-Node Mode)
           │
           ▼ (Consumer Batch Ingestion)
  PostgreSQL 16 (Time-Series Data Warehouse)
           │
           ▼ (dbt: Pruning 6 Flat Sensors + Rolling Mean/Std 5 + Wear Drift)
  Feature Store (Parquet: 38 Fitur Siap Latih)
           │
           ├───────────────────────────────────────────────┐
           ▼                                               ▼
[ MACHINE LEARNING TOURNAMENT ]                   [ SERVING & STREAMING ]
  1. XGBoost (Tuned - Juara)                       FastAPI (Layered Architecture)
  2. LightGBM (Tuned)                              - REST API (/predict-rul)
  3. PyTorch CNN-BiGRU                             - WebSocket (/ws/telemetry/{id})
  4. Attention-BiGRU (Asymmetric)                  - Live Interactive Cockpit Demo
```

---

## Hasil Benchmark Model

Turnamen model dilakukan pada 100 mesin turbofan (FD001) dengan metrik evaluasi RMSE, MAE, dan Asymmetric NASA Scoring Function.

| Model | RMSE | MAE | NASA Score | Status |
| :--- | :---: | :---: | :---: | :---: |
| **XGBoost (Tuned)** | **14.39** | **10.92** | **15,235** | **Juara Turnamen** |
| LightGBM (Tuned) | 14.46 | 10.92 | 15,908 | Runner-up |
| PyTorch CNN-BiGRU | 15.61 | 10.96 | 15,591 | Deep Learning Terbaik |
| Attention-BiGRU | 17.71 | 12.42 | 24,720 | Asymmetric Loss |

### Kesimpulan Rekayasa Fitur
Model tree-based (XGBoost) mengungguli model sekuensial deep learning karena dbt berhasil mengekstraksi sinyal fisik degradasi mesin melalui fitur rolling statistics dan initial wear drift pada 14 sensor kritis.

---

## Struktur Repositori

```text
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

## Panduan Menjalankan Sistem

### 1. Persiapan Lingkungan
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Menjalankan Infrastruktur Docker
```bash
docker compose -f docker/docker-compose.yml up -d
```
* PostgreSQL: `localhost:5433` (Database: `turbofan_dw`)
* Apache Kafka: `localhost:9092`
* Kafka-UI: `http://localhost:8080`

### 3. Mengunduh Dataset NASA
```bash
python src/utils/download_data.py
```

### 4. Streaming Ingestion via Kafka
Jalankan consumer di terminal pertama:
```bash
python -m src.ingestion.consumer --batch-size 500
```
Jalankan producer di terminal kedua untuk memutar 20.631 baris telemetri:
```bash
python -m src.ingestion.producer --delay-ms 1
```

### 5. Transformasi Data dengan dbt
```bash
cd src/transformation
dbt run
dbt test
cd ../..
python src/transformation/export_features.py
```

### 6. Menjalankan Server FastAPI
```bash
uvicorn src.serving.main:app --host 0.0.0.0 --port 8000 --reload
```
Akses layanan melalui browser:
* Dokumentasi Swagger UI: `http://localhost:8000/docs`
* Antarmuka Live Telemetry Stream: `http://localhost:8000/live-demo`

### 7. Menjalankan Pengujian Otomatis
```bash
pytest -v tests/
```

---

## Spesifikasi API dan WebSocket

### REST Endpoint

#### Pengecekan Kesehatan Server
```http
GET /health
```
Respon:
```json
{
  "status": "healthy",
  "active_model": "XGBoost",
  "app_version": "1.0.0"
}
```

#### Prediksi RUL On-Demand
```http
POST /predict-rul
Content-Type: application/json

{
  "engine_id": 1,
  "features": [-0.0007, -0.0004, 100.0, ..., 0.0]
}
```
Respon:
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

### WebSocket Streaming Telemetry
```text
ws://localhost:8000/ws/telemetry/{engine_id}?interval=0.5&loop=true&start_cycle=1
```
Format frame pesan JSON yang dipancarkan secara kontinu:
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

---

## Klasifikasi Status Perawatan dan Analisis Biaya

Sistem mengklasifikasikan sisa umur mesin ke dalam 3 zona operasional:

| Zona Status | Ambang Batas RUL | Rekomendasi Tindakan |
| :--- | :---: | :--- |
| **HEALTHY** | RUL > 75 siklus | Operasi normal, tidak membutuhkan tindakan perawatan |
| **WARNING** | 25 ≤ RUL ≤ 75 siklus | Rencanakan jadwal perawatan dalam 15 siklus ke depan |
| **CRITICAL** | RUL < 25 siklus | Lakukan pemeriksaan darurat dan larang pesawat terbang |

### Optimasi Biaya Operasional
Model prediktif meminimalkan fungsi biaya total perawatan maskapai:
$$\text{Total Cost} = (N_{\text{inspeksi}} \times C_{\text{inspeksi}}) + (N_{\text{jebol}} \times C_{\text{breakdown}})$$
Biaya kerusakan mesin mendadak di udara jauh lebih mahal daripada biaya inspeksi terjadwal, sehingga deteksi dini degradasi sensor memberikan efisiensi biaya operasional yang signifikan bagi maskapai penerbangan.
