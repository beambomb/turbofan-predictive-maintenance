from typing import Tuple
import numpy as np
from src.serving.core.model_loader import model_engine
from src.serving.schemas import PredictionRequest, PredictionResponse


class PredictionService:
    def determine_health_action(self, rul: float) -> Tuple[str, str]:
        if rul > 75.0:
            return "HEALTHY", "Operasi normal, tidak butuh tindakan perawatan"
        elif 25.0 <= rul <= 75.0:
            return "WARNING", "Rencanakan jadwal inspeksi dalam 15 siklus ke depan"
        else:
            return "CRITICAL", "Lakukan pemeriksaan darurat segera dan larang pesawat terbang"

    def process_prediction(self, request: PredictionRequest) -> PredictionResponse:
        features_np = np.array(request.features, dtype=np.float32)
        predicted_rul, latency_ms = model_engine.predict(features_np)
        health_status, action = self.determine_health_action(predicted_rul)

        return PredictionResponse(
            engine_id=request.engine_id,
            predicted_rul=round(predicted_rul, 2),
            health_status=health_status,
            recommended_action=action,
            inference_time_ms=round(latency_ms, 2),
            model_used=model_engine.model_type
        )


prediction_service = PredictionService()
