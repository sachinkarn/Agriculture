"""Request bodies (validated by Pydantic)."""
from typing import Literal, Optional

from pydantic import BaseModel, Field


class SoilIn(BaseModel):
    n: float = Field(240, ge=0, le=1000, description="Nitrogen, kg/ha")
    p: float = Field(14, ge=0, le=200, description="Phosphorus, kg/ha")
    k: float = Field(130, ge=0, le=1000, description="Potassium, kg/ha")
    ph: float = Field(6.4, ge=3, le=10, description="Soil pH")
    m: float = Field(45, ge=0, le=100, description="Soil moisture, %")


class IrrigationIn(BaseModel):
    crop: str = "Apple"
    soil_moisture: float = Field(..., ge=0, le=100)
    temperature: float = Field(31, ge=-10, le=60)
    humidity: float = Field(78, ge=0, le=100)
    rain_probability: float = Field(20, ge=0, le=100)
    diseased: bool = False


class RecommendIn(BaseModel):
    soil: SoilIn = SoilIn()
    water: Literal["L", "M", "H"] = "M"


class PlanIn(BaseModel):
    crop: str = "Apple"
    disease: Optional[str] = Field(None, description="None means the crop looks healthy")
    confidence: float = Field(0.9, ge=0, le=1)
    severity: Optional[str] = Field(None, description="Low | Medium | High")
    soil: SoilIn = SoilIn()
    # Weather: send values, or send latitude/longitude to fetch them, or send nothing for defaults.
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    rain_probability: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
