"""
Airport impact module for identifying affected airports and estimating traveler exposure.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
from geopy.distance import geodesic
import requests
import os
from datetime import datetime, timedelta

from config import (
    MAJOR_AIRPORTS,
    ATLANTIC_REGION_BOUNDS,
    AIRPORT_COLORS
)

logger = logging.getLogger(__name__)

class AirportImpact:
    """Analyzes airport impacts from hurricane tracks and estimates traveler exposure."""
    
    def __init__(self):
        self.airport_data = None
        self.affected_airports = {}
        self.traveler_estimates = {}
    
    def load_airport_data(self, use_cached: bool = True) -> pd.DataFrame:
        """
        Load airport data from OurAirports database or use cached major airports.
        
        Args:
            use_cached: If True, use predefined major airports; if False, download from OurAirports
            
        Returns:
            DataFrame with airport information
        """
        if use_cached:
            # Use predefined major airports from config
            airports = []
            for code, info in MAJOR_AIRPORTS.items():
                airports.append({
                    'icao_code': code,
                    'name': info['name'],
                    'latitude_deg': info['lat'],
                    'longitude_deg': info['lon'],
                    'daily_passengers': info['daily_passengers'],
                    'region': self._determine_region(info['lat'], info['lon'])
                })
            
            self.airport_data = pd.DataFrame(airports)
            logger.info(f"Loaded {len(self.airport_data)} major airports")
            return self.airport_data
        
        # Download from OurAirports (optional - not implemented in this version)
        logger.warning("OurAirports download not implemented, using cached data")
        return self.load_airport_data(use_cached=True)
    
    def _determine_region(self, lat: float, lon: float) -> str:
        """Determine geographic region for an airport."""
        if 25 <= lat <= 35 and -85 <= lon <= -75:
            return 'Florida'
        elif 30 <= lat <= 45 and -85 <= lon <= -65:
            return 'US_East_Coast'
        elif 10 <= lat <= 25 and -85 <= lon <= -60:
            return 'Caribbean'
        elif 25 <= lat <= 35 and -100 <= lon <= -85:
            return 'Gulf_Coast'
        elif 30 <= lat <= 45 and -65 <= lon <= -40:
            return 'Northeast'
        else:
            return 'Other'
    
    def find_affected_airports(self, hurricane_analysis: Dict) -> Dict:
        """
        Find airports affected by hurricane impact zones.
        
        Args:
            hurricane_analysis: Hurricane analysis result from HurricaneAnalyzer
            
        Returns:
            Dictionary with affected airports information
        """
        if self.airport_data is None:
            self.load_airport_data()
        
        track_id = hurricane_analysis['track_id']
        impact_zones = hurricane_analysis['impact_zones']
        
        affected_airports = {
            'track_id': track_id,
            'affected_airports': [],
            'total_daily_travelers': 0,
            'impact_summary': {},
            'regional_impact': {}
        }
        
        # Check each airport against impact zones
        for _, airport in self.airport_data.iterrows():
            airport_coords = (airport['latitude_deg'], airport['longitude_deg'])
            airport_impact = self._assess_airport_impact(
                airport_coords, 
                airport, 
                impact_zones, 
                hurricane_analysis
            )
            
            if airport_impact['is_affected']:
                affected_airports['affected_airports'].append(airport_impact)
                affected_airports['total_daily_travelers'] += airport['daily_passengers']
        
        # Calculate summary statistics
        affected_airports['impact_summary'] = self._calculate_impact_summary(
            affected_airports['affected_airports']
        )
        
        # Calculate regional impact
        affected_airports['regional_impact'] = self._calculate_regional_impact(
            affected_airports['affected_airports']
        )
        
        logger.info(f"Found {len(affected_airports['affected_airports'])} affected airports "
                   f"with {affected_airports['total_daily_travelers']:,} daily travelers")
        
        return affected_airports
    
    def _assess_airport_impact(self, airport_coords: Tuple[float, float], 
                             airport: pd.Series, impact_zones: Dict, 
                             hurricane_analysis: Dict) -> Dict:
        """
        Assess impact on a specific airport.
        
        Args:
            airport_coords: (lat, lon) of airport
            airport: Airport data series
            impact_zones: Hurricane impact zones
            hurricane_analysis: Complete hurricane analysis
            
        Returns:
            Dictionary with airport impact assessment
        """
        lat, lon = airport_coords
        impact_assessment = {
            'airport_code': airport['icao_code'],
            'airport_name': airport['name'],
            'coordinates': airport_coords,
            'daily_passengers': airport['daily_passengers'],
            'region': airport['region'],
            'is_affected': False,
            'impact_level': 'none',
            'closest_approach_km': float('inf'),
            'closest_approach_time': None,
            'impact_duration_hours': 0,
            'max_wind_speed_nearby': 0,
            'impact_category': 'none',
            'estimated_delay_hours': 0,
            'flight_disruption_probability': 0.0
        }
        
        # Check distance to hurricane track
        min_distance = float('inf')
        closest_time = None
        max_wind_nearby = 0
        
        trajectory = hurricane_analysis['trajectory']
        if trajectory:
            for i, coord in enumerate(trajectory['coordinates']):
                distance = geodesic(airport_coords, coord).kilometers
                if distance < min_distance:
                    min_distance = distance
                    closest_time = trajectory['time_points'][i]
                    max_wind_nearby = trajectory['wind_speeds'][i]
        
        impact_assessment['closest_approach_km'] = min_distance
        impact_assessment['closest_approach_time'] = closest_time
        impact_assessment['max_wind_speed_nearby'] = max_wind_nearby
        
        # Determine if airport is affected based on impact zones
        airport_point = (lat, lon)
        is_in_impact_zone = False
        
        for impact_point in impact_zones['impact_points']:
            distance = geodesic(airport_point, impact_point['center']).kilometers
            if distance <= impact_point['radius_km']:
                is_in_impact_zone = True
                impact_assessment['impact_duration_hours'] += 6  # Assume 6-hour impact per data point
                impact_assessment['max_wind_speed_nearby'] = max(
                    impact_assessment['max_wind_speed_nearby'],
                    impact_point['wind_speed']
                )
        
        # Also check if within reasonable distance of track
        if min_distance <= 200:  # Within 200km of track
            is_in_impact_zone = True
        
        if is_in_impact_zone:
            impact_assessment['is_affected'] = True
            impact_assessment['impact_category'] = self._get_impact_category(
                min_distance, impact_assessment['max_wind_speed_nearby']
            )
            impact_assessment['impact_level'] = self._get_impact_level(
                impact_assessment['impact_category']
            )
            impact_assessment['estimated_delay_hours'] = self._estimate_delay_hours(
                impact_assessment['max_wind_speed_nearby'], min_distance
            )
            impact_assessment['flight_disruption_probability'] = self._calculate_disruption_probability(
                impact_assessment['max_wind_speed_nearby'], min_distance
            )
        
        return impact_assessment
    
    def _get_impact_category(self, distance_km: float, wind_speed_knots: float) -> str:
        """Determine impact category based on distance and wind speed."""
        if distance_km <= 50:
            if wind_speed_knots >= 74:  # Hurricane force
                return 'severe'
            elif wind_speed_knots >= 58:  # Tropical storm
                return 'moderate'
            else:
                return 'light'
        elif distance_km <= 100:
            if wind_speed_knots >= 74:
                return 'moderate'
            elif wind_speed_knots >= 39:
                return 'light'
            else:
                return 'minimal'
        elif distance_km <= 200:
            if wind_speed_knots >= 74:
                return 'light'
            else:
                return 'minimal'
        else:
            return 'none'
    
    def _get_impact_level(self, category: str) -> str:
        """Convert impact category to impact level."""
        category_mapping = {
            'severe': 'high',
            'moderate': 'medium',
            'light': 'low',
            'minimal': 'low',
            'none': 'none'
        }
        return category_mapping.get(category, 'none')
    
    def _estimate_delay_hours(self, wind_speed_knots: float, distance_km: float) -> float:
        """Estimate average delay in hours based on wind speed and distance."""
        if distance_km > 200:
            return 0.0
        
        # Base delay based on wind speed
        if wind_speed_knots >= 74:  # Hurricane force
            base_delay = 8.0
        elif wind_speed_knots >= 58:  # Tropical storm
            base_delay = 4.0
        elif wind_speed_knots >= 39:  # Gale force
            base_delay = 2.0
        else:
            base_delay = 0.5
        
        # Reduce delay based on distance
        distance_factor = max(0.1, 1.0 - (distance_km / 200.0))
        
        return base_delay * distance_factor
    
    def _calculate_disruption_probability(self, wind_speed_knots: float, distance_km: float) -> float:
        """Calculate probability of flight disruption."""
        if distance_km > 200:
            return 0.0
        
        # Base probability based on wind speed
        if wind_speed_knots >= 74:  # Hurricane force
            base_prob = 0.95
        elif wind_speed_knots >= 58:  # Tropical storm
            base_prob = 0.80
        elif wind_speed_knots >= 39:  # Gale force
            base_prob = 0.60
        else:
            base_prob = 0.30
        
        # Reduce probability based on distance
        distance_factor = max(0.1, 1.0 - (distance_km / 200.0))
        
        return min(0.95, base_prob * distance_factor)
    
    def _calculate_impact_summary(self, affected_airports: List[Dict]) -> Dict:
        """Calculate summary statistics for affected airports."""
        if not affected_airports:
            return {
                'total_airports': 0,
                'total_travelers': 0,
                'high_impact_airports': 0,
                'medium_impact_airports': 0,
                'low_impact_airports': 0,
                'average_delay_hours': 0.0,
                'total_delay_hours': 0.0
            }
        
        summary = {
            'total_airports': len(affected_airports),
            'total_travelers': sum(ap['daily_passengers'] for ap in affected_airports),
            'high_impact_airports': len([ap for ap in affected_airports if ap['impact_level'] == 'high']),
            'medium_impact_airports': len([ap for ap in affected_airports if ap['impact_level'] == 'medium']),
            'low_impact_airports': len([ap for ap in affected_airports if ap['impact_level'] == 'low']),
            'average_delay_hours': np.mean([ap['estimated_delay_hours'] for ap in affected_airports]),
            'total_delay_hours': sum(ap['estimated_delay_hours'] * ap['daily_passengers'] for ap in affected_airports)
        }
        
        return summary
    
    def _calculate_regional_impact(self, affected_airports: List[Dict]) -> Dict:
        """Calculate impact by geographic region."""
        regional_impact = {}
        
        for airport in affected_airports:
            region = airport['region']
            if region not in regional_impact:
                regional_impact[region] = {
                    'airports': 0,
                    'travelers': 0,
                    'high_impact': 0,
                    'medium_impact': 0,
                    'low_impact': 0,
                    'total_delay_hours': 0.0
                }
            
            regional_impact[region]['airports'] += 1
            regional_impact[region]['travelers'] += airport['daily_passengers']
            
            if airport['impact_level'] == 'high':
                regional_impact[region]['high_impact'] += 1
            elif airport['impact_level'] == 'medium':
                regional_impact[region]['medium_impact'] += 1
            elif airport['impact_level'] == 'low':
                regional_impact[region]['low_impact'] += 1
            
            regional_impact[region]['total_delay_hours'] += (
                airport['estimated_delay_hours'] * airport['daily_passengers']
            )
        
        return regional_impact
    
    def get_top_affected_airports(self, affected_airports: List[Dict], top_n: int = 10) -> List[Dict]:
        """Get top N affected airports by impact score."""
        # Calculate impact score (combination of travelers and delay)
        for airport in affected_airports:
            airport['impact_score'] = (
                airport['daily_passengers'] * 
                airport['estimated_delay_hours'] * 
                airport['flight_disruption_probability']
            )
        
        # Sort by impact score and return top N
        sorted_airports = sorted(
            affected_airports, 
            key=lambda x: x['impact_score'], 
            reverse=True
        )
        
        return sorted_airports[:top_n]

def main():
    """Example usage of AirportImpact."""
    from data_fetcher import HurricaneDataFetcher
    from hurricane_analyzer import HurricaneAnalyzer
    
    # Load Hurricane Helene data
    fetcher = HurricaneDataFetcher()
    data = fetcher.download_hurricane_data("2024-09-23")
    
    if data is not None:
        # Analyze hurricane
        analyzer = HurricaneAnalyzer()
        hurricanes = analyzer.load_hurricane_data(data)
        
        # Find affected airports
        airport_impact = AirportImpact()
        airport_impact.load_airport_data()
        
        for track_id, hurricane_data in hurricanes.items():
            analysis = analyzer.analyze_hurricane(hurricane_data)
            affected = airport_impact.find_affected_airports(analysis)
            
            print(f"\nHurricane {track_id} - Affected Airports:")
            print(f"Total affected airports: {affected['impact_summary']['total_airports']}")
            print(f"Total daily travelers: {affected['impact_summary']['total_travelers']:,}")
            
            # Show top affected airports
            top_affected = airport_impact.get_top_affected_airports(affected['affected_airports'], 5)
            for i, airport in enumerate(top_affected, 1):
                print(f"{i}. {airport['airport_name']} ({airport['airport_code']})")
                print(f"   Daily passengers: {airport['daily_passengers']:,}")
                print(f"   Impact level: {airport['impact_level']}")
                print(f"   Estimated delay: {airport['estimated_delay_hours']:.1f} hours")
                print(f"   Disruption probability: {airport['flight_disruption_probability']:.1%}")

if __name__ == "__main__":
    main()
