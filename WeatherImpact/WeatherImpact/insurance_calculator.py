"""
Insurance calculator module for estimating flight delay insurance exposure and claims.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging
from datetime import datetime, timedelta

from .config import INSURANCE_PARAMS

logger = logging.getLogger(__name__)

class InsuranceCalculator:
    """Calculates insurance exposure and potential claims for flight delay coverage."""
    
    def __init__(self, insurance_params: Optional[Dict] = None):
        """
        Initialize insurance calculator.
        
        Args:
            insurance_params: Insurance parameters (uses config defaults if None)
        """
        self.params = insurance_params or INSURANCE_PARAMS
        self.exposure_history = []
        
    def calculate_exposure(self, affected_airports: Dict) -> Dict:
        """
        Calculate total insurance exposure for affected airports.
        
        Args:
            affected_airports: Airport impact analysis result
            
        Returns:
            Dictionary with exposure calculations
        """
        track_id = affected_airports['track_id']
        affected_list = affected_airports['affected_airports']
        
        exposure = {
            'track_id': track_id,
            'calculation_timestamp': datetime.now(),
            'insurance_params': self.params.copy(),
            'airport_exposures': [],
            'total_exposure': 0.0,
            'total_potential_claims': 0,
            'total_potential_payout': 0.0,
            'exposure_by_impact_level': {},
            'exposure_by_region': {},
            'risk_metrics': {}
        }
        
        # Calculate exposure for each affected airport
        for airport in affected_list:
            airport_exposure = self._calculate_airport_exposure(airport)
            exposure['airport_exposures'].append(airport_exposure)
            exposure['total_exposure'] += airport_exposure['total_exposure']
            exposure['total_potential_claims'] += airport_exposure['potential_claims']
            exposure['total_potential_payout'] += airport_exposure['potential_payout']
        
        # Calculate exposure by impact level
        exposure['exposure_by_impact_level'] = self._calculate_exposure_by_impact_level(
            exposure['airport_exposures']
        )
        
        # Calculate exposure by region
        exposure['exposure_by_region'] = self._calculate_exposure_by_region(
            exposure['airport_exposures']
        )
        
        # Calculate risk metrics
        exposure['risk_metrics'] = self._calculate_risk_metrics(
            exposure, affected_airports
        )
        
        # Store in history
        self.exposure_history.append(exposure)
        
        logger.info(f"Calculated total exposure: ${exposure['total_exposure']:,.2f} "
                   f"for {exposure['total_potential_claims']:,} potential claims")
        
        return exposure
    
    def _calculate_airport_exposure(self, airport: Dict) -> Dict:
        """
        Calculate exposure for a single airport.
        
        Args:
            airport: Airport impact assessment
            
        Returns:
            Dictionary with airport exposure calculations
        """
        daily_passengers = airport['daily_passengers']
        disruption_probability = airport['flight_disruption_probability']
        estimated_delay_hours = airport['estimated_delay_hours']
        
        # Calculate coverage penetration
        coverage_holders = int(daily_passengers * self.params['penetration_rate'])
        
        # Calculate affected coverage holders (those in impact zone during disruption)
        affected_coverage_holders = int(coverage_holders * disruption_probability)
        
        # Calculate potential claims (those who will actually file)
        potential_claims = int(affected_coverage_holders * self.params['claim_rate'])
        
        # Calculate financial exposure
        potential_payout = potential_claims * self.params['payout_per_claim']
        
        # Calculate additional costs (administrative, processing, etc.)
        administrative_cost_rate = 0.15  # 15% of payouts for admin costs
        total_exposure = potential_payout * (1 + administrative_cost_rate)
        
        airport_exposure = {
            'airport_code': airport['airport_code'],
            'airport_name': airport['airport_name'],
            'region': airport['region'],
            'impact_level': airport['impact_level'],
            'daily_passengers': daily_passengers,
            'coverage_holders': coverage_holders,
            'affected_coverage_holders': affected_coverage_holders,
            'potential_claims': potential_claims,
            'claim_rate': potential_claims / max(1, coverage_holders),
            'potential_payout': potential_payout,
            'administrative_costs': potential_payout * administrative_cost_rate,
            'total_exposure': total_exposure,
            'exposure_per_passenger': total_exposure / max(1, daily_passengers),
            'estimated_delay_hours': estimated_delay_hours,
            'disruption_probability': disruption_probability
        }
        
        return airport_exposure
    
    def _calculate_exposure_by_impact_level(self, airport_exposures: List[Dict]) -> Dict:
        """Calculate exposure aggregated by impact level."""
        impact_levels = {}
        
        for exposure in airport_exposures:
            level = exposure['impact_level']
            if level not in impact_levels:
                impact_levels[level] = {
                    'airports': 0,
                    'total_exposure': 0.0,
                    'potential_claims': 0,
                    'total_passengers': 0
                }
            
            impact_levels[level]['airports'] += 1
            impact_levels[level]['total_exposure'] += exposure['total_exposure']
            impact_levels[level]['potential_claims'] += exposure['potential_claims']
            impact_levels[level]['total_passengers'] += exposure['daily_passengers']
        
        # Calculate averages
        for level_data in impact_levels.values():
            if level_data['airports'] > 0:
                level_data['avg_exposure_per_airport'] = (
                    level_data['total_exposure'] / level_data['airports']
                )
                level_data['avg_claims_per_airport'] = (
                    level_data['potential_claims'] / level_data['airports']
                )
        
        return impact_levels
    
    def _calculate_exposure_by_region(self, airport_exposures: List[Dict]) -> Dict:
        """Calculate exposure aggregated by geographic region."""
        regions = {}
        
        for exposure in airport_exposures:
            region = exposure['region']
            if region not in regions:
                regions[region] = {
                    'airports': 0,
                    'total_exposure': 0.0,
                    'potential_claims': 0,
                    'total_passengers': 0,
                    'impact_levels': {}
                }
            
            regions[region]['airports'] += 1
            regions[region]['total_exposure'] += exposure['total_exposure']
            regions[region]['potential_claims'] += exposure['potential_claims']
            regions[region]['total_passengers'] += exposure['daily_passengers']
            
            # Track impact levels by region
            impact_level = exposure['impact_level']
            if impact_level not in regions[region]['impact_levels']:
                regions[region]['impact_levels'][impact_level] = 0
            regions[region]['impact_levels'][impact_level] += 1
        
        # Calculate percentages and averages
        total_exposure = sum(r['total_exposure'] for r in regions.values())
        for region_data in regions.values():
            if total_exposure > 0:
                region_data['exposure_percentage'] = (
                    region_data['total_exposure'] / total_exposure * 100
                )
            if region_data['airports'] > 0:
                region_data['avg_exposure_per_airport'] = (
                    region_data['total_exposure'] / region_data['airports']
                )
        
        return regions
    
    def _calculate_risk_metrics(self, exposure: Dict, affected_airports: Dict) -> Dict:
        """Calculate overall risk metrics for the hurricane."""
        total_passengers = affected_airports['total_daily_travelers']
        total_airports = len(affected_airports['affected_airports'])
        
        risk_metrics = {
            'total_passengers_at_risk': total_passengers,
            'total_affected_airports': total_airports,
            'exposure_per_passenger': (
                exposure['total_exposure'] / max(1, total_passengers)
            ),
            'exposure_per_airport': (
                exposure['total_exposure'] / max(1, total_airports)
            ),
            'claim_rate_overall': (
                exposure['total_potential_claims'] / max(1, total_passengers * self.params['penetration_rate'])
            ),
            'severity_score': self._calculate_severity_score(exposure, affected_airports),
            'concentration_risk': self._calculate_concentration_risk(exposure['airport_exposures'])
        }
        
        return risk_metrics
    
    def _calculate_severity_score(self, exposure: Dict, affected_airports: Dict) -> float:
        """
        Calculate a severity score (0-100) based on exposure and impact.
        
        Higher scores indicate more severe potential impact.
        """
        # Base score from total exposure
        exposure_score = min(50, exposure['total_exposure'] / 100000)  # Max 50 points
        
        # Impact level multiplier
        impact_multiplier = 1.0
        for airport_exposure in exposure['airport_exposures']:
            if airport_exposure['impact_level'] == 'high':
                impact_multiplier += 0.3
            elif airport_exposure['impact_level'] == 'medium':
                impact_multiplier += 0.2
            elif airport_exposure['impact_level'] == 'low':
                impact_multiplier += 0.1
        
        # Geographic concentration factor
        concentration_factor = min(1.5, len(exposure['airport_exposures']) / 10)
        
        # Calculate final score
        severity_score = exposure_score * impact_multiplier * concentration_factor
        
        return min(100, severity_score)
    
    def _calculate_concentration_risk(self, airport_exposures: List[Dict]) -> Dict:
        """Calculate concentration risk metrics."""
        if not airport_exposures:
            return {'concentration_ratio': 0.0, 'top_5_percentage': 0.0}
        
        # Sort by exposure
        sorted_exposures = sorted(
            airport_exposures, 
            key=lambda x: x['total_exposure'], 
            reverse=True
        )
        
        total_exposure = sum(exp['total_exposure'] for exp in airport_exposures)
        
        # Top 5 airports concentration
        top_5_exposure = sum(exp['total_exposure'] for exp in sorted_exposures[:5])
        top_5_percentage = (top_5_exposure / max(1, total_exposure)) * 100
        
        # Calculate Herfindahl-Hirschman Index (concentration measure)
        market_shares = [exp['total_exposure'] / max(1, total_exposure) for exp in airport_exposures]
        hhi = sum(share ** 2 for share in market_shares) * 10000
        
        return {
            'concentration_ratio': hhi,
            'top_5_percentage': top_5_percentage,
            'max_single_airport_share': max(market_shares) * 100 if market_shares else 0
        }
    
    def calculate_time_series_exposure(self, affected_airports: Dict, 
                                     time_horizon_days: int = 7) -> Dict:
        """
        Calculate exposure over time for the hurricane.
        
        Args:
            affected_airports: Airport impact analysis
            time_horizon_days: Number of days to project forward
            
        Returns:
            Dictionary with time series exposure data
        """
        track_id = affected_airports['track_id']
        
        # Create time series (assuming daily updates)
        time_series = {
            'track_id': track_id,
            'time_horizon_days': time_horizon_days,
            'daily_exposures': [],
            'cumulative_exposure': 0.0,
            'peak_exposure_day': None,
            'peak_exposure_amount': 0.0
        }
        
        # For now, assume constant exposure over time
        # In a more sophisticated model, this would vary based on hurricane movement
        daily_exposure = self.calculate_exposure(affected_airports)
        base_exposure = daily_exposure['total_exposure']
        
        for day in range(time_horizon_days):
            # Simulate exposure decay over time (hurricane moves away)
            decay_factor = max(0.1, 1.0 - (day / time_horizon_days) * 0.8)
            day_exposure = base_exposure * decay_factor
            
            daily_data = {
                'day': day + 1,
                'exposure': day_exposure,
                'cumulative_exposure': time_series['cumulative_exposure'] + day_exposure,
                'decay_factor': decay_factor
            }
            
            time_series['daily_exposures'].append(daily_data)
            time_series['cumulative_exposure'] += day_exposure
            
            # Track peak exposure
            if day_exposure > time_series['peak_exposure_amount']:
                time_series['peak_exposure_amount'] = day_exposure
                time_series['peak_exposure_day'] = day + 1
        
        return time_series
    
    def generate_exposure_report(self, exposure: Dict) -> str:
        """
        Generate a human-readable exposure report.
        
        Args:
            exposure: Exposure calculation results
            
        Returns:
            Formatted report string
        """
        report = []
        report.append("=" * 60)
        report.append(f"HURRICANE INSURANCE EXPOSURE REPORT")
        report.append(f"Hurricane ID: {exposure['track_id']}")
        report.append(f"Analysis Date: {exposure['calculation_timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 60)
        
        # Summary
        report.append("\nEXECUTIVE SUMMARY")
        report.append("-" * 20)
        report.append(f"Total Exposure: ${exposure['total_exposure']:,.2f}")
        report.append(f"Potential Claims: {exposure['total_potential_claims']:,}")
        report.append(f"Potential Payout: ${exposure['total_potential_payout']:,.2f}")
        report.append(f"Administrative Costs: ${exposure['total_exposure'] - exposure['total_potential_payout']:,.2f}")
        
        # Risk metrics
        risk = exposure['risk_metrics']
        report.append(f"\nRISK METRICS")
        report.append("-" * 20)
        report.append(f"Severity Score: {risk['severity_score']:.1f}/100")
        report.append(f"Exposure per Passenger: ${risk['exposure_per_passenger']:.2f}")
        report.append(f"Overall Claim Rate: {risk['claim_rate_overall']:.1%}")
        
        # Top affected airports
        sorted_airports = sorted(
            exposure['airport_exposures'],
            key=lambda x: x['total_exposure'],
            reverse=True
        )
        
        report.append(f"\nTOP 5 AFFECTED AIRPORTS")
        report.append("-" * 25)
        for i, airport in enumerate(sorted_airports[:5], 1):
            report.append(f"{i}. {airport['airport_name']} ({airport['airport_code']})")
            report.append(f"   Exposure: ${airport['total_exposure']:,.2f}")
            report.append(f"   Potential Claims: {airport['potential_claims']:,}")
            report.append(f"   Impact Level: {airport['impact_level']}")
        
        # Regional breakdown
        report.append(f"\nREGIONAL EXPOSURE BREAKDOWN")
        report.append("-" * 30)
        for region, data in exposure['exposure_by_region'].items():
            report.append(f"{region}:")
            report.append(f"  Exposure: ${data['total_exposure']:,.2f} ({data['exposure_percentage']:.1f}%)")
            report.append(f"  Airports: {data['airports']}")
            report.append(f"  Claims: {data['potential_claims']:,}")
        
        return "\n".join(report)
    
    def export_exposure_data(self, exposure: Dict, filename: Optional[str] = None) -> str:
        """
        Export exposure data to CSV file.
        
        Args:
            exposure: Exposure calculation results
            filename: Output filename (auto-generated if None)
            
        Returns:
            Path to exported file
        """
        if filename is None:
            timestamp = exposure['calculation_timestamp'].strftime('%Y%m%d_%H%M%S')
            filename = f"exposure_report_{exposure['track_id']}_{timestamp}.csv"
        
        # Create DataFrame from airport exposures
        df = pd.DataFrame(exposure['airport_exposures'])
        
        # Add additional columns
        df['track_id'] = exposure['track_id']
        df['calculation_date'] = exposure['calculation_timestamp']
        
        # Export to CSV
        df.to_csv(filename, index=False)
        
        logger.info(f"Exported exposure data to {filename}")
        return filename

def main():
    """Example usage of InsuranceCalculator."""
    from data_fetcher import HurricaneDataFetcher
    from hurricane_analyzer import HurricaneAnalyzer
    from airport_impact import AirportImpact
    
    # Load Hurricane Helene data
    fetcher = HurricaneDataFetcher()
    data = fetcher.download_hurricane_data("2024-09-23")
    
    if data is not None:
        # Analyze hurricane and find affected airports
        analyzer = HurricaneAnalyzer()
        hurricanes = analyzer.load_hurricane_data(data)
        
        airport_impact = AirportImpact()
        airport_impact.load_airport_data()
        
        # Calculate insurance exposure
        calculator = InsuranceCalculator()
        
        for track_id, hurricane_data in hurricanes.items():
            analysis = analyzer.analyze_hurricane(hurricane_data)
            affected = airport_impact.find_affected_airports(analysis)
            exposure = calculator.calculate_exposure(affected)
            
            print(f"\nHurricane {track_id} - Insurance Exposure:")
            print(f"Total Exposure: ${exposure['total_exposure']:,.2f}")
            print(f"Potential Claims: {exposure['total_potential_claims']:,}")
            print(f"Risk Score: {exposure['risk_metrics']['severity_score']:.1f}/100")
            
            # Generate report
            report = calculator.generate_exposure_report(exposure)
            print(f"\n{report}")

if __name__ == "__main__":
    main()
