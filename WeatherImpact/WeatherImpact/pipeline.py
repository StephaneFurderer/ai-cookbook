"""
Main pipeline orchestration script for hurricane impact analysis.
"""

import argparse
import logging
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
import json

from .data_fetcher import HurricaneDataFetcher
from .hurricane_analyzer import HurricaneAnalyzer
from .airport_impact import AirportImpact
from .insurance_calculator import InsuranceCalculator
from .visualizer import HurricaneVisualizer
from .config import DEFAULT_START_DATE, DEFAULT_END_DATE, OUTPUTS_DIR, DATA_DIR

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('hurricane_analysis.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class HurricaneImpactPipeline:
    """Main pipeline for hurricane impact analysis."""
    
    def __init__(self, outputs_dir: str = OUTPUTS_DIR, data_dir: str = DATA_DIR):
        self.outputs_dir = outputs_dir
        self.data_dir = data_dir
        self.fetcher = HurricaneDataFetcher(data_dir=data_dir)
        self.analyzer = HurricaneAnalyzer()
        self.airport_impact = AirportImpact()
        self.calculator = InsuranceCalculator()
        self.visualizer = HurricaneVisualizer(outputs_dir)
        
        # Create output directory for this run
        self.run_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.run_output_dir = os.path.join(outputs_dir, f"run_{self.run_timestamp}")
        os.makedirs(self.run_output_dir, exist_ok=True)
        
        logger.info(f"Pipeline initialized. Output directory: {self.run_output_dir}")
    
    def run_analysis(self, start_date: str, 
                    hurricane_id: Optional[str] = None,
                    force_download: bool = False) -> Dict:
        """
        Run complete hurricane impact analysis pipeline.
        
        Args:
            start_date: Start date for analysis (YYYY-MM-DD)
            hurricane_id: Specific hurricane ID to analyze (optional)
            force_download: Force re-download of data
            
        Returns:
            Dictionary with analysis results
        """
        logger.info(f"Starting hurricane impact analysis from {start_date} to {end_date}")
        
        results = {
            'pipeline_start_time': datetime.now(),
            'parameters': {
                'start_date': start_date,
                'hurricane_id': hurricane_id,
                'force_download': force_download
            },
            'hurricane_analyses': {},
            'total_exposure': 0.0,
            'summary': {}
        }
        
        try:
            # Step 1: Download hurricane data
            logger.info("Step 1: Downloading hurricane data...")
            hurricane_data = self._download_data(start_date, force_download)
            
            if hurricane_data is None or hurricane_data.empty:
                logger.error("No hurricane data available for the specified date range")
                return results
            
            # Step 2: Analyze hurricanes
            logger.info("Step 2: Analyzing hurricane tracks and impact zones...")
            hurricane_analyses = self._analyze_hurricanes(hurricane_data, hurricane_id)
            results['hurricane_analyses'] = hurricane_analyses
            
            # Step 3: Calculate airport impacts and insurance exposure
            logger.info("Step 3: Calculating airport impacts and insurance exposure...")
            total_exposure = 0.0
            
            for track_id, analysis in hurricane_analyses.items():
                # Find affected airports
                affected_airports = self.airport_impact.find_affected_airports(analysis)
                
                # Calculate insurance exposure
                exposure = self.calculator.calculate_exposure(affected_airports)
                
                # Store results
                analysis['affected_airports'] = affected_airports
                analysis['exposure'] = exposure
                
                total_exposure += exposure['total_exposure']
                
                logger.info(f"Hurricane {track_id}: ${exposure['total_exposure']:,.2f} exposure")
            
            results['total_exposure'] = total_exposure
            
            # Step 4: Generate visualizations
            logger.info("Step 4: Generating visualizations...")
            self._generate_visualizations(hurricane_analyses)
            
            # Step 5: Generate reports
            logger.info("Step 5: Generating reports...")
            self._generate_reports(hurricane_analyses, results)
            
            # Step 6: Create summary
            results['summary'] = self._create_summary(hurricane_analyses, total_exposure)
            results['pipeline_end_time'] = datetime.now()
            results['pipeline_duration'] = (
                results['pipeline_end_time'] - results['pipeline_start_time']
            ).total_seconds()
            
            logger.info(f"Pipeline completed successfully in {results['pipeline_duration']:.1f} seconds")
            logger.info(f"Total exposure across all hurricanes: ${total_exposure:,.2f}")
            
            return results
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            results['error'] = str(e)
            results['pipeline_end_time'] = datetime.now()
            return results
    
    def _download_data(self, start_date: str, 
                      force_download: bool) -> Dict:
        """Download hurricane data for the specified date range."""
        data_by_date = self.fetcher.download_date_range(
            start_date, force_download
        )
        
        if not data_by_date:
            logger.warning("No data downloaded")
            return {}
        
        # Combine all data into single DataFrame
        all_data = []
        for date, df in data_by_date.items():
            if df is not None and not df.empty:
                all_data.append(df)
        
        if not all_data:
            logger.warning("No valid data found")
            return {}
        
        import pandas as pd
        combined_data = pd.concat(all_data, ignore_index=True)
        logger.info(f"Downloaded {len(combined_data)} total records")
        
        return combined_data
    
    def _analyze_hurricanes(self, hurricane_data, hurricane_id: Optional[str] = None) -> Dict:
        """Analyze hurricane tracks and create impact zones."""
        hurricanes = self.analyzer.load_hurricane_data(hurricane_data)
        
        if hurricane_id and hurricane_id in hurricanes:
            # Analyze specific hurricane
            analysis = self.analyzer.analyze_hurricane(hurricanes[hurricane_id])
            return {hurricane_id: analysis}
        else:
            # Analyze all hurricanes
            analyses = self.analyzer.analyze_multiple_hurricanes(hurricanes)
            return analyses
    
    def _generate_visualizations(self, hurricane_analyses: Dict):
        """Generate visualizations for all hurricanes."""
        for track_id, analysis in hurricane_analyses.items():
            affected_airports = analysis['affected_airports']
            exposure = analysis['exposure']
            
            # Create interactive map
            map_file = self.visualizer.create_interactive_map(
                analysis, affected_airports, exposure
            )
            
            # Create dashboard
            dashboard_file = self.visualizer.create_dashboard(
                analysis, affected_airports, exposure
            )
            
            logger.info(f"Generated visualizations for {track_id}:")
            logger.info(f"  Map: {map_file}")
            logger.info(f"  Dashboard: {dashboard_file}")
    
    def _generate_reports(self, hurricane_analyses: Dict, results: Dict):
        """Generate text and JSON reports."""
        # Generate text report
        report_text = self._generate_text_report(hurricane_analyses, results)
        report_file = os.path.join(self.run_output_dir, "analysis_report.txt")
        with open(report_file, 'w') as f:
            f.write(report_text)
        
        # Generate JSON report
        json_file = os.path.join(self.run_output_dir, "analysis_results.json")
        
        # Convert datetime objects to strings for JSON serialization
        json_results = self._prepare_for_json(results)
        with open(json_file, 'w') as f:
            json.dump(json_results, f, indent=2, default=str)
        
        logger.info(f"Reports generated:")
        logger.info(f"  Text report: {report_file}")
        logger.info(f"  JSON report: {json_file}")
    
    def _generate_text_report(self, hurricane_analyses: Dict, results: Dict) -> str:
        """Generate human-readable text report."""
        report = []
        report.append("=" * 80)
        report.append("HURRICANE IMPACT ANALYSIS REPORT")
        report.append("=" * 80)
        report.append(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Date Range: {results['parameters']['start_date']} to {results['parameters']['end_date']}")
        report.append(f"Total Hurricanes Analyzed: {len(hurricane_analyses)}")
        report.append(f"Total Exposure: ${results['total_exposure']:,.2f}")
        report.append("")
        
        # Summary statistics
        report.append("SUMMARY STATISTICS")
        report.append("-" * 40)
        total_airports = 0
        total_passengers = 0
        total_claims = 0
        
        for track_id, analysis in hurricane_analyses.items():
            affected_airports = analysis['affected_airports']
            exposure = analysis['exposure']
            
            total_airports += len(affected_airports['affected_airports'])
            total_passengers += affected_airports['total_daily_travelers']
            total_claims += exposure['total_potential_claims']
        
        report.append(f"Total Affected Airports: {total_airports}")
        report.append(f"Total Daily Travelers at Risk: {total_passengers:,}")
        report.append(f"Total Potential Claims: {total_claims:,}")
        report.append("")
        
        # Detailed analysis for each hurricane
        for track_id, analysis in hurricane_analyses.items():
            report.append(f"HURRICANE {track_id} DETAILED ANALYSIS")
            report.append("-" * 50)
            
            # Hurricane characteristics
            summary = analysis.get('summary', {})
            report.append(f"Peak Intensity: {summary.get('peak_category', 'Unknown')}")
            report.append(f"Current Status: {summary.get('current_category', 'Unknown')}")
            report.append(f"Track Length: {summary.get('track_length_km', 0):.1f} km")
            report.append(f"Duration: {summary.get('duration_hours', 0):.1f} hours")
            report.append("")
            
            # Airport impacts
            affected_airports = analysis['affected_airports']
            report.append("AIRPORT IMPACTS:")
            report.append(f"  Affected Airports: {affected_airports['impact_summary']['total_airports']}")
            report.append(f"  Total Travelers: {affected_airports['impact_summary']['total_travelers']:,}")
            report.append(f"  High Impact Airports: {affected_airports['impact_summary']['high_impact_airports']}")
            report.append(f"  Medium Impact Airports: {affected_airports['impact_summary']['medium_impact_airports']}")
            report.append(f"  Low Impact Airports: {affected_airports['impact_summary']['low_impact_airports']}")
            report.append("")
            
            # Insurance exposure
            exposure = analysis['exposure']
            report.append("INSURANCE EXPOSURE:")
            report.append(f"  Total Exposure: ${exposure['total_exposure']:,.2f}")
            report.append(f"  Potential Claims: {exposure['total_potential_claims']:,}")
            report.append(f"  Risk Score: {exposure['risk_metrics']['severity_score']:.1f}/100")
            report.append("")
            
            # Top affected airports
            top_airports = sorted(
                exposure['airport_exposures'],
                key=lambda x: x['total_exposure'],
                reverse=True
            )[:5]
            
            report.append("TOP 5 AFFECTED AIRPORTS:")
            for i, airport in enumerate(top_airports, 1):
                report.append(f"  {i}. {airport['airport_name']} ({airport['airport_code']})")
                report.append(f"     Exposure: ${airport['total_exposure']:,.2f}")
                report.append(f"     Passengers: {airport['daily_passengers']:,}")
                report.append(f"     Impact Level: {airport['impact_level']}")
            report.append("")
        
        return "\n".join(report)
    
    def _create_summary(self, hurricane_analyses: Dict, total_exposure: float) -> Dict:
        """Create executive summary."""
        summary = {
            'total_hurricanes': len(hurricane_analyses),
            'total_exposure': total_exposure,
            'total_affected_airports': 0,
            'total_travelers_at_risk': 0,
            'total_potential_claims': 0,
            'hurricane_summaries': {}
        }
        
        for track_id, analysis in hurricane_analyses.items():
            affected_airports = analysis['affected_airports']
            exposure = analysis['exposure']
            
            summary['total_affected_airports'] += len(affected_airports['affected_airports'])
            summary['total_travelers_at_risk'] += affected_airports['total_daily_travelers']
            summary['total_potential_claims'] += exposure['total_potential_claims']
            
            summary['hurricane_summaries'][track_id] = {
                'peak_category': analysis.get('summary', {}).get('peak_category', 'Unknown'),
                'current_category': analysis.get('summary', {}).get('current_category', 'Unknown'),
                'affected_airports': len(affected_airports['affected_airports']),
                'exposure': exposure['total_exposure'],
                'risk_score': exposure['risk_metrics']['severity_score']
            }
        
        return summary
    
    def _prepare_for_json(self, obj):
        """Prepare object for JSON serialization by converting datetime objects."""
        if isinstance(obj, dict):
            return {key: self._prepare_for_json(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._prepare_for_json(item) for item in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        else:
            return obj

def main():
    """Main function for command-line interface."""
    parser = argparse.ArgumentParser(
        description="Hurricane Impact Analysis Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze Hurricane Helene (2024-09-23)
  python pipeline.py --start-date 2024-09-23 --end-date 2024-09-27
  
  # Analyze specific hurricane
  python pipeline.py --start-date 2024-09-23 --end-date 2024-09-27 --hurricane-id AL972024
  
  # Force re-download of data
  python pipeline.py --start-date 2024-09-23 --end-date 2024-09-27 --force-download
        """
    )
    
    parser.add_argument(
        '--start-date',
        type=str,
        default=DEFAULT_START_DATE,
        help=f'Start date for analysis (YYYY-MM-DD). Default: {DEFAULT_START_DATE}'
    )
    
    parser.add_argument(
        '--end-date',
        type=str,
        default=DEFAULT_END_DATE,
        help=f'End date for analysis (YYYY-MM-DD). Default: {DEFAULT_END_DATE}'
    )
    
    parser.add_argument(
        '--hurricane-id',
        type=str,
        help='Specific hurricane ID to analyze (e.g., AL972024)'
    )
    
    parser.add_argument(
        '--force-download',
        action='store_true',
        help='Force re-download of hurricane data'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default=OUTPUTS_DIR,
        help=f'Output directory for results. Default: {OUTPUTS_DIR}'
    )
    
    args = parser.parse_args()
    
    # Validate dates
    try:
        datetime.strptime(args.start_date, '%Y-%m-%d')
        datetime.strptime(args.end_date, '%Y-%m-%d')
    except ValueError:
        logger.error("Invalid date format. Use YYYY-MM-DD")
        sys.exit(1)
    
    # Run pipeline
    pipeline = HurricaneImpactPipeline(args.output_dir)
    results = pipeline.run_analysis(
        start_date=args.start_date,
        end_date=args.end_date,
        hurricane_id=args.hurricane_id,
        force_download=args.force_download
    )
    
    # Print summary
    if 'error' in results:
        logger.error(f"Analysis failed: {results['error']}")
        sys.exit(1)
    elif 'summary' in results:
        summary = results['summary']
        print("\n" + "="*60)
        print("HURRICANE IMPACT ANALYSIS COMPLETE")
        print("="*60)
        print(f"Total Hurricanes: {summary.get('total_hurricanes', 0)}")
        print(f"Total Exposure: ${summary.get('total_exposure', 0):,.2f}")
        print(f"Affected Airports: {summary.get('total_affected_airports', 0)}")
        print(f"Travelers at Risk: {summary.get('total_travelers_at_risk', 0):,}")
        print(f"Potential Claims: {summary.get('total_potential_claims', 0):,}")
        print(f"\nResults saved to: {pipeline.run_output_dir}")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("HURRICANE IMPACT ANALYSIS COMPLETE")
        print("="*60)
        print("No hurricanes found for the specified date range")
        print("="*60)

if __name__ == "__main__":
    main()
