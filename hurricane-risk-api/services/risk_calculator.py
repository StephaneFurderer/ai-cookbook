"""
Risk calculation service for hurricane impact analysis
"""
from datetime import datetime, timedelta
from typing import Dict, List, Any
from geopy.distance import geodesic
import pandas as pd

from core.airports import MAJOR_AIRPORTS
from core.config import settings


class RiskCalculator:
    """Calculate risk exposure from hurricane impacts."""
    
    def __init__(self):
        self.risk_radius_km = settings.RISK_RADIUS_KM
        self.airport_data = self._load_airport_data()
    
    def _load_airport_data(self) -> pd.DataFrame:
        """Load airport data from configuration."""
        airports = []
        for code, info in MAJOR_AIRPORTS.items():
            airports.append({
                'airport_code': code,
                'name': info['name'],
                'lat': info['lat'],
                'lon': info['lon'],
                'baseline_capacity': info['daily_passengers']
            })
        return pd.DataFrame(airports)
    
    def _determine_risk_level(self, distance_km: float) -> str:
        """Determine risk level based on distance from hurricane."""
        if distance_km < 50:
            return "high"
        elif distance_km < 100:
            return "medium"
        else:
            return "low"
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in kilometers."""
        return geodesic((lat1, lon1), (lat2, lon2)).kilometers
    
    def _parse_hurricane_records(self, records: List[Dict]) -> List[Dict[str, Any]]:
        """Parse hurricane records from weather-lab-data-api response."""
        hurricanes = []
        for record in records:
            try:
                hurr_data = {
                    'track_id': record.get('track_id'),
                    'valid_time': record.get('valid_time'),
                    'lat': float(record.get('lat', 0)),
                    'lon': float(record.get('lon', 0)),
                    'wind_speed': float(record.get('maximum_sustained_wind_speed_knots', 0))
                }
                hurricanes.append(hurr_data)
            except (ValueError, TypeError) as e:
                # Skip invalid records
                continue
        return hurricanes
    
    def calculate_daily_travelers(self, airport_code: str, date: datetime) -> int:
        """Calculate expected daily travelers for an airport on a specific date."""
        airport = self.airport_data[self.airport_data['airport_code'] == airport_code]
        if airport.empty:
            return 0
        
        baseline_capacity = airport.iloc[0]['baseline_capacity']
        
        # Simple seasonality based on month (can be enhanced later)
        month = date.month
        
        # Spring/summer multipliers (rough approximation)
        if month in [3, 4, 5, 6, 7, 8]:
            multiplier = 1.2  # Peak travel season
        elif month in [11, 12, 1]:
            multiplier = 1.1  # Holiday season
        else:
            multiplier = 1.0  # Base
        
        # Day of week multiplier
        dow = date.weekday()
        if dow in [4, 5, 6]:  # Friday, Saturday, Sunday
            dow_multiplier = 1.2
        elif dow in [0, 1]:  # Monday, Tuesday
            dow_multiplier = 0.9
        else:
            dow_multiplier = 1.0
        
        daily_travelers = baseline_capacity * multiplier * dow_multiplier
        
        return int(max(0, daily_travelers))
    
    def calculate_risk_profile(self, hurricane_data: dict, start_date: str, days: int) -> Dict[str, Any]:
        """
        Calculate risk profile for a date range.
        
        Args:
            hurricane_data: Response from weather-lab-data-api with 'data' key
            start_date: Start date string in YYYY-MM-DD format
            days: Number of days to analyze
            
        Returns:
            Dictionary with risk analysis results
        """
        date_range = pd.date_range(start=start_date, periods=days, freq='D')
        daily_risk_profiles = []
        
        # Get daily data from hurricane_data
        data_by_date = hurricane_data.get('data', {})
        
        for date in date_range:
            date_str = date.strftime('%Y-%m-%d')
            
            # Get hurricane records for this date
            date_data = data_by_date.get(date_str, {})
            records = date_data.get('records', [])
            
            # Parse hurricane positions
            hurricanes = self._parse_hurricane_records(records)
            
            # Initialize daily profile
            airports_at_risk = []
            total_travelers_at_risk = 0
            
            # Check each airport
            for _, airport in self.airport_data.iterrows():
                airport_code = airport['airport_code']
                airport_name = airport['name']
                airport_lat = airport['lat']
                airport_lon = airport['lon']
                
                # Find minimum distance to any hurricane
                min_distance = float('inf')
                
                for hurricane in hurricanes:
                    distance = self._calculate_distance(
                        airport_lat, airport_lon,
                        hurricane['lat'], hurricane['lon']
                    )
                    min_distance = min(min_distance, distance)
                
                # Check if airport is within risk radius
                if min_distance <= self.risk_radius_km:
                    # Calculate travelers at risk
                    travelers = self.calculate_daily_travelers(airport_code, date)
                    
                    airports_at_risk.append({
                        'airport_code': airport_code,
                        'airport_name': airport_name,
                        'travelers_at_risk': travelers,
                        'distance_to_hurricane_km': round(min_distance, 2),
                        'risk_level': self._determine_risk_level(min_distance)
                    })
                    
                    total_travelers_at_risk += travelers
            
            # Sort airports by travelers at risk (descending)
            airports_at_risk.sort(key=lambda x: x['travelers_at_risk'], reverse=True)
            
            daily_risk_profiles.append({
                'date': date_str,
                'total_travelers_at_risk': total_travelers_at_risk,
                'airports_affected': len(airports_at_risk),
                'airports_at_risk': airports_at_risk,
                'active_hurricanes': len(hurricanes)
            })
        
        return {
            'daily_risk': daily_risk_profiles
        }

