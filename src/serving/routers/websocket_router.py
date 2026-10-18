import asyncio
from typing import List
from pathlib import Path
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from fastapi.responses import HTMLResponse
from src.serving.services.streaming_service import streaming_service

router = APIRouter()
HTML_PATH = Path(__file__).resolve().parent.parent / "static" / "live_demo.html"


@router.get("/ws-engines", response_model=List[int])
def get_available_engines():
    return streaming_service.get_available_engines()


@router.websocket("/ws/telemetry/{engine_id}")
async def stream_engine_telemetry(
    websocket: WebSocket,
    engine_id: int,
    interval: float = Query(0.5, ge=0.001, le=10.0),
    loop: bool = Query(False),
    start_cycle: int = Query(1, ge=1)
):
    await websocket.accept()

    try:
        cycles = streaming_service.get_engine_cycles(engine_id)
        if start_cycle > 1:
            cycles = [c for c in cycles if c["cycle"] >= start_cycle]
            if not cycles:
                cycles = streaming_service.get_engine_cycles(engine_id)
    except ValueError as e:
        await websocket.send_json({"error": str(e)})
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        while True:
            for message in cycles:
                await websocket.send_json(message)
                await asyncio.sleep(interval)

            if not loop:
                await websocket.send_json({
                    "event": "completed",
                    "engine_id": engine_id,
                    "message": f"Siklus terbang mesin {engine_id} telah mencapai akhir umur operasi"
                })
                break
    except WebSocketDisconnect:
        pass


@router.get("/live-demo", response_class=HTMLResponse)
def get_live_demo():
    return HTMLResponse(content=HTML_PATH.read_text(encoding="utf-8"))
