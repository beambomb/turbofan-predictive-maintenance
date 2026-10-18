from fastapi import FastAPI
from src.serving.config import settings
from src.serving.routers.prediction_router import router as api_router
from src.serving.routers.websocket_router import router as ws_router

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Layanan Prediksi Sisa Umur Mesin Pesawat Berbasis Arsitektur Berlapis"
)

app.include_router(api_router)
app.include_router(ws_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.serving.main:app", host=settings.host, port=settings.port, reload=True)
