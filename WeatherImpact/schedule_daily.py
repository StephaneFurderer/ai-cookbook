"""
Daily automation script for hurricane impact analysis.
Designed to be run via CRON for automated daily updates.
"""

import argparse
import logging
import sys
import os
from datetime import datetime, timedelta
from typing import Optional
import json

from pipeline import HurricaneImpactPipeline
from config import OUTPUTS_DIR

# Set up logging for CRON environment
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('hurricane_daily_analysis.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class DailyHurricaneAnalysis:
    """Daily automated hurricane analysis system."""
    
    def __init__(self, outputs_dir: str = OUTPUTS_DIR):
        self.outputs_dir = outputs_dir
        self.pipeline = HurricaneImpactPipeline(outputs_dir)
        
        # Create daily outputs directory
        self.daily_output_dir = os.path.join(outputs_dir, "daily")
        os.makedirs(self.daily_output_dir, exist_ok=True)
    
    def run_daily_analysis(self, analysis_date: Optional[str] = None, 
                          lookback_days: int = 1) -> dict:
        """
        Run daily analysis for the specified date or yesterday.
        
        Args:
            analysis_date: Date to analyze (YYYY-MM-DD). If None, uses yesterday.
            lookback_days: Number of days to look back for hurricane data
            
        Returns:
            Dictionary with analysis results
        """
        if analysis_date is None:
            # Use yesterday by default
            yesterday = datetime.now() - timedelta(days=1)
            analysis_date = yesterday.strftime('%Y-%m-%d')
        
        logger.info(f"Starting daily analysis for {analysis_date}")
        
        # Calculate date range
        start_date = (datetime.strptime(analysis_date, '%Y-%m-%d') - 
                     timedelta(days=lookback_days)).strftime('%Y-%m-%d')
        end_date = analysis_date
        
        # Run analysis
        results = self.pipeline.run_analysis(
            start_date=start_date,
            end_date=end_date,
            force_download=False  # Use cached data if available
        )
        
        # Save daily results
        self._save_daily_results(results, analysis_date)
        
        # Generate daily summary
        summary = self._generate_daily_summary(results, analysis_date)
        
        # Send notifications (if configured)
        self._send_notifications(summary, analysis_date)
        
        logger.info(f"Daily analysis completed for {analysis_date}")
        return results
    
    def _save_daily_results(self, results: dict, analysis_date: str):
        """Save daily analysis results."""
        # Save JSON results
        json_file = os.path.join(
            self.daily_output_dir, 
            f"daily_analysis_{analysis_date}.json"
        )
        
        # Prepare results for JSON serialization
        json_results = self._prepare_for_json(results)
        
        with open(json_file, 'w') as f:
            json.dump(json_results, f, indent=2, default=str)
        
        # Save summary
        summary_file = os.path.join(
            self.daily_output_dir,
            f"daily_summary_{analysis_date}.txt"
        )
        
        with open(summary_file, 'w') as f:
            f.write(self._generate_daily_summary(results, analysis_date))
        
        logger.info(f"Daily results saved: {json_file}")
        logger.info(f"Daily summary saved: {summary_file}")
    
    def _generate_daily_summary(self, results: dict, analysis_date: str) -> str:
        """Generate daily summary report."""
        summary = []
        summary.append("=" * 60)
        summary.append(f"DAILY HURRICANE IMPACT ANALYSIS")
        summary.append(f"Analysis Date: {analysis_date}")
        summary.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        summary.append("=" * 60)
        
        if 'error' in results:
            summary.append(f"ANALYSIS FAILED: {results['error']}")
            return "\n".join(summary)
        
        # Pipeline statistics
        summary.append("PIPELINE STATISTICS")
        summary.append("-" * 30)
        summary.append(f"Start Time: {results['pipeline_start_time']}")
        summary.append(f"End Time: {results['pipeline_end_time']}")
        summary.append(f"Duration: {results['pipeline_duration']:.1f} seconds")
        summary.append("")
        
        # Hurricane summary
        summary.append("HURRICANE SUMMARY")
        summary.append("-" * 30)
        hurricane_analyses = results['hurricane_analyses']
        
        if not hurricane_analyses:
            summary.append("No hurricanes found for analysis period")
            return "\n".join(summary)
        
        summary.append(f"Total Hurricanes Analyzed: {len(hurricane_analyses)}")
        summary.append(f"Total Exposure: ${results['total_exposure']:,.2f}")
        summary.append("")
        
        # Individual hurricane details
        for track_id, analysis in hurricane_analyses.items():
            summary.append(f"Hurricane {track_id}:")
            
            # Hurricane characteristics
            hurricane_summary = analysis.get('summary', {})
            summary.append(f"  Peak Intensity: {hurricane_summary.get('peak_category', 'Unknown')}")
            summary.append(f"  Current Status: {hurricane_summary.get('current_category', 'Unknown')}")
            summary.append(f"  Max Wind Speed: {hurricane_summary.get('max_wind_speed', 0):.1f} knots")
            
            # Airport impacts
            affected_airports = analysis['affected_airports']
            summary.append(f"  Affected Airports: {len(affected_airports['affected_airports'])}")
            summary.append(f"  Total Travelers at Risk: {affected_airports['total_daily_travelers']:,}")
            
            # Insurance exposure
            exposure = analysis['exposure']
            summary.append(f"  Total Exposure: ${exposure['total_exposure']:,.2f}")
            summary.append(f"  Potential Claims: {exposure['total_potential_claims']:,}")
            summary.append(f"  Risk Score: {exposure['risk_metrics']['severity_score']:.1f}/100")
            
            # Top affected airport
            if exposure['airport_exposures']:
                top_airport = max(exposure['airport_exposures'], 
                                key=lambda x: x['total_exposure'])
                summary.append(f"  Top Affected Airport: {top_airport['airport_name']} "
                             f"(${top_airport['total_exposure']:,.2f})")
            summary.append("")
        
        # Risk assessment
        summary.append("RISK ASSESSMENT")
        summary.append("-" * 30)
        
        if results['total_exposure'] > 1000000:  # > $1M
            risk_level = "HIGH"
            risk_color = "RED"
        elif results['total_exposure'] > 100000:  # > $100K
            risk_level = "MEDIUM"
            risk_color = "ORANGE"
        else:
            risk_level = "LOW"
            risk_color = "GREEN"
        
        summary.append(f"Overall Risk Level: {risk_level} ({risk_color})")
        summary.append(f"Total Exposure: ${results['total_exposure']:,.2f}")
        
        if hurricane_analyses:
            max_risk_score = max(
                analysis['exposure']['risk_metrics']['severity_score'] 
                for analysis in hurricane_analyses.values()
            )
            summary.append(f"Highest Risk Score: {max_risk_score:.1f}/100")
        
        summary.append("")
        
        # Recommendations
        summary.append("RECOMMENDATIONS")
        summary.append("-" * 30)
        
        if risk_level == "HIGH":
            summary.append("• IMMEDIATE ACTION REQUIRED")
            summary.append("• Review and activate emergency response protocols")
            summary.append("• Consider increasing reserves for potential claims")
            summary.append("• Monitor hurricane development closely")
        elif risk_level == "MEDIUM":
            summary.append("• Monitor situation closely")
            summary.append("• Prepare for potential increase in claims")
            summary.append("• Review current reserves adequacy")
        else:
            summary.append("• Continue routine monitoring")
            summary.append("• No immediate action required")
        
        summary.append("")
        summary.append("=" * 60)
        
        return "\n".join(summary)
    
    def _send_notifications(self, summary: str, analysis_date: str):
        """Send notifications based on analysis results."""
        # For now, just log notifications
        # In a production environment, this could send emails, Slack messages, etc.
        
        # Check if high risk conditions exist
        if "HIGH" in summary and "RED" in summary:
            logger.warning(f"HIGH RISK ALERT for {analysis_date}")
            logger.warning("Immediate attention required - check analysis results")
        
        # Log daily summary
        logger.info(f"Daily analysis summary for {analysis_date}:")
        logger.info(summary)
    
    def _prepare_for_json(self, obj):
        """Prepare object for JSON serialization."""
        if isinstance(obj, dict):
            return {key: self._prepare_for_json(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._prepare_for_json(item) for item in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        else:
            return obj
    
    def cleanup_old_data(self, retention_days: int = 30):
        """Clean up old analysis data to prevent disk space issues."""
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        logger.info(f"Cleaning up data older than {retention_days} days")
        
        # Clean up daily outputs
        if os.path.exists(self.daily_output_dir):
            for filename in os.listdir(self.daily_output_dir):
                filepath = os.path.join(self.daily_output_dir, filename)
                
                if os.path.isfile(filepath):
                    file_age = datetime.fromtimestamp(os.path.getmtime(filepath))
                    if file_age < cutoff_date:
                        os.remove(filepath)
                        logger.info(f"Removed old file: {filename}")
        
        # Clean up main outputs directory
        if os.path.exists(self.outputs_dir):
            for item in os.listdir(self.outputs_dir):
                item_path = os.path.join(self.outputs_dir, item)
                
                if os.path.isdir(item_path) and item.startswith('run_'):
                    # Extract timestamp from directory name
                    try:
                        timestamp_str = item.replace('run_', '')
                        timestamp = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                        
                        if timestamp < cutoff_date:
                            import shutil
                            shutil.rmtree(item_path)
                            logger.info(f"Removed old analysis directory: {item}")
                    except ValueError:
                        # Skip directories that don't match expected format
                        continue

def main():
    """Main function for daily automation."""
    parser = argparse.ArgumentParser(
        description="Daily Hurricane Impact Analysis Automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run daily analysis for yesterday (default)
  python schedule_daily.py
  
  # Run analysis for specific date
  python schedule_daily.py --date 2024-09-24
  
  # Run with custom lookback period
  python schedule_daily.py --lookback-days 3
  
  # Clean up old data
  python schedule_daily.py --cleanup --retention-days 14
        """
    )
    
    parser.add_argument(
        '--date',
        type=str,
        help='Date to analyze (YYYY-MM-DD). Default: yesterday'
    )
    
    parser.add_argument(
        '--lookback-days',
        type=int,
        default=1,
        help='Number of days to look back for hurricane data. Default: 1'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default=OUTPUTS_DIR,
        help=f'Output directory. Default: {OUTPUTS_DIR}'
    )
    
    parser.add_argument(
        '--cleanup',
        action='store_true',
        help='Clean up old analysis data'
    )
    
    parser.add_argument(
        '--retention-days',
        type=int,
        default=30,
        help='Number of days to retain data when cleaning up. Default: 30'
    )
    
    args = parser.parse_args()
    
    # Validate date if provided
    if args.date:
        try:
            datetime.strptime(args.date, '%Y-%m-%d')
        except ValueError:
            logger.error("Invalid date format. Use YYYY-MM-DD")
            sys.exit(1)
    
    # Initialize daily analysis
    daily_analysis = DailyHurricaneAnalysis(args.output_dir)
    
    if args.cleanup:
        # Run cleanup
        daily_analysis.cleanup_old_data(args.retention_days)
        logger.info("Cleanup completed")
    else:
        # Run daily analysis
        results = daily_analysis.run_daily_analysis(
            analysis_date=args.date,
            lookback_days=args.lookback_days
        )
        
        if 'error' in results:
            logger.error(f"Daily analysis failed: {results['error']}")
            sys.exit(1)
        else:
            logger.info("Daily analysis completed successfully")

if __name__ == "__main__":
    main()
