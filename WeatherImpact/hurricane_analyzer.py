"""
Hurricane analyzer module for processing track data and creating impact zones.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import logging
from geopy.distance import geodesic
import shapely.geometry as geom
from shapely.ops import unary_union

from config import (
    MIN_WIND_SPEED_KNOTS,
    IMPACT_ZONE_BUFFER_KM,
    MAX_FORECAST_DAYS,
    WIND_SPEED_CATEGORIES,
    get_hurricane_category
)

logger = logging.getLogger(__name__)

class HurricaneAnalyzer:
    """Analyzes hurricane track data to create impact zones and trajectories."""
    
    def __init__(self):
        self.impact_zones = {}
        self.trajectories = {}
    
    def load_hurricane_data(self, data: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        Load and organize hurricane data by track_id.
        
        Args:
            data: DataFrame with hurricane track data
            
        Returns:
            Dictionary mapping track_id to hurricane data
        """
        if data is None or data.empty:
            logger.warning("No hurricane data provided")
            return {}
        
        hurricanes = {}
        for track_id, group in data.groupby('track_id'):
            # Sort by valid_time to ensure chronological order
            group = group.sort_values('valid_time').reset_index(drop=True)
            hurricanes[track_id] = group
            logger.info(f"Loaded hurricane {track_id} with {len(group)} data points")
        
        return hurricanes
    
    def extract_trajectory(self, hurricane_data: pd.DataFrame) -> Dict:
        """
        Extract hurricane trajectory with key characteristics.
        
        Args:
            hurricane_data: DataFrame for a single hurricane
            
        Returns:
            Dictionary with trajectory information
        """
        if hurricane_data.empty:
            return {}
        
        # Sort by time
        data = hurricane_data.sort_values('valid_time').reset_index(drop=True)
        
        trajectory = {
            'track_id': data['track_id'].iloc[0],
            'init_time': data['init_time'].iloc[0],
            'time_points': data['valid_time'].tolist(),
            'coordinates': list(zip(data['lat'], data['lon'])),
            'wind_speeds': data['maximum_sustained_wind_speed_knots'].tolist(),
            'pressures': data['minimum_sea_level_pressure_hpa'].tolist(),
            'lead_times': data['lead_time'].tolist(),
            'intensity_history': [],
            'peak_intensity': {
                'wind_speed': data['maximum_sustained_wind_speed_knots'].max(),
                'pressure': data['minimum_sea_level_pressure_hpa'].min(),
                'category': get_hurricane_category(data['maximum_sustained_wind_speed_knots'].max())
            },
            'current_status': {
                'wind_speed': data['maximum_sustained_wind_speed_knots'].iloc[-1],
                'pressure': data['minimum_sea_level_pressure_hpa'].iloc[-1],
                'category': get_hurricane_category(data['maximum_sustained_wind_speed_knots'].iloc[-1]),
                'lat': data['lat'].iloc[-1],
                'lon': data['lon'].iloc[-1],
                'time': data['valid_time'].iloc[-1]
            }
        }
        
        # Calculate intensity history
        for _, row in data.iterrows():
            intensity = {
                'time': row['valid_time'],
                'wind_speed': row['maximum_sustained_wind_speed_knots'],
                'pressure': row['minimum_sea_level_pressure_hpa'],
                'category': get_hurricane_category(row['maximum_sustained_wind_speed_knots']),
                'lat': row['lat'],
                'lon': row['lon']
            }
            trajectory['intensity_history'].append(intensity)
        
        return trajectory
    
    def create_impact_zones(self, hurricane_data: pd.DataFrame) -> Dict:
        """
        Create impact zones around hurricane track points.
        
        Args:
            hurricane_data: DataFrame for a single hurricane
            
        Returns:
            Dictionary with impact zone information
        """
        if hurricane_data.empty:
            return {}
        
        track_id = hurricane_data['track_id'].iloc[0]
        zones = {
            'track_id': track_id,
            'impact_points': [],
            'combined_zone': None,
            'max_impact_radius': 0
        }
        
        max_radius = 0
        
        for _, row in hurricane_data.iterrows():
            lat, lon = row['lat'], row['lon']
            wind_speed = row['maximum_sustained_wind_speed_knots']
            time = row['valid_time']
            
            # Calculate impact radius based on wind speed and available radius data
            impact_radius = self._calculate_impact_radius(row, wind_speed)
            max_radius = max(max_radius, impact_radius)
            
            # Create circular impact zone
            center = (lat, lon)
            circle = self._create_circle_zone(center, impact_radius)
            
            impact_point = {
                'time': time,
                'center': center,
                'radius_km': impact_radius,
                'wind_speed': wind_speed,
                'category': get_hurricane_category(wind_speed),
                'geometry': circle,
                'lead_time': row['lead_time']
            }
            
            zones['impact_points'].append(impact_point)
        
        zones['max_impact_radius'] = max_radius
        
        # Create combined impact zone (union of all circles)
        if zones['impact_points']:
            circles = [point['geometry'] for point in zones['impact_points']]
            zones['combined_zone'] = unary_union(circles)
        
        return zones
    
    def _calculate_impact_radius(self, row: pd.Series, wind_speed: float) -> float:
        """
        Calculate impact radius for a hurricane point.
        
        Args:
            row: Hurricane data row
            wind_speed: Wind speed in knots
            
        Returns:
            Impact radius in kilometers
        """
        # Try to use actual radius data if available
        radius_34_ne = row.get('radius_34_knot_winds_ne_km', np.nan)
        radius_34_se = row.get('radius_34_knot_winds_se_km', np.nan)
        radius_34_sw = row.get('radius_34_knot_winds_sw_km', np.nan)
        radius_34_nw = row.get('radius_34_knot_winds_nw_km', np.nan)
        
        if not pd.isna(radius_34_ne):
            # Use average of 34-knot wind radii as base impact zone
            radii = [r for r in [radius_34_ne, radius_34_se, radius_34_sw, radius_34_nw] if not pd.isna(r)]
            if radii:
                base_radius = np.mean(radii)
            else:
                base_radius = self._estimate_radius_from_wind_speed(wind_speed)
        else:
            base_radius = self._estimate_radius_from_wind_speed(wind_speed)
        
        # Add buffer for airport impact assessment
        return base_radius + IMPACT_ZONE_BUFFER_KM
    
    def _estimate_radius_from_wind_speed(self, wind_speed: float) -> float:
        """
        Estimate impact radius based on wind speed when actual radius data is unavailable.
        
        Args:
            wind_speed: Wind speed in knots
            
        Returns:
            Estimated radius in kilometers
        """
        # Empirical relationship between wind speed and typical storm size
        if wind_speed < 34:
            return 50  # Tropical depression
        elif wind_speed < 64:
            return 100  # Tropical storm
        elif wind_speed < 83:
            return 150  # Category 1
        elif wind_speed < 96:
            return 200  # Category 2
        elif wind_speed < 113:
            return 250  # Category 3
        elif wind_speed < 137:
            return 300  # Category 4
        else:
            return 400  # Category 5
    
    def _create_circle_zone(self, center: Tuple[float, float], radius_km: float) -> geom.Polygon:
        """
        Create a circular zone around a center point.
        
        Args:
            center: (latitude, longitude) center point
            radius_km: Radius in kilometers
            
        Returns:
            Shapely Polygon representing the circular zone
        """
        lat, lon = center
        
        # Create circle using geodesic calculations
        # Approximate: 1 degree latitude ≈ 111 km
        lat_offset = radius_km / 111.0
        lon_offset = radius_km / (111.0 * np.cos(np.radians(lat)))
        
        # Create a rough circle with 16 points
        angles = np.linspace(0, 2 * np.pi, 16, endpoint=False)
        points = []
        
        for angle in angles:
            # Use simple approximation for small circles
            point_lat = lat + lat_offset * np.cos(angle)
            point_lon = lon + lon_offset * np.sin(angle)
            points.append((point_lon, point_lat))  # Shapely expects (lon, lat)
        
        return geom.Polygon(points)
    
    def analyze_hurricane(self, hurricane_data: pd.DataFrame) -> Dict:
        """
        Complete analysis of a hurricane including trajectory and impact zones.
        
        Args:
            hurricane_data: DataFrame for a single hurricane
            
        Returns:
            Dictionary with complete hurricane analysis
        """
        track_id = hurricane_data['track_id'].iloc[0]
        
        analysis = {
            'track_id': track_id,
            'trajectory': self.extract_trajectory(hurricane_data),
            'impact_zones': self.create_impact_zones(hurricane_data),
            'analysis_timestamp': datetime.now(),
            'data_points': len(hurricane_data)
        }
        
        # Add summary statistics
        trajectory = analysis['trajectory']
        if trajectory:
            analysis['summary'] = {
                'duration_hours': (trajectory['time_points'][-1] - trajectory['time_points'][0]).total_seconds() / 3600,
                'max_wind_speed': trajectory['peak_intensity']['wind_speed'],
                'min_pressure': trajectory['peak_intensity']['pressure'],
                'peak_category': trajectory['peak_intensity']['category'],
                'current_category': trajectory['current_status']['category'],
                'track_length_km': self._calculate_track_length(trajectory['coordinates']),
                'max_impact_radius': analysis['impact_zones']['max_impact_radius']
            }
        
        return analysis
    
    def _calculate_track_length(self, coordinates: List[Tuple[float, float]]) -> float:
        """
        Calculate total track length in kilometers.
        
        Args:
            coordinates: List of (lat, lon) tuples
            
        Returns:
            Total track length in kilometers
        """
        if len(coordinates) < 2:
            return 0.0
        
        total_distance = 0.0
        for i in range(1, len(coordinates)):
            distance = geodesic(coordinates[i-1], coordinates[i]).kilometers
            total_distance += distance
        
        return total_distance
    
    def analyze_multiple_hurricanes(self, hurricanes_data: Dict[str, pd.DataFrame]) -> Dict[str, Dict]:
        """
        Analyze multiple hurricanes.
        
        Args:
            hurricanes_data: Dictionary mapping track_id to hurricane data
            
        Returns:
            Dictionary mapping track_id to hurricane analysis
        """
        analyses = {}
        
        for track_id, data in hurricanes_data.items():
            logger.info(f"Analyzing hurricane {track_id}")
            analysis = self.analyze_hurricane(data)
            analyses[track_id] = analysis
        
        return analyses
    
    def get_affected_areas(self, analysis: Dict, target_coordinates: List[Tuple[float, float]]) -> Dict:
        """
        Determine which target coordinates are affected by hurricane impact zones.
        
        Args:
            analysis: Hurricane analysis result
            target_coordinates: List of (lat, lon) coordinates to check
            
        Returns:
            Dictionary with affected areas information
        """
        affected = {
            'track_id': analysis['track_id'],
            'affected_points': [],
            'total_affected': 0,
            'max_impact_time': None,
            'max_impact_distance': float('inf')
        }
        
        impact_zones = analysis['impact_zones']
        
        for point in target_coordinates:
            lat, lon = point
            point_geom = geom.Point(lon, lat)  # Shapely expects (lon, lat)
            
            # Check against combined impact zone
            if impact_zones['combined_zone'] and impact_zones['combined_zone'].contains(point_geom):
                # Find closest impact point
                min_distance = float('inf')
                closest_impact = None
                
                for impact_point in impact_zones['impact_points']:
                    distance = geodesic(point, impact_point['center']).kilometers
                    if distance < min_distance:
                        min_distance = distance
                        closest_impact = impact_point
                
                affected_point = {
                    'coordinates': point,
                    'impact_time': closest_impact['time'] if closest_impact else None,
                    'impact_distance_km': min_distance,
                    'impact_wind_speed': closest_impact['wind_speed'] if closest_impact else None,
                    'impact_category': closest_impact['category'] if closest_impact else None
                }
                
                affected['affected_points'].append(affected_point)
                affected['total_affected'] += 1
                
                if min_distance < affected['max_impact_distance']:
                    affected['max_impact_distance'] = min_distance
                    affected['max_impact_time'] = closest_impact['time'] if closest_impact else None
        
        return affected

def main():
    """Example usage of HurricaneAnalyzer."""
    from data_fetcher import HurricaneDataFetcher
    
    # Load Hurricane Helene data
    fetcher = HurricaneDataFetcher()
    data = fetcher.download_hurricane_data("2024-09-23")
    
    if data is not None:
        analyzer = HurricaneAnalyzer()
        hurricanes = analyzer.load_hurricane_data(data)
        
        for track_id, hurricane_data in hurricanes.items():
            print(f"\nAnalyzing Hurricane {track_id}")
            analysis = analyzer.analyze_hurricane(hurricane_data)
            
            if 'summary' in analysis:
                summary = analysis['summary']
                print(f"  Peak intensity: {summary['peak_category']} ({summary['max_wind_speed']:.1f} knots)")
                print(f"  Current status: {summary['current_category']}")
                print(f"  Track length: {summary['track_length_km']:.1f} km")
                print(f"  Max impact radius: {summary['max_impact_radius']:.1f} km")
                print(f"  Duration: {summary['duration_hours']:.1f} hours")

if __name__ == "__main__":
    main()
