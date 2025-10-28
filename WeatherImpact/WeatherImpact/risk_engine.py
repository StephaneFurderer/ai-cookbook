"""
Risk calculation engine for determining traveler exposure from hurricane impacts.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
from geopy.distance import geodesic

from .traveler_risk import TravelerRiskCalculator
from .config import MAJOR_AIRPORTS

logger = logging.getLogger(__name__)

class RiskEngine:
    """Calculates traveler risk exposure from hurricane impacts."""
    
    def __init__(self):
        self.traveler_calculator = TravelerRiskCalculator()
        self.risk_radius_km = 160.9  # 100 miles in kilometers
    
    def calculate_risk_exposure(self, hurricane_analyses: Dict[str, Dict], 
                               date_range: List[datetime]) -> Dict[datetime, Dict]:
        """
        Calculate risk exposure for all airports over a date range.
        
        Args:
            hurricane_analyses: Dictionary of hurricane analyses from HurricaneAnalyzer
            date_range: List of dates to analyze
            
        Returns:
            Dictionary mapping date to risk exposure data
        """
        logger.info(f"Calculating risk exposure for {len(date_range)} dates and {len(hurricane_analyses)} hurricanes")
        
        risk_exposure = {}
        
        for date in date_range:
            date_key = date.date()
            daily_risk = {
                'date': date,
                'airports_at_risk': [],
                'total_travelers_at_risk': 0,
                'hurricane_impacts': {},
                'regional_breakdown': {}
            }
            
            # Check each hurricane for impacts on this date
            for track_id, analysis in hurricane_analyses.items():
                hurricane_impact = self._check_hurricane_impact_on_date(analysis, date)
                
                if hurricane_impact['airports_affected']:
                    daily_risk['hurricane_impacts'][track_id] = hurricane_impact
                    daily_risk['airports_at_risk'].extend(hurricane_impact['airports_affected'])
            
            # Remove duplicate airports (in case multiple hurricanes affect same airport)
            daily_risk['airports_at_risk'] = list(set(daily_risk['airports_at_risk']))
            
            # Calculate total travelers at risk
            for airport_code in daily_risk['airports_at_risk']:
                travelers = self.traveler_calculator.calculate_daily_travelers(airport_code, date)
                daily_risk['total_travelers_at_risk'] += travelers
            
            # Calculate regional breakdown
            daily_risk['regional_breakdown'] = self._calculate_regional_breakdown(
                daily_risk['airports_at_risk'], date
            )
            
            risk_exposure[date] = daily_risk
        
        return risk_exposure
    
    def _check_hurricane_impact_on_date(self, hurricane_analysis: Dict, date: datetime) -> Dict:
        """Check if a hurricane impacts any airports on a specific date."""
        impact_zones = hurricane_analysis['impact_zones']
        trajectory = hurricane_analysis['trajectory']
        
        impact_result = {
            'track_id': hurricane_analysis['track_id'],
            'airports_affected': [],
            'impact_details': []
        }
        
        # Get hurricane positions for this date
        hurricane_positions = self._get_hurricane_positions_for_date(trajectory, date)
        
        if not hurricane_positions:
            return impact_result
        
        # Check each airport against hurricane positions
        for airport_code, airport_info in MAJOR_AIRPORTS.items():
            airport_lat = airport_info['lat']
            airport_lon = airport_info['lon']
            
            for hurr_lat, hurr_lon in hurricane_positions:
                distance_km = geodesic((airport_lat, airport_lon), (hurr_lat, hurr_lon)).kilometers
                
                if distance_km <= self.risk_radius_km:
                    impact_result['airports_affected'].append(airport_code)
                    impact_result['impact_details'].append({
                        'airport_code': airport_code,
                        'airport_name': airport_info['name'],
                        'distance_km': distance_km,
                        'hurricane_position': (hurr_lat, hurr_lon)
                    })
                    break  # Airport is affected, no need to check other positions
        
        return impact_result
    
    def _get_hurricane_positions_for_date(self, trajectory: Dict, date: datetime) -> List[Tuple[float, float]]:
        """Get hurricane positions for a specific date."""
        positions = []
        
        if not trajectory or 'intensity_history' not in trajectory:
            return positions
        
        date_key = date.date()
        
        for point in trajectory['intensity_history']:
            point_date = point['time'].date()
            if point_date == date_key:
                positions.append((point['lat'], point['lon']))
        
        return positions
    
    def _calculate_regional_breakdown(self, airports_at_risk: List[str], date: datetime) -> Dict[str, Dict]:
        """Calculate regional breakdown of risk exposure."""
        regional_breakdown = {}
        
        for airport_code in airports_at_risk:
            if airport_code in MAJOR_AIRPORTS:
                airport_info = MAJOR_AIRPORTS[airport_code]
                region = self._determine_region(airport_info['lat'], airport_info['lon'])
                
                if region not in regional_breakdown:
                    regional_breakdown[region] = {
                        'airports': [],
                        'total_travelers': 0
                    }
                
                regional_breakdown[region]['airports'].append(airport_code)
                travelers = self.traveler_calculator.calculate_daily_travelers(airport_code, date)
                regional_breakdown[region]['total_travelers'] += travelers
        
        return regional_breakdown
    
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
    
    def calculate_cumulative_risk(self, risk_exposure: Dict[datetime, Dict]) -> Dict:
        """Calculate cumulative risk metrics across the entire date range."""
        total_travelers_at_risk = 0
        unique_airports_affected = set()
        hurricane_impacts = {}
        
        for date, daily_risk in risk_exposure.items():
            total_travelers_at_risk += daily_risk['total_travelers_at_risk']
            unique_airports_affected.update(daily_risk['airports_at_risk'])
            
            # Track hurricane impacts
            for track_id, impact in daily_risk['hurricane_impacts'].items():
                if track_id not in hurricane_impacts:
                    hurricane_impacts[track_id] = {
                        'total_impact_days': 0,
                        'unique_airports_affected': set(),
                        'max_travelers_at_risk': 0
                    }
                
                hurricane_impacts[track_id]['total_impact_days'] += 1
                hurricane_impacts[track_id]['unique_airports_affected'].update(impact['airports_affected'])
                hurricane_impacts[track_id]['max_travelers_at_risk'] = max(
                    hurricane_impacts[track_id]['max_travelers_at_risk'],
                    sum(self.traveler_calculator.calculate_daily_travelers(airport, date) 
                        for airport in impact['airports_affected'])
                )
        
        # Convert sets to lists for JSON serialization
        for track_id in hurricane_impacts:
            hurricane_impacts[track_id]['unique_airports_affected'] = list(
                hurricane_impacts[track_id]['unique_airports_affected']
            )
        
        return {
            'total_travelers_at_risk': total_travelers_at_risk,
            'unique_airports_affected': list(unique_airports_affected),
            'total_airports_affected': len(unique_airports_affected),
            'hurricane_impacts': hurricane_impacts,
            'risk_summary': {
                'highest_risk_day': max(risk_exposure.keys(), 
                                      key=lambda d: risk_exposure[d]['total_travelers_at_risk']),
                'total_risk_days': len([d for d in risk_exposure.values() 
                                      if d['total_travelers_at_risk'] > 0])
            }
        }
    
    def get_airport_risk_timeline(self, airport_code: str, risk_exposure: Dict[datetime, Dict]) -> List[Dict]:
        """Get risk timeline for a specific airport."""
        timeline = []
        
        for date, daily_risk in risk_exposure.items():
            is_at_risk = airport_code in daily_risk['airports_at_risk']
            travelers = self.traveler_calculator.calculate_daily_travelers(airport_code, date)
            
            timeline.append({
                'date': date,
                'is_at_risk': is_at_risk,
                'expected_travelers': travelers,
                'travelers_at_risk': travelers if is_at_risk else 0
            })
        
        return timeline
    
    def get_top_risk_airports(self, risk_exposure: Dict[datetime, Dict], top_n: int = 10) -> List[Dict]:
        """Get top airports by total travelers at risk."""
        airport_risk_totals = {}
        
        for date, daily_risk in risk_exposure.items():
            for airport_code in daily_risk['airports_at_risk']:
                travelers = self.traveler_calculator.calculate_daily_travelers(airport_code, date)
                
                if airport_code not in airport_risk_totals:
                    airport_risk_totals[airport_code] = {
                        'airport_code': airport_code,
                        'airport_name': MAJOR_AIRPORTS[airport_code]['name'],
                        'total_travelers_at_risk': 0,
                        'risk_days': 0
                    }
                
                airport_risk_totals[airport_code]['total_travelers_at_risk'] += travelers
                airport_risk_totals[airport_code]['risk_days'] += 1
        
        # Sort by total travelers at risk
        sorted_airports = sorted(
            airport_risk_totals.values(),
            key=lambda x: x['total_travelers_at_risk'],
            reverse=True
        )
        
        return sorted_airports[:top_n]
    
    def export_risk_data(self, risk_exposure: Dict[datetime, Dict], filename: Optional[str] = None) -> str:
        """Export risk exposure data to CSV."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"risk_exposure_{timestamp}.csv"
        
        # Flatten risk exposure data
        export_data = []
        
        for date, daily_risk in risk_exposure.items():
            for airport_code in daily_risk['airports_at_risk']:
                travelers = self.traveler_calculator.calculate_daily_travelers(airport_code, date)
                airport_info = MAJOR_AIRPORTS[airport_code]
                
                export_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'airport_code': airport_code,
                    'airport_name': airport_info['name'],
                    'lat': airport_info['lat'],
                    'lon': airport_info['lon'],
                    'expected_travelers': travelers,
                    'travelers_at_risk': travelers,
                    'region': self._determine_region(airport_info['lat'], airport_info['lon'])
                })
        
        df = pd.DataFrame(export_data)
        df.to_csv(filename, index=False)
        
        logger.info(f"Risk exposure data exported to {filename}")
        return filename

def main():
    """Example usage of RiskEngine."""
    from hurricane_data_loader import HurricaneDataLoader
    
    # Load hurricane data
    loader = HurricaneDataLoader()
    hurricane_analyses = loader.load_hurricane_data(source='live', date='2024-09-23')
    
    if not hurricane_analyses:
        print("No hurricane data available")
        return
    
    # Create risk engine
    risk_engine = RiskEngine()
    
    # Define date range (next 14 days)
    start_date = datetime(2024, 9, 23)
    date_range = [start_date + timedelta(days=i) for i in range(14)]
    
    # Calculate risk exposure
    risk_exposure = risk_engine.calculate_risk_exposure(hurricane_analyses, date_range)
    
    # Print summary
    print("Risk Exposure Summary:")
    print(f"Total days analyzed: {len(date_range)}")
    
    total_travelers_at_risk = sum(daily['total_travelers_at_risk'] for daily in risk_exposure.values())
    print(f"Total travelers at risk: {total_travelers_at_risk:,}")
    
    # Get top risk airports
    top_airports = risk_engine.get_top_risk_airports(risk_exposure, top_n=5)
    print("\nTop 5 Risk Airports:")
    for airport in top_airports:
        print(f"  {airport['airport_name']}: {airport['total_travelers_at_risk']:,} travelers at risk")

if __name__ == "__main__":
    main()
