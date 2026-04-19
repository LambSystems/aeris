from pydantic import BaseModel, Field

from app.schemas import BoundingBox


class YOLODetection(BaseModel):
    object_class: str
    confidence: float = Field(ge=0.0, le=1.0)
    bbox: BoundingBox | None = None
    frame_id: str = "frame_001"
    timestamp: str


class CASTNETReading(BaseModel):
    site_id: str
    location: str
    ozone_ppb: float
    sulfate_ug_m3: float
    nitrate_ug_m3: float
    co_ppb: float
    measurement_date: str


class DetectionRequest(BaseModel):
    detection: YOLODetection


class SustainabilityAdvice(BaseModel):
    object_detected: str
    confidence: float
    context: str
    action: str
