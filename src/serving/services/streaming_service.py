from typing import List, Dict, Any
import numpy as np
import pandas as pd
from src.serving.config import settings
from src.serving.core.model_loader import model_engine
from src.serving.services.prediction_service import prediction_service

FEATURE_COLUMNS = [
    "setting_1", "setting_2", "setting_3",
    "sensor_2_lpc_temp", "sensor_3_hpc_temp", "sensor_4_lpt_temp",
    "sensor_7_hpc_pressure", "sensor_8_fan_speed", "sensor_9_core_speed",
    "sensor_11_static_hpc_pressure", "sensor_12_fuel_flow_ratio",
    "sensor_13_corrected_fan_speed", "sensor_14_corrected_core_speed",
    "sensor_15_bypass_ratio", "sensor_17_bleed_enthalpy",
    "sensor_20_hpt_coolant_bleed", "sensor_21_lpt_coolant_bleed",
    "s2_drift_initial", "s3_drift_initial", "s4_drift_initial",
    "s7_drift_initial", "s11_drift_initial", "s12_drift_initial",
    "s2_roll_mean_5", "s3_roll_mean_5", "s4_roll_mean_5",
    "s7_roll_mean_5", "s8_roll_mean_5", "s9_roll_mean_5",
    "s11_roll_mean_5", "s12_roll_mean_5", "s15_roll_mean_5",
    "s2_roll_std_5", "s3_roll_std_5", "s4_roll_std_5",
    "s7_roll_std_5", "s11_roll_std_5", "s12_roll_std_5"
]


class StreamingService:
    def __init__(self):
        self._df = None
        self._load_data()

    def _load_data(self):
        if settings.processed_data_path.exists():
            self._df = pd.read_parquet(settings.processed_data_path)
        else:
            import psycopg2
            import os
            conn = psycopg2.connect(
                host=os.getenv("POSTGRES_HOST", "localhost"),
                port=int(os.getenv("POSTGRES_PORT", "5433")),
                dbname=os.getenv("POSTGRES_DB", "turbofan_dw"),
                user=os.getenv("POSTGRES_USER", "postgres"),
                password=os.getenv("POSTGRES_PASSWORD", "postgres")
            )
            self._df = pd.read_sql_query("SELECT * FROM analytics.fct_turbofan_features ORDER BY engine_id, cycle;", conn)
            conn.close()

    def get_available_engines(self) -> List[int]:
        if self._df is None:
            return []
        return sorted([int(e) for e in self._df["engine_id"].unique()])

    def get_engine_cycles(self, engine_id: int) -> List[Dict[str, Any]]:
        if self._df is None:
            self._load_data()

        subset = self._df[self._df["engine_id"] == engine_id].sort_values("cycle")
        if subset.empty:
            raise ValueError(f"Mesin ID {engine_id} tidak ditemukan")

        total_cycles = len(subset)
        messages = []

        for _, row in subset.iterrows():
            msg = self.process_cycle(row, total_cycles)
            messages.append(msg)

        return messages

    def process_cycle(self, row: pd.Series, total_cycles: int) -> Dict[str, Any]:
        features_np = row[FEATURE_COLUMNS].values.astype(np.float32)
        predicted_rul, latency_ms = model_engine.predict(features_np)
        health_status, action = prediction_service.determine_health_action(predicted_rul)

        sensors = {
            "lpc_temp": round(float(row["sensor_2_lpc_temp"]), 2),
            "hpc_temp": round(float(row["sensor_3_hpc_temp"]), 2),
            "lpt_temp": round(float(row["sensor_4_lpt_temp"]), 2),
            "hpc_pressure": round(float(row["sensor_7_hpc_pressure"]), 2),
            "core_speed": round(float(row["sensor_9_core_speed"]), 2),
            "fuel_flow": round(float(row["sensor_12_fuel_flow_ratio"]), 4),
            "bypass_ratio": round(float(row["sensor_15_bypass_ratio"]), 4),
            "bleed_enthalpy": round(float(row["sensor_17_bleed_enthalpy"]), 2)
        }

        return {
            "engine_id": int(row["engine_id"]),
            "cycle": int(row["cycle"]),
            "total_cycles": int(total_cycles),
            "predicted_rul": round(predicted_rul, 2),
            "health_status": health_status,
            "recommended_action": action,
            "inference_time_ms": round(latency_ms, 2),
            "model_used": model_engine.model_type,
            "sensors": sensors
        }


streaming_service = StreamingService()
