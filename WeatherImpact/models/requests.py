"""
Request models for Hurricane Risk API
"""
from pydantic import BaseModel, Field


class RiskAnalysisRequest(BaseModel):
    """Request for single date risk analysis."""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    days: int = Field(default=1, description="Number of days to analyze")


class RiskAnalysisRangeRequest(BaseModel):
    """Request for date range risk analysis."""
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    days: int = Field(..., ge=1, le=30, description="Number of days to forecast (1-30)")

