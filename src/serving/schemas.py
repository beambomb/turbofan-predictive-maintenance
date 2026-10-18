from typing import List, Dict, Any
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    active_model: str
    app_version: str


class PredictionRequest(BaseModel):
    engine_id: int = Field(..., ge=1, json_schema_extra={"example": 1})
    features: List[float] = Field(
        ...,
        description="Daftar 38 nilai fitur sensor mesin saat ini"
    )


class PredictionResponse(BaseModel):
    engine_id: int
    predicted_rul: float
    health_status: str
    recommended_action: str
    inference_time_ms: float
    model_used: str


class StreamPredictionMessage(BaseModel):
    engine_id: int
    cycle: int
    total_cycles: int
    predicted_rul: float
    health_status: str
    recommended_action: str
    inference_time_ms: float
    model_used: str
    sensors: Dict[str, Any]
