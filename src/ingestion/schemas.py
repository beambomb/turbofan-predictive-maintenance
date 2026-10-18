"""
Data Contract & Pydantic Schemas for NASA Turbofan Telemetry Streaming.
"""

from datetime import datetime, timezone
from typing import List
from pydantic import BaseModel, Field, ConfigDict


# Helper lists untuk kemudahan mapping di Producer & Downstream Models
SETTING_COLUMNS: List[str] = ["setting_1", "setting_2", "setting_3"]
SENSOR_COLUMNS: List[str] = [f"s_{i}" for i in range(1, 22)]
RAW_DATA_COLUMNS: List[str] = ["engine_id", "cycle"] + SETTING_COLUMNS + SENSOR_COLUMNS


class TurbofanTelemetry(BaseModel):
    """
    Pydantic Schema yang merepresentasikan 1 event telemetry siklus turbofan C-MAPSS.
    """
    model_config = ConfigDict(extra="ignore")

    # Identifiers & Sequence
    engine_id: int = Field(..., ge=1, description="ID Unit mesin pesawat (1 - 100)")
    cycle: int = Field(..., ge=1, description="Siklus penerbangan operasional")

    # Operational Settings
    setting_1: float = Field(..., description="Operational setting 1 (Altitude/Mach)")
    setting_2: float = Field(..., description="Operational setting 2 (Throttle Resolver Angle)")
    setting_3: float = Field(..., description="Operational setting 3")

    # 21 Sensor Measurements
    s_1: float = Field(..., description="Total temperature at fan inlet (°R)")
    s_2: float = Field(..., description="Total temperature at LPC outlet (°R)")
    s_3: float = Field(..., description="Total temperature at HPC outlet (°R)")
    s_4: float = Field(..., description="Total temperature at LPT outlet (°R)")
    s_5: float = Field(..., description="Pressure at fan inlet (psia)")
    s_6: float = Field(..., description="Total pressure in bypass-duct (psia)")
    s_7: float = Field(..., description="Total pressure at HPC outlet (psia)")
    s_8: float = Field(..., description="Physical fan speed (rpm)")
    s_9: float = Field(..., description="Physical core speed (rpm)")
    s_10: float = Field(..., description="Engine pressure ratio (P50/P2)")
    s_11: float = Field(..., description="Static pressure at HPC outlet (psia)")
    s_12: float = Field(..., description="Ratio of fuel flow to Ps30 (pps/psia)")
    s_13: float = Field(..., description="Corrected fan speed (rpm)")
    s_14: float = Field(..., description="Corrected core speed (rpm)")
    s_15: float = Field(..., description="Bypass Ratio")
    s_16: float = Field(..., description="Burner fuel-air ratio")
    s_17: float = Field(..., description="Bleed Enthalpy")
    s_18: float = Field(..., description="Required fan speed")
    s_19: float = Field(..., description="Required fan conversion speed")
    s_20: float = Field(..., description="High-pressure turbines coolant bleed (lbm/s)")
    s_21: float = Field(..., description="Low-pressure turbines coolant bleed (lbm/s)")

    # Event Metadata
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Waktu event streaming dihasilkan (UTC)"
    )
