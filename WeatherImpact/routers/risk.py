"""
Risk calculation API endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timedelta
from typing import Dict, Any

from models.requests import RiskAnalysisRequest, RiskAnalysisRangeRequest
from models.responses import RiskAnalysisResponse, DailyRiskProfile, AirportRisk
from services.data_client import WeatherLabClient
from services.risk_calculator import RiskCalculator
from core.config import settings

router = APIRouter()


async def get_weather_client() -> WeatherLabClient:
    """Dependency to get WeatherLab client."""
    client = WeatherLabClient(settings.WEATHER_LAB_API_URL)
    try:
        yield client
    finally:
        await client.close()


@router.get("/health")
async def health() -> Dict[str, str]:
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "hurricane-risk-api",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@router.post("/analyze", response_model=RiskAnalysisResponse)
async def analyze_risk(
    request: RiskAnalysisRequest,
    client: WeatherLabClient = Depends(get_weather_client)
) -> RiskAnalysisResponse:
    """
    Analyze risk for a single date.
    
    Args:
        request: Risk analysis request with date and days
        client: WeatherLab client dependency
        
    Returns:
        Risk analysis response with daily risk profiles
    """
    try:
        # Fetch hurricane data
        hurricane_data = await client.get_hurricane_data_range(
            request.date, 
            request.days
        )
        
        # Calculate risk profile
        calculator = RiskCalculator()
        result = calculator.calculate_risk_profile(
            hurricane_data,
            request.date,
            request.days
        )
        
        # Build response
        end_date = (datetime.strptime(request.date, '%Y-%m-%d') + 
                   timedelta(days=request.days-1)).strftime('%Y-%m-%d')
        
        response = RiskAnalysisResponse(
            meta={
                'start_date': request.date,
                'end_date': end_date,
                'total_days': request.days,
                'analysis_timestamp': datetime.utcnow().isoformat() + 'Z'
            },
            daily_risk=[
                DailyRiskProfile(**profile) for profile in result['daily_risk']
            ]
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-range", response_model=RiskAnalysisResponse)
async def analyze_risk_range(
    request: RiskAnalysisRangeRequest,
    client: WeatherLabClient = Depends(get_weather_client)
) -> RiskAnalysisResponse:
    """
    Analyze risk for a date range (forecast).
    
    Args:
        request: Risk analysis range request
        client: WeatherLab client dependency
        
    Returns:
        Risk analysis response with daily risk profiles
    """
    try:
        # Fetch hurricane data
        hurricane_data = await client.get_hurricane_data_range(
            request.start_date,
            request.days
        )
        
        # Calculate risk profile
        calculator = RiskCalculator()
        result = calculator.calculate_risk_profile(
            hurricane_data,
            request.start_date,
            request.days
        )
        
        # Build response
        end_date = (datetime.strptime(request.start_date, '%Y-%m-%d') + 
                   timedelta(days=request.days-1)).strftime('%Y-%m-%d')
        
        response = RiskAnalysisResponse(
            meta={
                'start_date': request.start_date,
                'end_date': end_date,
                'total_days': request.days,
                'analysis_timestamp': datetime.utcnow().isoformat() + 'Z'
            },
            daily_risk=[
                DailyRiskProfile(**profile) for profile in result['daily_risk']
            ]
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

