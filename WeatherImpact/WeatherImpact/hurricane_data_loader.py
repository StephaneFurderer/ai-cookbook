"""
Hurricane data loader module for handling both live and hypothetical hurricane data.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Union
import logging
import io

from .data_fetcher import HurricaneDataFetcher
from .hurricane_analyzer import HurricaneAnalyzer

logger = logging.getLogger(__name__)

class HurricaneDataLoader:
    """Unified loader for live and hypothetical hurricane data."""
    
    def __init__(self):
        self.fetcher = HurricaneDataFetcher()
        self.analyzer = HurricaneAnalyzer()
    
    def load_hurricane_data(self, source: str = 'live', date: Optional[str] = None, 
                          uploaded_file: Optional[Union[str, io.BytesIO]] = None) -> Dict[str, Dict]:
        """
        Load hurricane data from various sources.
        
        Args:
            source: 'live' for WeatherLab API, 'hypothetical' for uploaded data
            date: Date string (YYYY-MM-DD) for live data
            uploaded_file: File path or BytesIO object for hypothetical data
            
        Returns:
            Dictionary mapping track_id to hurricane analysis
        """
        if source == 'live':
            return self._load_live_data(date)
        elif source == 'hypothetical':
            return self._load_hypothetical_data(uploaded_file)
        else:
            raise ValueError(f"Unknown source: {source}")
    
    def _load_live_data(self, date: str) -> Dict[str, Dict]:
        """Load live hurricane data from WeatherLab API."""
        if not date:
            raise ValueError("Date is required for live data")
        
        logger.info(f"Loading live hurricane data for {date}")
        
        # Download data using existing fetcher
        raw_data = self.fetcher.download_hurricane_data(date)
        
        if raw_data is None or raw_data.empty:
            logger.warning(f"No hurricane data available for {date}")
            return {}
        
        # Process through existing analyzer
        hurricanes = self.analyzer.load_hurricane_data(raw_data)
        analyses = self.analyzer.analyze_multiple_hurricanes(hurricanes)
        
        logger.info(f"Loaded {len(analyses)} hurricanes from live data")
        return analyses
    
    def _load_hypothetical_data(self, uploaded_file: Union[str, io.BytesIO]) -> Dict[str, Dict]:
        """Load hypothetical hurricane data from uploaded file."""
        logger.info("Loading hypothetical hurricane data")
        
        # Read the uploaded file
        if isinstance(uploaded_file, str):
            # File path
            df = pd.read_csv(uploaded_file)
        else:
            # BytesIO object (from Streamlit file uploader)
            df = pd.read_csv(uploaded_file)
        
        # Validate required columns
        required_columns = ['track_id', 'valid_time', 'lat', 'lon', 'maximum_sustained_wind_speed_knots']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Convert valid_time to datetime if it's not already
        if not pd.api.types.is_datetime64_any_dtype(df['valid_time']):
            df['valid_time'] = pd.to_datetime(df['valid_time'])
        
        # Add missing columns with default values to match live data format
        df['init_time'] = df['valid_time'].min()  # Use earliest time as init time
        df['lead_time'] = (df['valid_time'] - df['init_time']).dt.total_seconds() / 3600  # Hours
        df['minimum_sea_level_pressure_hpa'] = 1013.25  # Standard atmospheric pressure
        df['radius_of_maximum_winds_km'] = np.nan
        df['radius_34_knot_winds_ne_km'] = np.nan
        df['radius_34_knot_winds_se_km'] = np.nan
        df['radius_34_knot_winds_sw_km'] = np.nan
        df['radius_34_knot_winds_nw_km'] = np.nan
        df['radius_50_knot_winds_ne_km'] = np.nan
        df['radius_50_knot_winds_se_km'] = np.nan
        df['radius_50_knot_winds_sw_km'] = np.nan
        df['radius_50_knot_winds_nw_km'] = np.nan
        df['radius_64_knot_winds_ne_km'] = np.nan
        df['radius_64_knot_winds_se_km'] = np.nan
        df['radius_64_knot_winds_sw_km'] = np.nan
        df['radius_64_knot_winds_nw_km'] = np.nan
        df['sample'] = -1  # Default sample value
        
        # Reorder columns to match expected format
        expected_columns = [
            'init_time', 'track_id', 'sample', 'valid_time', 'lead_time', 'lat', 'lon',
            'minimum_sea_level_pressure_hpa', 'maximum_sustained_wind_speed_knots',
            'radius_of_maximum_winds_km', 'radius_34_knot_winds_ne_km',
            'radius_34_knot_winds_se_km', 'radius_34_knot_winds_sw_km',
            'radius_34_knot_winds_nw_km', 'radius_50_knot_winds_ne_km',
            'radius_50_knot_winds_se_km', 'radius_50_knot_winds_sw_km',
            'radius_50_knot_winds_nw_km', 'radius_64_knot_winds_ne_km',
            'radius_64_knot_winds_se_km', 'radius_64_knot_winds_sw_km',
            'radius_64_knot_winds_nw_km'
        ]
        
        df = df.reindex(columns=expected_columns)
        
        # Process through existing analyzer
        hurricanes = self.analyzer.load_hurricane_data(df)
        analyses = self.analyzer.analyze_multiple_hurricanes(hurricanes)
        
        logger.info(f"Loaded {len(analyses)} hurricanes from hypothetical data")
        return analyses
    
    def get_available_dates(self) -> List[str]:
        """Get list of available dates for live data."""
        return self.fetcher.get_available_dates()
    
    def get_hurricane_summary(self, date: str) -> Dict:
        """Get summary of hurricanes for a specific date."""
        return self.fetcher.get_hurricane_summary(date)
    
    def validate_hypothetical_data(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Validate hypothetical hurricane data format.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Check required columns
        required_columns = ['track_id', 'valid_time', 'lat', 'lon', 'maximum_sustained_wind_speed_knots']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            errors.append(f"Missing required columns: {missing_columns}")
        
        # Check data types and ranges
        if 'lat' in df.columns:
            if not df['lat'].between(-90, 90).all():
                errors.append("Latitude values must be between -90 and 90")
        
        if 'lon' in df.columns:
            if not df['lon'].between(-180, 180).all():
                errors.append("Longitude values must be between -180 and 180")
        
        if 'maximum_sustained_wind_speed_knots' in df.columns:
            if not (df['maximum_sustained_wind_speed_knots'] >= 0).all():
                errors.append("Wind speed values must be non-negative")
        
        # Check for required data
        if df.empty:
            errors.append("DataFrame is empty")
        
        # Check for duplicate track_id and valid_time combinations
        if 'track_id' in df.columns and 'valid_time' in df.columns:
            duplicates = df.duplicated(subset=['track_id', 'valid_time']).sum()
            if duplicates > 0:
                errors.append(f"Found {duplicates} duplicate track_id and valid_time combinations")
        
        return len(errors) == 0, errors
    
    def create_sample_hypothetical_data(self) -> pd.DataFrame:
        """Create sample hypothetical hurricane data for testing."""
        # Sample Hurricane Helene-like track
        base_time = datetime(2024, 9, 23, 12, 0, 0)
        
        sample_data = {
            'track_id': ['AL972024'] * 5,
            'valid_time': [
                base_time,
                base_time + timedelta(hours=6),
                base_time + timedelta(hours=12),
                base_time + timedelta(hours=18),
                base_time + timedelta(hours=24)
            ],
            'lat': [17.2, 17.39, 17.83, 18.25, 18.61],
            'lon': [-81.7, -81.83, -82.06, -82.69, -83.42],
            'maximum_sustained_wind_speed_knots': [30.0, 27.7, 32.1, 35.6, 38.6]
        }
        
        return pd.DataFrame(sample_data)
    
    def export_hypothetical_template(self) -> str:
        """Create a CSV template for hypothetical hurricane data."""
        template_data = {
            'track_id': ['AL972024', 'AL972024', 'AL972024'],
            'valid_time': ['2024-09-23 12:00:00', '2024-09-23 18:00:00', '2024-09-24 00:00:00'],
            'lat': [17.2, 17.39, 17.83],
            'lon': [-81.7, -81.83, -82.06],
            'maximum_sustained_wind_speed_knots': [30.0, 27.7, 32.1]
        }
        
        template_df = pd.DataFrame(template_data)
        return template_df.to_csv(index=False)

def main():
    """Example usage of HurricaneDataLoader."""
    loader = HurricaneDataLoader()
    
    # Test live data loading
    print("Testing live data loading...")
    try:
        live_data = loader.load_hurricane_data(source='live', date='2024-09-23')
        print(f"Loaded {len(live_data)} hurricanes from live data")
        
        for track_id, analysis in live_data.items():
            print(f"Hurricane {track_id}: {analysis['summary']['peak_category']}")
    except Exception as e:
        print(f"Live data loading failed: {e}")
    
    # Test hypothetical data loading
    print("\nTesting hypothetical data loading...")
    try:
        sample_data = loader.create_sample_hypothetical_data()
        hypothetical_data = loader.load_hurricane_data(source='hypothetical', uploaded_file=sample_data)
        print(f"Loaded {len(hypothetical_data)} hurricanes from hypothetical data")
        
        for track_id, analysis in hypothetical_data.items():
            print(f"Hurricane {track_id}: {analysis['summary']['peak_category']}")
    except Exception as e:
        print(f"Hypothetical data loading failed: {e}")

if __name__ == "__main__":
    main()
