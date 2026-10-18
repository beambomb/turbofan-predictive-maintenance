from fastapi import APIRouter, HTTPException, status
from src.serving.schemas import HealthResponse, PredictionRequest, PredictionResponse
from src.serving.services.prediction_service import prediction_service
from src.serving.core.model_loader import model_engine
from src.serving.config import settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def get_health():
    return HealthResponse(
        status="healthy",
        active_model=model_engine.model_type,
        app_version=settings.app_version
    )


@router.post("/predict-rul", response_model=PredictionResponse)
def predict_engine_rul(request: PredictionRequest):
    if len(request.features) != 38:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Jumlah fitur harus tepat 38 angka, diterima {len(request.features)}"
        )
    return prediction_service.process_prediction(request)
