"""
Visualization module for creating interactive maps and dashboards.
"""

import folium
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging
from datetime import datetime
import os

from config import (
    MAP_CENTER,
    MAP_ZOOM,
    DEFAULT_MAP_TILES,
    HURRICANE_COLORS,
    AIRPORT_COLORS,
    OUTPUTS_DIR
)

logger = logging.getLogger(__name__)

class HurricaneVisualizer:
    """Creates interactive visualizations for hurricane impact analysis."""
    
    def __init__(self, outputs_dir: str = OUTPUTS_DIR):
        self.outputs_dir = outputs_dir
        os.makedirs(outputs_dir, exist_ok=True)
    
    def create_interactive_map(self, hurricane_analysis: Dict, 
                             affected_airports: Dict, 
                             exposure: Dict) -> str:
        """
        Create an interactive map showing hurricane track, airports, and impact zones.
        
        Args:
            hurricane_analysis: Hurricane analysis results
            affected_airports: Airport impact analysis
            exposure: Insurance exposure calculations
            
        Returns:
            Path to the generated HTML map file
        """
        # Create base map
        m = folium.Map(
            location=MAP_CENTER,
            zoom_start=MAP_ZOOM,
            tiles=DEFAULT_MAP_TILES
        )
        
        # Add hurricane track
        self._add_hurricane_track(m, hurricane_analysis)
        
        # Add impact zones
        self._add_impact_zones(m, hurricane_analysis)
        
        # Add airports
        self._add_airports(m, affected_airports, exposure)
        
        # Add legend
        self._add_map_legend(m)
        
        # Generate filename and save
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        track_id = hurricane_analysis['track_id']
        filename = f"{track_id}_interactive_map_{timestamp}.html"
        filepath = os.path.join(self.outputs_dir, filename)
        
        m.save(filepath)
        logger.info(f"Interactive map saved to {filepath}")
        
        return filepath
    
    def _add_hurricane_track(self, map_obj: folium.Map, hurricane_analysis: Dict):
        """Add hurricane track to the map."""
        trajectory = hurricane_analysis['trajectory']
        if not trajectory:
            return
        
        coordinates = trajectory['coordinates']
        wind_speeds = trajectory['wind_speeds']
        time_points = trajectory['time_points']
        
        # Create track line
        track_coords = [(coord[0], coord[1]) for coord in coordinates]
        folium.PolyLine(
            track_coords,
            color='red',
            weight=4,
            opacity=0.8,
            popup=f"Hurricane {hurricane_analysis['track_id']} Track"
        ).add_to(map_obj)
        
        # Add track points with wind speed information
        for i, (coord, wind_speed, time_point) in enumerate(zip(coordinates, wind_speeds, time_points)):
            color = self._get_hurricane_color(wind_speed)
            radius = max(5, min(15, wind_speed / 10))  # Radius based on wind speed
            
            popup_text = f"""
            <b>Hurricane Position</b><br>
            Time: {time_point.strftime('%Y-%m-%d %H:%M')}<br>
            Wind Speed: {wind_speed:.1f} knots<br>
            Category: {self._get_category_from_wind_speed(wind_speed)}<br>
            Position: {coord[0]:.3f}°, {coord[1]:.3f}°
            """
            
            folium.CircleMarker(
                location=coord,
                radius=radius,
                popup=folium.Popup(popup_text, max_width=200),
                color='black',
                weight=2,
                fillColor=color,
                fillOpacity=0.7
            ).add_to(map_obj)
    
    def _add_impact_zones(self, map_obj: folium.Map, hurricane_analysis: Dict):
        """Add impact zones to the map."""
        impact_zones = hurricane_analysis['impact_zones']
        if not impact_zones or 'impact_points' not in impact_zones:
            return
        
        for impact_point in impact_zones['impact_points']:
            center = impact_point['center']
            radius_km = impact_point['radius_km']
            wind_speed = impact_point['wind_speed']
            time = impact_point['time']
            
            # Create impact zone circle
            folium.Circle(
                location=center,
                radius=radius_km * 1000,  # Convert km to meters
                popup=f"""
                <b>Impact Zone</b><br>
                Time: {time.strftime('%Y-%m-%d %H:%M')}<br>
                Wind Speed: {wind_speed:.1f} knots<br>
                Radius: {radius_km:.0f} km<br>
                Category: {self._get_category_from_wind_speed(wind_speed)}
                """,
                color='orange',
                weight=2,
                fillColor='orange',
                fillOpacity=0.1
            ).add_to(map_obj)
    
    def _add_airports(self, map_obj: folium.Map, affected_airports: Dict, exposure: Dict):
        """Add airports to the map with exposure information."""
        airport_exposures = {exp['airport_code']: exp for exp in exposure['airport_exposures']}
        
        for airport in affected_airports['affected_airports']:
            airport_code = airport['airport_code']
            coords = airport['coordinates']
            impact_level = airport['impact_level']
            exposure_data = airport_exposures.get(airport_code, {})
            
            # Determine marker color based on impact level
            color = self._get_airport_color(impact_level)
            
            # Create popup text
            popup_text = f"""
            <b>{airport['airport_name']}</b><br>
            Code: {airport_code}<br>
            Region: {airport['region']}<br>
            Impact Level: {impact_level.title()}<br>
            Daily Passengers: {airport['daily_passengers']:,}<br>
            Estimated Delay: {airport['estimated_delay_hours']:.1f} hours<br>
            Disruption Probability: {airport['flight_disruption_probability']:.1%}<br>
            <hr>
            <b>Insurance Exposure</b><br>
            Total Exposure: ${exposure_data.get('total_exposure', 0):,.2f}<br>
            Potential Claims: {exposure_data.get('potential_claims', 0):,}<br>
            Exposure per Passenger: ${exposure_data.get('exposure_per_passenger', 0):.2f}
            """
            
            # Add airport marker
            folium.CircleMarker(
                location=coords,
                radius=max(8, min(20, airport['daily_passengers'] / 5000)),  # Size based on passenger volume
                popup=folium.Popup(popup_text, max_width=300),
                color='black',
                weight=2,
                fillColor=color,
                fillOpacity=0.8
            ).add_to(map_obj)
    
    def _add_map_legend(self, map_obj: folium.Map):
        """Add legend to the map."""
        legend_html = """
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 200px; height: 200px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <p><b>Hurricane Impact Map</b></p>
        <p><i class="fa fa-circle" style="color:red"></i> Hurricane Track</p>
        <p><i class="fa fa-circle" style="color:orange"></i> Impact Zones</p>
        <p><b>Airports by Impact:</b></p>
        <p><i class="fa fa-circle" style="color:gray"></i> No Impact</p>
        <p><i class="fa fa-circle" style="color:gold"></i> Low Impact</p>
        <p><i class="fa fa-circle" style="color:darkorange"></i> Medium Impact</p>
        <p><i class="fa fa-circle" style="color:crimson"></i> High Impact</p>
        <p><b>Marker Size:</b> Passenger Volume</p>
        </div>
        """
        map_obj.get_root().html.add_child(folium.Element(legend_html))
    
    def create_dashboard(self, hurricane_analysis: Dict, 
                        affected_airports: Dict, 
                        exposure: Dict) -> str:
        """
        Create an interactive dashboard with charts and KPIs.
        
        Args:
            hurricane_analysis: Hurricane analysis results
            affected_airports: Airport impact analysis
            exposure: Insurance exposure calculations
            
        Returns:
            Path to the generated HTML dashboard file
        """
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Exposure by Airport', 'Exposure by Region', 
                          'Impact Level Distribution', 'Time Series Exposure'),
            specs=[[{"type": "bar"}, {"type": "pie"}],
                   [{"type": "bar"}, {"type": "scatter"}]]
        )
        
        # 1. Exposure by Airport (top airports)
        top_airports = sorted(
            exposure['airport_exposures'],
            key=lambda x: x['total_exposure'],
            reverse=True
        )[:10]
        
        airport_names = [ap['airport_name'][:20] + '...' if len(ap['airport_name']) > 20 
                        else ap['airport_name'] for ap in top_airports]
        airport_exposures = [ap['total_exposure'] for ap in top_airports]
        
        fig.add_trace(
            go.Bar(
                x=airport_names,
                y=airport_exposures,
                name='Exposure by Airport',
                marker_color='lightblue'
            ),
            row=1, col=1
        )
        
        # 2. Exposure by Region (pie chart)
        region_data = exposure['exposure_by_region']
        regions = list(region_data.keys())
        region_exposures = [region_data[region]['total_exposure'] for region in regions]
        
        fig.add_trace(
            go.Pie(
                labels=regions,
                values=region_exposures,
                name='Exposure by Region'
            ),
            row=1, col=2
        )
        
        # 3. Impact Level Distribution
        impact_data = exposure['exposure_by_impact_level']
        impact_levels = list(impact_data.keys())
        impact_counts = [impact_data[level]['airports'] for level in impact_levels]
        
        fig.add_trace(
            go.Bar(
                x=impact_levels,
                y=impact_counts,
                name='Airports by Impact Level',
                marker_color=['gray', 'gold', 'darkorange', 'crimson']
            ),
            row=2, col=1
        )
        
        # 4. Hurricane Intensity Over Time (if available)
        trajectory = hurricane_analysis['trajectory']
        if trajectory and 'time_points' in trajectory:
            times = trajectory['time_points']
            wind_speeds = trajectory['wind_speeds']
            
            fig.add_trace(
                go.Scatter(
                    x=times,
                    y=wind_speeds,
                    mode='lines+markers',
                    name='Wind Speed Over Time',
                    line=dict(color='red', width=3)
                ),
                row=2, col=2
            )
        
        # Update layout
        fig.update_layout(
            title=f"Hurricane {hurricane_analysis['track_id']} - Insurance Impact Dashboard",
            height=800,
            showlegend=False
        )
        
        # Add KPI cards
        kpi_html = self._create_kpi_cards(exposure, affected_airports)
        
        # Generate filename and save
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        track_id = hurricane_analysis['track_id']
        filename = f"{track_id}_dashboard_{timestamp}.html"
        filepath = os.path.join(self.outputs_dir, filename)
        
        # Save with KPI cards
        fig.write_html(
            filepath,
            include_plotlyjs=True,
            div_id="dashboard",
            config={'displayModeBar': True}
        )
        
        # Add KPI cards to the HTML
        self._add_kpi_cards_to_html(filepath, kpi_html)
        
        logger.info(f"Dashboard saved to {filepath}")
        return filepath
    
    def _create_kpi_cards(self, exposure: Dict, affected_airports: Dict) -> str:
        """Create KPI cards HTML."""
        kpi_html = f"""
        <div style="display: flex; justify-content: space-around; margin-bottom: 20px; padding: 20px; background-color: #f8f9fa;">
            <div style="text-align: center; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h3 style="color: #dc3545; margin: 0;">${exposure['total_exposure']:,.0f}</h3>
                <p style="margin: 5px 0; color: #666;">Total Exposure</p>
            </div>
            <div style="text-align: center; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h3 style="color: #fd7e14; margin: 0;">{exposure['total_potential_claims']:,}</h3>
                <p style="margin: 5px 0; color: #666;">Potential Claims</p>
            </div>
            <div style="text-align: center; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h3 style="color: #20c997; margin: 0;">{affected_airports['impact_summary']['total_airports']}</h3>
                <p style="margin: 5px 0; color: #666;">Affected Airports</p>
            </div>
            <div style="text-align: center; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h3 style="color: #6f42c1; margin: 0;">{exposure['risk_metrics']['severity_score']:.1f}</h3>
                <p style="margin: 5px 0; color: #666;">Risk Score</p>
            </div>
        </div>
        """
        return kpi_html
    
    def _add_kpi_cards_to_html(self, filepath: str, kpi_html: str):
        """Add KPI cards to the HTML dashboard."""
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Insert KPI cards after the opening body tag
        content = content.replace('<body>', f'<body>{kpi_html}')
        
        with open(filepath, 'w') as f:
            f.write(content)
    
    def _get_hurricane_color(self, wind_speed: float) -> str:
        """Get color for hurricane based on wind speed."""
        if wind_speed < 34:
            return HURRICANE_COLORS['tropical_depression']
        elif wind_speed < 64:
            return HURRICANE_COLORS['tropical_storm']
        elif wind_speed < 83:
            return HURRICANE_COLORS['category_1']
        elif wind_speed < 96:
            return HURRICANE_COLORS['category_2']
        elif wind_speed < 113:
            return HURRICANE_COLORS['category_3']
        elif wind_speed < 137:
            return HURRICANE_COLORS['category_4']
        else:
            return HURRICANE_COLORS['category_5']
    
    def _get_category_from_wind_speed(self, wind_speed: float) -> str:
        """Get hurricane category from wind speed."""
        if wind_speed < 34:
            return 'Tropical Depression'
        elif wind_speed < 64:
            return 'Tropical Storm'
        elif wind_speed < 83:
            return 'Category 1'
        elif wind_speed < 96:
            return 'Category 2'
        elif wind_speed < 113:
            return 'Category 3'
        elif wind_speed < 137:
            return 'Category 4'
        else:
            return 'Category 5'
    
    def _get_airport_color(self, impact_level: str) -> str:
        """Get color for airport based on impact level."""
        return AIRPORT_COLORS.get(impact_level, AIRPORT_COLORS['no_impact'])
    
    def create_exposure_timeline(self, exposure_history: List[Dict]) -> str:
        """
        Create a timeline visualization of exposure over time.
        
        Args:
            exposure_history: List of exposure calculations over time
            
        Returns:
            Path to the generated HTML file
        """
        if not exposure_history:
            return None
        
        # Prepare data
        dates = [exp['calculation_timestamp'] for exp in exposure_history]
        exposures = [exp['total_exposure'] for exp in exposure_history]
        claims = [exp['total_potential_claims'] for exp in exposure_history]
        
        # Create figure
        fig = go.Figure()
        
        # Add exposure line
        fig.add_trace(go.Scatter(
            x=dates,
            y=exposures,
            mode='lines+markers',
            name='Total Exposure',
            line=dict(color='red', width=3),
            yaxis='y'
        ))
        
        # Add claims line (on secondary y-axis)
        fig.add_trace(go.Scatter(
            x=dates,
            y=claims,
            mode='lines+markers',
            name='Potential Claims',
            line=dict(color='blue', width=3),
            yaxis='y2'
        ))
        
        # Update layout
        fig.update_layout(
            title='Insurance Exposure Timeline',
            xaxis_title='Date',
            yaxis=dict(
                title='Total Exposure ($)',
                side='left',
                tickformat='$,.0f'
            ),
            yaxis2=dict(
                title='Potential Claims',
                side='right',
                overlaying='y',
                tickformat=',.0f'
            ),
            height=500
        )
        
        # Save
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"exposure_timeline_{timestamp}.html"
        filepath = os.path.join(self.outputs_dir, filename)
        
        fig.write_html(filepath, include_plotlyjs=True)
        logger.info(f"Exposure timeline saved to {filepath}")
        
        return filepath

def main():
    """Example usage of HurricaneVisualizer."""
    from data_fetcher import HurricaneDataFetcher
    from hurricane_analyzer import HurricaneAnalyzer
    from airport_impact import AirportImpact
    from insurance_calculator import InsuranceCalculator
    
    # Load and analyze Hurricane Helene data
    fetcher = HurricaneDataFetcher()
    data = fetcher.download_hurricane_data("2024-09-23")
    
    if data is not None:
        analyzer = HurricaneAnalyzer()
        hurricanes = analyzer.load_hurricane_data(data)
        
        airport_impact = AirportImpact()
        airport_impact.load_airport_data()
        
        calculator = InsuranceCalculator()
        visualizer = HurricaneVisualizer()
        
        for track_id, hurricane_data in hurricanes.items():
            analysis = analyzer.analyze_hurricane(hurricane_data)
            affected = airport_impact.find_affected_airports(analysis)
            exposure = calculator.calculate_exposure(affected)
            
            # Create visualizations
            map_file = visualizer.create_interactive_map(analysis, affected, exposure)
            dashboard_file = visualizer.create_dashboard(analysis, affected, exposure)
            
            print(f"Visualizations created for Hurricane {track_id}:")
            print(f"  Interactive Map: {map_file}")
            print(f"  Dashboard: {dashboard_file}")

if __name__ == "__main__":
    main()
