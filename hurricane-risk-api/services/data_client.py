"""
Data client for fetching hurricane data from weather-lab-data-api
"""
import httpx
from typing import Dict, Any


class WeatherLabClient:
    """Client for interacting with weather-lab-data-api."""
    
    def __init__(self, base_url: str):
        """
        Initialize the WeatherLab client.
        
        Args:
            base_url: Base URL of the weather-lab-data-api
        """
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def get_hurricane_data(self, date: str) -> Dict[str, Any]:
        """
        Get hurricane data for a specific date.
        
        Args:
            date: Date in YYYY-MM-DD format
            
        Returns:
            Dictionary with 'meta' and 'records' keys
        """
        url = f"{self.base_url}/data"
        params = {"date": date}
        
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        
        return response.json()
    
    async def get_hurricane_data_range(self, start_date: str, days: int) -> Dict[str, Any]:
        """
        Get hurricane data for a date range.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            days: Number of days to fetch
            
        Returns:
            Dictionary with 'meta' and 'data' keys
        """
        url = f"{self.base_url}/data-range"
        params = {"start": start_date, "days": days}
        
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        
        return response.json()
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

