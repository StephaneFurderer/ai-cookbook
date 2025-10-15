#!/usr/bin/env python3
"""
Integration example: Using IBTrACS data with the hurricane impact analysis pipeline.

This script demonstrates how to combine IBTrACS hurricane data with the existing
hurricane impact analysis pipeline to get comprehensive hurricane information.
"""

import sys
import os
import pandas as pd
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ibtracs_fetcher import IBTrACSFetcher
from pipeline import HurricaneImpactPipeline

def get_hurricane_list_from_ibtracs(start_date: str, end_date: str) -> pd.DataFrame:
    """
    Get hurricane list from IBTrACS for the specified date range.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        
    Returns:
        DataFrame with hurricane information
    """
    print(f"Fetching hurricane data from IBTrACS for {start_date} to {end_date}...")
    
    try:
        fetcher = IBTrACSFetcher()
        hurricanes = fetcher.get_hurricanes_by_date_range(start_date, end_date)
        
        if hurricanes.empty:
            print("No hurricanes found in IBTrACS for the specified date range")
            return hurricanes
        
        print(f"Found {len(hurricanes)} hurricanes in IBTrACS:")
        print(hurricanes[['SID', 'NAME', 'SEASON', 'BASIN_NAME']].to_string(index=False))
        
        return hurricanes
        
    except Exception as e:
        print(f"Error fetching IBTrACS data: {e}")
        return pd.DataFrame()

def analyze_hurricane_with_ibtracs(storm_id: str, storm_name: str, 
                                 start_date: str, end_date: str) -> dict:
    """
    Analyze a hurricane using both IBTrACS data and the impact pipeline.
    
    Args:
        storm_id: Storm identifier from IBTrACS
        storm_name: Storm name from IBTrACS
        start_date: Start date for analysis
        end_date: End date for analysis
        
    Returns:
        Dictionary with combined analysis results
    """
    print(f"\nAnalyzing {storm_name} (ID: {storm_id})...")
    
    results = {
        'ibtracs_info': {
            'storm_id': storm_id,
            'storm_name': storm_name,
            'analysis_date': datetime.now().isoformat()
        },
        'impact_analysis': None,
        'ibtracs_track': None,
        'error': None
    }
    
    try:
        # Get detailed track data from IBTrACS
        fetcher = IBTrACSFetcher()
        track_data = fetcher.get_hurricane_track(storm_id)
        
        if not track_data.empty:
            results['ibtracs_track'] = {
                'total_points': len(track_data),
                'date_range': {
                    'start': track_data['ISO_TIME'].min(),
                    'end': track_data['ISO_TIME'].max()
                },
                'max_wind': track_data['WMO_WIND'].max() if 'WMO_WIND' in track_data.columns else None,
                'min_pressure': track_data['WMO_PRES'].min() if 'WMO_PRES' in track_data.columns else None,
                'track_points': track_data[['ISO_TIME', 'LAT', 'LON', 'WMO_WIND', 'WMO_PRES']].to_dict('records')
            }
            print(f"  IBTrACS track: {len(track_data)} points, max wind: {results['ibtracs_track']['max_wind']} knots")
        else:
            print("  No detailed track data available from IBTrACS")
        
        # Run impact analysis pipeline
        pipeline = HurricaneImpactPipeline()
        impact_results = pipeline.run_analysis(start_date, end_date, storm_id)
        
        if 'error' in impact_results:
            results['error'] = impact_results['error']
            print(f"  Impact analysis failed: {impact_results['error']}")
        else:
            results['impact_analysis'] = impact_results
            print(f"  Impact analysis: ${impact_results.get('total_exposure', 0):,.2f} exposure")
        
    except Exception as e:
        results['error'] = str(e)
        print(f"  Analysis failed: {e}")
    
    return results

def main():
    """Main function demonstrating IBTrACS integration."""
    print("=" * 80)
    print("IBTrACS + HURRICANE IMPACT ANALYSIS INTEGRATION")
    print("=" * 80)
    
    # Define analysis parameters
    start_date = '2024-09-23'
    end_date = '2024-09-27'
    
    print(f"Analysis period: {start_date} to {end_date}")
    
    try:
        # Step 1: Get hurricane list from IBTrACS
        hurricanes = get_hurricane_list_from_ibtracs(start_date, end_date)
        
        if hurricanes.empty:
            print("No hurricanes found for analysis")
            return 1
        
        # Step 2: Analyze each hurricane
        all_results = []
        
        for _, storm in hurricanes.iterrows():
            storm_id = storm['SID']
            storm_name = storm['NAME']
            
            # Analyze the hurricane
            analysis = analyze_hurricane_with_ibtracs(
                storm_id, storm_name, start_date, end_date
            )
            
            all_results.append(analysis)
        
        # Step 3: Generate summary report
        print("\n" + "=" * 80)
        print("INTEGRATION ANALYSIS SUMMARY")
        print("=" * 80)
        
        successful_analyses = [r for r in all_results if r['error'] is None]
        failed_analyses = [r for r in all_results if r['error'] is not None]
        
        print(f"Total hurricanes found: {len(all_results)}")
        print(f"Successful analyses: {len(successful_analyses)}")
        print(f"Failed analyses: {len(failed_analyses)}")
        
        if successful_analyses:
            total_exposure = sum(
                r['impact_analysis'].get('total_exposure', 0) 
                for r in successful_analyses 
                if r['impact_analysis']
            )
            print(f"Total exposure across all hurricanes: ${total_exposure:,.2f}")
        
        # Step 4: Save detailed results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = f"ibtracs_integration_results_{timestamp}.json"
        
        import json
        with open(results_file, 'w') as f:
            json.dump(all_results, f, indent=2, default=str)
        
        print(f"\nDetailed results saved to: {results_file}")
        
        # Step 5: Display detailed results for each hurricane
        print("\n" + "-" * 60)
        print("DETAILED RESULTS")
        print("-" * 60)
        
        for i, result in enumerate(all_results, 1):
            storm_info = result['ibtracs_info']
            print(f"\n{i}. {storm_info['storm_name']} (ID: {storm_info['storm_id']})")
            
            if result['error']:
                print(f"   Status: FAILED - {result['error']}")
            else:
                print("   Status: SUCCESS")
                
                # IBTrACS track info
                if result['ibtracs_track']:
                    track = result['ibtracs_track']
                    print(f"   IBTrACS Track: {track['total_points']} points")
                    if track['max_wind']:
                        print(f"   Max Wind Speed: {track['max_wind']} knots")
                    if track['min_pressure']:
                        print(f"   Min Pressure: {track['min_pressure']} mb")
                
                # Impact analysis info
                if result['impact_analysis']:
                    impact = result['impact_analysis']
                    print(f"   Total Exposure: ${impact.get('total_exposure', 0):,.2f}")
                    if 'summary' in impact:
                        summary = impact['summary']
                        print(f"   Affected Airports: {summary.get('total_affected_airports', 0)}")
                        print(f"   Travelers at Risk: {summary.get('total_travelers_at_risk', 0):,}")
        
        print("\n" + "=" * 80)
        print("INTEGRATION COMPLETE")
        print("=" * 80)
        
        return 0
        
    except Exception as e:
        print(f"❌ Integration failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
