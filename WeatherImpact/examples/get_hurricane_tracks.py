#!/usr/bin/env python3
"""
Example script to extract hurricane track IDs and names from IBTrACS dataset.

This script demonstrates how to use the IBTrACSFetcher to get hurricane
information from the NOAA IBTrACS v4 dataset via Google Earth Engine.
"""

import sys
import os
import pandas as pd
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ibtracs_fetcher import IBTrACSFetcher

def main():
    """Main function to demonstrate hurricane data extraction."""
    print("=" * 80)
    print("HURRICANE TRACK ID AND NAME EXTRACTION")
    print("Using NOAA IBTrACS v4 dataset via Google Earth Engine")
    print("=" * 80)
    
    try:
        # Initialize the IBTrACS fetcher
        print("Initializing IBTrACS fetcher...")
        fetcher = IBTrACSFetcher()
        print("✅ IBTrACS fetcher initialized successfully")
        
        # Example 1: Get all hurricanes from 2020-2024
        print("\n" + "-" * 60)
        print("EXAMPLE 1: All Hurricanes (2020-2024)")
        print("-" * 60)
        
        hurricanes = fetcher.get_all_hurricanes(2020, 2024)
        print(f"Found {len(hurricanes)} hurricanes from 2020-2024")
        
        if not hurricanes.empty:
            print("\nFirst 15 hurricanes:")
            display_cols = ['SID', 'NAME', 'SEASON', 'BASIN_NAME']
            print(hurricanes[display_cols].head(15).to_string(index=False))
        
        # Example 2: Get North Atlantic hurricanes only
        print("\n" + "-" * 60)
        print("EXAMPLE 2: North Atlantic Hurricanes (2020-2024)")
        print("-" * 60)
        
        na_hurricanes = fetcher.get_hurricanes_by_basin('NA', 2020, 2024)
        print(f"Found {len(na_hurricanes)} North Atlantic hurricanes")
        
        if not na_hurricanes.empty:
            print("\nNorth Atlantic hurricanes:")
            print(na_hurricanes[['SID', 'NAME', 'SEASON']].to_string(index=False))
        
        # Example 3: Get hurricanes from a specific date range
        print("\n" + "-" * 60)
        print("EXAMPLE 3: Hurricanes Active During Hurricane Season 2024")
        print("(June 1 - November 30, 2024)")
        print("-" * 60)
        
        season_hurricanes = fetcher.get_hurricanes_by_date_range('2024-06-01', '2024-11-30')
        print(f"Found {len(season_hurricanes)} hurricanes active during 2024 season")
        
        if not season_hurricanes.empty:
            print("\n2024 hurricane season storms:")
            print(season_hurricanes[['SID', 'NAME', 'SEASON', 'BASIN_NAME']].to_string(index=False))
        
        # Example 4: Get detailed track for a specific hurricane
        if not na_hurricanes.empty:
            print("\n" + "-" * 60)
            print("EXAMPLE 4: Detailed Track for First North Atlantic Hurricane")
            print("-" * 60)
            
            first_storm = na_hurricanes.iloc[0]
            storm_id = first_storm['SID']
            storm_name = first_storm['NAME']
            
            print(f"Getting detailed track for {storm_name} (ID: {storm_id})")
            
            track_data = fetcher.get_hurricane_track(storm_id)
            
            if not track_data.empty:
                print(f"Found {len(track_data)} track points")
                print("\nFirst 10 track points:")
                track_cols = ['ISO_TIME', 'LAT', 'LON', 'WMO_WIND', 'WMO_PRES']
                available_cols = [col for col in track_cols if col in track_data.columns]
                print(track_data[available_cols].head(10).to_string(index=False))
            else:
                print("No detailed track data available")
        
        # Example 5: Get summary statistics
        print("\n" + "-" * 60)
        print("EXAMPLE 5: Summary Statistics (2020-2024)")
        print("-" * 60)
        
        summary = fetcher.get_hurricane_summary(2020, 2024)
        
        print(f"Total hurricanes: {summary['total_hurricanes']}")
        print(f"Named storms: {summary['named_storms']}")
        print(f"Unnamed storms: {summary['unnamed_storms']}")
        print(f"Year range: {summary['year_range']}")
        print(f"Years with data: {summary['years_with_data']}")
        
        print("\nHurricanes by basin:")
        for basin, count in summary['basin_names'].items():
            print(f"  {basin}: {count}")
        
        # Save results to CSV
        print("\n" + "-" * 60)
        print("SAVING RESULTS")
        print("-" * 60)
        
        # Save all hurricanes
        output_file = f"hurricane_tracks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        hurricanes.to_csv(output_file, index=False)
        print(f"✅ Saved all hurricane data to: {output_file}")
        
        # Save North Atlantic hurricanes
        na_output_file = f"north_atlantic_hurricanes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        na_hurricanes.to_csv(na_output_file, index=False)
        print(f"✅ Saved North Atlantic hurricane data to: {na_output_file}")
        
        print("\n" + "=" * 80)
        print("EXTRACTION COMPLETE")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nMake sure you have:")
        print("1. Installed the earthengine-api package: pip install earthengine-api")
        print("2. Authenticated with Google Earth Engine: earthengine authenticate")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
