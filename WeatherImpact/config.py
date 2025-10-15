"""
Configuration settings for Hurricane Impact Analysis system.
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List

# Base URL pattern for Google DeepMind WeatherLab hurricane data
WEATHERLAB_BASE_URL = "https://deepmind.google.com/science/weatherlab/download/cyclones/FNV3/ensemble_mean/paired/csv"
WEATHERLAB_URL_PATTERN = f"{WEATHERLAB_BASE_URL}/FNV3_{{date}}T00_00_paired.csv"

# Default analysis parameters
DEFAULT_START_DATE = "2024-09-23"  # Hurricane Helene
DEFAULT_END_DATE = "2024-09-27"

# Hurricane analysis parameters
MIN_WIND_SPEED_KNOTS = 34  # Minimum wind speed for flight disruptions (34 knots)
IMPACT_ZONE_BUFFER_KM = 50  # Additional buffer around hurricane for airport impact
MAX_FORECAST_DAYS = 5  # Maximum days to forecast ahead

# Airport impact parameters
ATLANTIC_REGION_BOUNDS = {
    'north': 50.0,
    'south': 10.0,
    'east': -40.0,  # West longitude (negative)
    'west': -100.0  # East longitude (negative)
}

# Major airports in Atlantic region with daily passenger estimates (2023 data)
MAJOR_AIRPORTS = {
    # US East Coast
    'ATL': {'lat': 33.6407, 'lon': -84.4277, 'daily_passengers': 100000, 'name': 'Hartsfield-Jackson Atlanta'},
    'MIA': {'lat': 25.7959, 'lon': -80.2870, 'daily_passengers': 50000, 'name': 'Miami International'},
    'JFK': {'lat': 40.6413, 'lon': -73.7781, 'daily_passengers': 80000, 'name': 'John F. Kennedy International'},
    'LGA': {'lat': 40.7769, 'lon': -73.8740, 'daily_passengers': 40000, 'name': 'LaGuardia'},
    'BOS': {'lat': 42.3656, 'lon': -71.0096, 'daily_passengers': 30000, 'name': 'Logan International'},
    'DCA': {'lat': 38.8512, 'lon': -77.0402, 'daily_passengers': 25000, 'name': 'Ronald Reagan Washington'},
    'IAD': {'lat': 38.9531, 'lon': -77.4565, 'daily_passengers': 20000, 'name': 'Dulles International'},
    'PHL': {'lat': 39.8729, 'lon': -75.2437, 'daily_passengers': 25000, 'name': 'Philadelphia International'},
    'BWI': {'lat': 39.1774, 'lon': -76.6684, 'daily_passengers': 15000, 'name': 'Baltimore-Washington International'},
    'CLT': {'lat': 35.2144, 'lon': -80.9473, 'daily_passengers': 45000, 'name': 'Charlotte Douglas International'},
    'RDU': {'lat': 35.8776, 'lon': -78.7875, 'daily_passengers': 12000, 'name': 'Raleigh-Durham International'},
    'ORF': {'lat': 36.8945, 'lon': -76.2019, 'daily_passengers': 8000, 'name': 'Norfolk International'},
    'RIC': {'lat': 37.5052, 'lon': -77.3197, 'daily_passengers': 6000, 'name': 'Richmond International'},
    'SAV': {'lat': 32.1276, 'lon': -81.2021, 'daily_passengers': 4000, 'name': 'Savannah/Hilton Head International'},
    'CHS': {'lat': 32.8986, 'lon': -80.0405, 'daily_passengers': 3000, 'name': 'Charleston International'},
    'MYR': {'lat': 33.6797, 'lon': -78.9283, 'daily_passengers': 2000, 'name': 'Myrtle Beach International'},
    
    # Florida
    'MCO': {'lat': 28.4312, 'lon': -81.3081, 'daily_passengers': 60000, 'name': 'Orlando International'},
    'FLL': {'lat': 26.0716, 'lon': -80.1526, 'daily_passengers': 35000, 'name': 'Fort Lauderdale-Hollywood International'},
    'TPA': {'lat': 27.9755, 'lon': -82.5332, 'daily_passengers': 25000, 'name': 'Tampa International'},
    'RSW': {'lat': 26.5362, 'lon': -81.7552, 'daily_passengers': 8000, 'name': 'Southwest Florida International'},
    'PBI': {'lat': 26.6832, 'lon': -80.0956, 'daily_passengers': 12000, 'name': 'Palm Beach International'},
    'JAX': {'lat': 30.4941, 'lon': -81.6879, 'daily_passengers': 8000, 'name': 'Jacksonville International'},
    'EYW': {'lat': 24.5561, 'lon': -81.7596, 'daily_passengers': 1000, 'name': 'Key West International'},
    
    # Caribbean
    'SJU': {'lat': 18.4394, 'lon': -66.0018, 'daily_passengers': 15000, 'name': 'Luis Muñoz Marín International'},
    'AUA': {'lat': 12.5014, 'lon': -70.0152, 'daily_passengers': 3000, 'name': 'Queen Beatrix International'},
    'BGI': {'lat': 13.0746, 'lon': -59.4925, 'daily_passengers': 2000, 'name': 'Grantley Adams International'},
    'SXM': {'lat': 18.0409, 'lon': -63.1089, 'daily_passengers': 1500, 'name': 'Princess Juliana International'},
    'NAS': {'lat': 25.0389, 'lon': -77.4662, 'daily_passengers': 2000, 'name': 'Lynden Pindling International'},
    'PLS': {'lat': 21.7736, 'lon': -72.2659, 'daily_passengers': 1000, 'name': 'Providenciales International'},
    
    # Bermuda
    'BDA': {'lat': 32.3640, 'lon': -64.6787, 'daily_passengers': 1500, 'name': 'L.F. Wade International'},
    
    # Central America
    'PTY': {'lat': 9.0714, 'lon': -79.3835, 'daily_passengers': 8000, 'name': 'Tocumen International'},
    'SJO': {'lat': 9.9939, 'lon': -84.2089, 'daily_passengers': 5000, 'name': 'Juan Santamaría International'},
}

# Insurance company parameters
INSURANCE_PARAMS = {
    'policy_coverage': 'flight_delay_weather',  # Type of coverage
    'delay_threshold_hours': 3,  # Minimum delay for coverage
    'payout_per_claim': 500,  # Average payout in USD
    'penetration_rate': 0.02,  # 2% of travelers have coverage
    'claim_rate': 0.60,  # 60% of covered travelers in impact zone file claims
    'company_name': 'AeroShield Insurance'
}

# File paths
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
OUTPUTS_DIR = os.path.join(os.path.dirname(__file__), 'outputs')
NOTEBOOKS_DIR = os.path.join(os.path.dirname(__file__), 'notebooks')

# Create directories if they don't exist
for directory in [DATA_DIR, OUTPUTS_DIR, NOTEBOOKS_DIR]:
    os.makedirs(directory, exist_ok=True)

# Visualization settings
MAP_CENTER = [25.0, -70.0]  # Center of Atlantic region
MAP_ZOOM = 5
DEFAULT_MAP_TILES = 'OpenStreetMap'

# Color schemes for visualization
HURRICANE_COLORS = {
    'tropical_depression': '#00BFFF',  # Deep sky blue
    'tropical_storm': '#1E90FF',       # Dodger blue
    'category_1': '#32CD32',           # Lime green
    'category_2': '#FFD700',           # Gold
    'category_3': '#FF8C00',           # Dark orange
    'category_4': '#FF4500',           # Orange red
    'category_5': '#DC143C',           # Crimson
}

AIRPORT_COLORS = {
    'no_impact': '#808080',      # Gray
    'low_impact': '#FFD700',     # Gold
    'medium_impact': '#FF8C00',  # Dark orange
    'high_impact': '#DC143C',    # Crimson
}

# Wind speed categories (knots) for hurricane classification
WIND_SPEED_CATEGORIES = {
    'tropical_depression': (0, 33),
    'tropical_storm': (34, 63),
    'category_1': (64, 82),
    'category_2': (83, 95),
    'category_3': (96, 112),
    'category_4': (113, 136),
    'category_5': (137, float('inf')),
}

def get_hurricane_category(wind_speed_knots: float) -> str:
    """Get hurricane category based on wind speed."""
    for category, (min_speed, max_speed) in WIND_SPEED_CATEGORIES.items():
        if min_speed <= wind_speed_knots < max_speed:
            return category
    return 'unknown'

def get_weatherlab_url(date_str: str) -> str:
    """Generate WeatherLab URL for a specific date."""
    return WEATHERLAB_URL_PATTERN.format(date=date_str)

def get_date_range(start_date: str, end_date: str) -> List[str]:
    """Generate list of dates between start and end date."""
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    dates = []
    current = start
    while current <= end:
        dates.append(current.strftime('%Y-%m-%d'))
        current += timedelta(days=1)
    return dates
