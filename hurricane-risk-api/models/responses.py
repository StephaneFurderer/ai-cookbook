"""Response models for Hurricane Risk API"""
from pydantic import BaseModel
from typing import List


class AirportRisk(BaseModel):
    """Airport risk information."""
    airport_code: str
    airport_name: str
    travelers_at_risk: int
    distance_to_hurricane_km: float
    risk_level: str  # "high", "medium", "low"


class DailyRiskProfile(BaseModel):
    """Daily risk profile for a specific date."""
    date: str
    total_travelers_at_risk: int
    airports_affected: int
    airports_at_risk: List[AirportRisk]
    active_hurricanes: int


class RiskAnalysisResponse(BaseModel):
    """Response for risk analysis."""
    meta: dict
    daily_risk: List[DailyRiskProfile]
