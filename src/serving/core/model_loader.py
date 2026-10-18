import time
from typing import Tuple
import numpy as np
import joblib
import onnxruntime as ort
from src.serving.config import settings


class ModelEngine:
    def __init__(self):
        self.model = None
        self.model_type = None
        self.load_model()

    def load_model(self):
        if settings.model_path_joblib.exists():
            self.model = joblib.load(settings.model_path_joblib)
            self.model_type = "XGBoost"
        elif settings.model_path_onnx.exists():
            self.model = ort.InferenceSession(str(settings.model_path_onnx), providers=["CPUExecutionProvider"])
            self.model_type = "PyTorch ONNX"
        else:
            raise FileNotFoundError("Tidak ada file model ditemukan di folder models/")

    def predict(self, feature_array: np.ndarray) -> Tuple[float, float]:
        start = time.perf_counter()

        if self.model_type == "XGBoost":
            if feature_array.ndim == 1:
                feature_array = feature_array.reshape(1, -1)
            raw_pred = float(self.model.predict(feature_array)[0])
        else:
            if feature_array.ndim == 1:
                feature_array = np.tile(feature_array, (30, 1))
            if feature_array.ndim == 2:
                feature_array = np.expand_dims(feature_array, axis=0)
            input_name = self.model.get_inputs()[0].name
            raw_out = self.model.run(None, {input_name: feature_array.astype(np.float32)})
            raw_pred = float(raw_out[0][0][0])

        elapsed_ms = (time.perf_counter() - start) * 1000.0
        clipped_rul = float(np.clip(raw_pred, 0.0, 125.0))
        return clipped_rul, elapsed_ms


model_engine = ModelEngine()
