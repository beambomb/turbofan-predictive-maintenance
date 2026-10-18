from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseModel):
    app_name: str = "NASA Turbofan Predictive Maintenance API"
    app_version: str = "1.0.0"
    model_path_joblib: Path = BASE_DIR / "models" / "best_rul_model.joblib"
    model_path_onnx: Path = BASE_DIR / "models" / "best_rul_model.onnx"
    processed_data_path: Path = BASE_DIR / "data" / "processed" / "features_fd001.parquet"
    host: str = "0.0.0.0"
    port: int = 8000


settings = Settings()
