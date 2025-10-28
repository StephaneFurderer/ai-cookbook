"""
Traveler risk module for calculating airport passenger volumes with seasonality modeling.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
from geopy.distance import geodesic

from .config import MAJOR_AIRPORTS

logger = logging.getLogger(__name__)

class TravelerRiskCalculator:
    """Calculates airport traveler volumes with seasonality and holiday modeling."""
    
    def __init__(self):
        self.airport_data = self._load_airport_data()
        self.seasonality_factors = self._initialize_seasonality_factors()
        self.holiday_multipliers = self._initialize_holiday_multipliers()
        self.dow_multipliers = self._initialize_dow_multipliers()
    
    def _load_airport_data(self) -> pd.DataFrame:
        """Load airport data from config."""
        airports = []
        for code, info in MAJOR_AIRPORTS.items():
            airports.append({
                'airport_code': code,
                'name': info['name'],
                'lat': info['lat'],
                'lon': info['lon'],
                'baseline_capacity': info['daily_passengers'],
                'region': self._determine_region(info['lat'], info['lon'])
            })
        
        return pd.DataFrame(airports)
    
    def _determine_region(self, lat: float, lon: float) -> str:
        """Determine geographic region for an airport."""
        if 10 <= lat <= 25 and -85 <= lon <= -60:
            return 'Caribbean'
        elif 25 <= lat <= 35 and -85 <= lon <= -75:
            return 'Florida'
        elif 30 <= lat <= 45 and -85 <= lon <= -65:
            return 'US_East_Coast'
        elif 25 <= lat <= 35 and -100 <= lon <= -85:
            return 'Gulf_Coast'
        elif 30 <= lat <= 45 and -65 <= lon <= -40:
            return 'Northeast'
        else:
            return 'Other'
    
    def _initialize_seasonality_factors(self) -> Dict[str, Dict[int, float]]:
        """Initialize monthly seasonality factors by region."""
        return {
            'Caribbean': {
                1: 1.5, 2: 1.5, 3: 1.3, 4: 1.1, 5: 0.9, 6: 0.7,
                7: 0.7, 8: 0.7, 9: 0.7, 10: 0.8, 11: 1.0, 12: 1.4
            },
            'Florida': {
                1: 1.2, 2: 1.2, 3: 1.4, 4: 1.1, 5: 0.9, 6: 0.8,
                7: 0.8, 8: 0.8, 9: 0.8, 10: 0.9, 11: 1.0, 12: 1.1
            },
            'US_East_Coast': {
                1: 0.9, 2: 0.9, 3: 1.1, 4: 1.0, 5: 1.0, 6: 1.0,
                7: 1.0, 8: 1.0, 9: 0.9, 10: 1.0, 11: 1.0, 12: 1.0
            },
            'Gulf_Coast': {
                1: 0.9, 2: 0.9, 3: 1.1, 4: 1.0, 5: 0.9, 6: 0.8,
                7: 0.8, 8: 0.8, 9: 0.8, 10: 0.9, 11: 1.0, 12: 1.0
            },
            'Northeast': {
                1: 0.8, 2: 0.8, 3: 1.0, 4: 1.0, 5: 1.0, 6: 1.0,
                7: 1.0, 8: 1.0, 9: 1.0, 10: 1.0, 11: 1.0, 12: 1.0
            },
            'Other': {
                1: 1.0, 2: 1.0, 3: 1.0, 4: 1.0, 5: 1.0, 6: 1.0,
                7: 1.0, 8: 1.0, 9: 1.0, 10: 1.0, 11: 1.0, 12: 1.0
            }
        }
    
    def _initialize_holiday_multipliers(self) -> Dict[str, float]:
        """Initialize holiday multipliers."""
        return {
            'thanksgiving_week': 1.8,
            'christmas_week': 2.0,
            'spring_break': 1.4,
            'summer_vacation': 1.2,
            'new_years': 1.3,
            'memorial_day': 1.1,
            'independence_day': 1.1,
            'labor_day': 1.1,
            'default': 1.0
        }
    
    def _initialize_dow_multipliers(self) -> Dict[int, float]:
        """Initialize day-of-week multipliers."""
        return {
            0: 0.9,  # Monday
            1: 0.9,  # Tuesday
            2: 0.9,  # Wednesday
            3: 1.0,  # Thursday
            4: 1.2,  # Friday
            5: 1.2,  # Saturday
            6: 1.2   # Sunday
        }
    
    def _is_holiday_period(self, date: datetime) -> str:
        """Check if date falls within a holiday period."""
        month = date.month
        day = date.day
        year = date.year
        
        # Thanksgiving week (4th Thursday of November)
        if month == 11:
            # Find 4th Thursday
            first_thursday = 1
            while datetime(year, 11, first_thursday).weekday() != 3:
                first_thursday += 1
            fourth_thursday = first_thursday + 21
            if fourth_thursday <= day <= fourth_thursday + 6:
                return 'thanksgiving_week'
        
        # Christmas week (Dec 20-31)
        if month == 12 and day >= 20:
            return 'christmas_week'
        
        # New Year's week (Dec 30 - Jan 5)
        if (month == 12 and day >= 30) or (month == 1 and day <= 5):
            return 'new_years'
        
        # Spring break (March 15 - April 15)
        if month == 3 and day >= 15:
            return 'spring_break'
        if month == 4 and day <= 15:
            return 'spring_break'
        
        # Summer vacation (June 15 - August 15)
        if month == 6 and day >= 15:
            return 'summer_vacation'
        if month == 7:
            return 'summer_vacation'
        if month == 8 and day <= 15:
            return 'summer_vacation'
        
        # Memorial Day (last Monday of May)
        if month == 5:
            last_monday = 29
            while datetime(year, 5, last_monday).weekday() != 0:
                last_monday -= 1
            if day >= last_monday - 2 and day <= last_monday + 2:
                return 'memorial_day'
        
        # Independence Day (July 4)
        if month == 7 and day == 4:
            return 'independence_day'
        
        # Labor Day (first Monday of September)
        if month == 9:
            first_monday = 1
            while datetime(year, 9, first_monday).weekday() != 0:
                first_monday += 1
            if day >= first_monday - 2 and day <= first_monday + 2:
                return 'labor_day'
        
        return 'default'
    
    def get_seasonality_factor(self, date: datetime, airport_code: str) -> float:
        """Get seasonality factor for a specific airport and date."""
        airport = self.airport_data[self.airport_data['airport_code'] == airport_code]
        if airport.empty:
            return 1.0
        
        region = airport.iloc[0]['region']
        month = date.month
        
        return self.seasonality_factors.get(region, {}).get(month, 1.0)
    
    def get_holiday_multiplier(self, date: datetime) -> float:
        """Get holiday multiplier for a specific date."""
        holiday = self._is_holiday_period(date)
        return self.holiday_multipliers.get(holiday, 1.0)
    
    def get_dow_multiplier(self, date: datetime) -> float:
        """Get day-of-week multiplier for a specific date."""
        dow = date.weekday()
        return self.dow_multipliers.get(dow, 1.0)
    
    def calculate_daily_travelers(self, airport_code: str, date: datetime) -> float:
        """Calculate expected daily travelers for an airport on a specific date."""
        airport = self.airport_data[self.airport_data['airport_code'] == airport_code]
        if airport.empty:
            return 0.0
        
        baseline_capacity = airport.iloc[0]['baseline_capacity']
        
        # Apply all multipliers
        seasonal_factor = self.get_seasonality_factor(date, airport_code)
        holiday_multiplier = self.get_holiday_multiplier(date)
        dow_multiplier = self.get_dow_multiplier(date)
        
        daily_travelers = baseline_capacity * seasonal_factor * holiday_multiplier * dow_multiplier
        
        return max(0, daily_travelers)  # Ensure non-negative
    
    def get_travelers_forecast(self, airport_code: str, start_date: datetime, days: int = 14) -> pd.DataFrame:
        """Get traveler forecast for an airport over a date range."""
        dates = pd.date_range(start=start_date, periods=days, freq='D')
        
        forecast_data = []
        for date in dates:
            travelers = self.calculate_daily_travelers(airport_code, date)
            forecast_data.append({
                'date': date,
                'airport_code': airport_code,
                'expected_travelers': travelers,
                'seasonal_factor': self.get_seasonality_factor(date, airport_code),
                'holiday_multiplier': self.get_holiday_multiplier(date),
                'dow_multiplier': self.get_dow_multiplier(date)
            })
        
        return pd.DataFrame(forecast_data)
    
    def get_all_airports_forecast(self, start_date: datetime, days: int = 14) -> pd.DataFrame:
        """Get traveler forecast for all airports over a date range."""
        all_forecasts = []
        
        for _, airport in self.airport_data.iterrows():
            forecast = self.get_travelers_forecast(airport['airport_code'], start_date, days)
            all_forecasts.append(forecast)
        
        return pd.concat(all_forecasts, ignore_index=True)
    
    def calculate_travelers_at_risk(self, airport_coords: Tuple[float, float], 
                                  hurricane_track: List[Tuple[float, float, datetime]], 
                                  forecast_dates: List[datetime]) -> Dict[datetime, float]:
        """Calculate travelers at risk for an airport based on hurricane proximity."""
        airport_lat, airport_lon = airport_coords
        risk_by_date = {}
        
        # Create a mapping of hurricane positions by date
        hurricane_by_date = {}
        for lat, lon, time in hurricane_track:
            date_key = time.date()
            if date_key not in hurricane_by_date:
                hurricane_by_date[date_key] = []
            hurricane_by_date[date_key].append((lat, lon))
        
        for date in forecast_dates:
            date_key = date.date()
            travelers_at_risk = 0.0
            
            if date_key in hurricane_by_date:
                # Check if airport is within 100 miles of any hurricane position on this date
                for hurr_lat, hurr_lon in hurricane_by_date[date_key]:
                    distance_km = geodesic((airport_lat, airport_lon), (hurr_lat, hurr_lon)).kilometers
                    if distance_km <= 160.9:  # 100 miles = 160.9 km
                        # Find airport code for this location
                        airport_code = self._get_airport_code_by_coords(airport_lat, airport_lon)
                        if airport_code:
                            travelers_at_risk = self.calculate_daily_travelers(airport_code, date)
                        break  # Airport is at risk, no need to check other positions
            
            risk_by_date[date] = travelers_at_risk
        
        return risk_by_date
    
    def _get_airport_code_by_coords(self, lat: float, lon: float, tolerance: float = 0.01) -> Optional[str]:
        """Get airport code by coordinates with tolerance."""
        for _, airport in self.airport_data.iterrows():
            if (abs(airport['lat'] - lat) <= tolerance and 
                abs(airport['lon'] - lon) <= tolerance):
                return airport['airport_code']
        return None
    
    def get_airport_summary(self, date: datetime) -> pd.DataFrame:
        """Get summary of all airports with expected travelers for a specific date."""
        summary_data = []
        
        for _, airport in self.airport_data.iterrows():
            travelers = self.calculate_daily_travelers(airport['airport_code'], date)
            summary_data.append({
                'airport_code': airport['airport_code'],
                'name': airport['name'],
                'lat': airport['lat'],
                'lon': airport['lon'],
                'region': airport['region'],
                'baseline_capacity': airport['baseline_capacity'],
                'expected_travelers': travelers,
                'seasonal_factor': self.get_seasonality_factor(date, airport['airport_code']),
                'holiday_multiplier': self.get_holiday_multiplier(date),
                'dow_multiplier': self.get_dow_multiplier(date)
            })
        
        return pd.DataFrame(summary_data)
    
    def get_regional_summary(self, date: datetime) -> pd.DataFrame:
        """Get regional summary of expected travelers."""
        summary = self.get_airport_summary(date)
        regional = summary.groupby('region').agg({
            'expected_travelers': 'sum',
            'airport_code': 'count'
        }).reset_index()
        regional.columns = ['region', 'total_travelers', 'airport_count']
        
        return regional
