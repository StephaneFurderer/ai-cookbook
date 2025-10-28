"""
Streamlit Hurricane Risk Dashboard

Multi-page application for visualizing airport traveler risk from hurricanes.
"""

import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import io
import sys
import os

# Add WeatherImpact to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from WeatherImpact.traveler_risk import TravelerRiskCalculator
from WeatherImpact.risk_engine import RiskEngine
from WeatherImpact.hurricane_data_loader import HurricaneDataLoader
from WeatherImpact.config import MAJOR_AIRPORTS, MAP_CENTER

# Page configuration
st.set_page_config(
    page_title="Hurricane Risk Dashboard",
    page_icon="🌀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'traveler_calculator' not in st.session_state:
    st.session_state.traveler_calculator = TravelerRiskCalculator()
if 'risk_engine' not in st.session_state:
    st.session_state.risk_engine = RiskEngine()
if 'hurricane_loader' not in st.session_state:
    st.session_state.hurricane_loader = HurricaneDataLoader()

def main():
    """Main application entry point."""
    st.title("🌀 Hurricane Risk Dashboard")
    st.markdown("---")
    
    # Sidebar navigation
    page = st.sidebar.selectbox(
        "Select Page",
        [
            "Current Risk Exposure",
            "Seasonality Model", 
            "2-Week Forecast",
            "Hurricane Risk Modeling"
        ]
    )
    
    # Route to appropriate page
    if page == "Current Risk Exposure":
        show_current_risk_page()
    elif page == "Seasonality Model":
        show_seasonality_page()
    elif page == "2-Week Forecast":
        show_forecast_page()
    elif page == "Hurricane Risk Modeling":
        show_hurricane_modeling_page()

def show_current_risk_page():
    """Page 1: Current Risk Exposure with map and airport markers."""
    st.header("Current Risk Exposure")
    
    # Date selector
    selected_date = st.date_input(
        "Select Analysis Date",
        value=datetime.now().date(),
        help="Choose the date to analyze current risk exposure"
    )
    
    # Load hurricane data for selected date
    hurricane_analyses = load_hurricane_data_for_date(selected_date)
    
    # Calculate current risk
    risk_exposure = calculate_current_risk(selected_date, hurricane_analyses)
    
    # Sidebar metrics
    st.sidebar.metric("Total Travelers at Risk", f"{risk_exposure['total_travelers_at_risk']:,}")
    st.sidebar.metric("Airports at Risk", len(risk_exposure['airports_at_risk']))
    st.sidebar.metric("Active Hurricanes", len(hurricane_analyses))
    
    # Top 5 most impacted airports
    if risk_exposure['airports_at_risk']:
        st.sidebar.subheader("Top 5 Most Impacted Airports")
        
        # Calculate travelers for each airport at risk
        airport_risk_data = []
        for airport_code in risk_exposure['airports_at_risk']:
            travelers = st.session_state.traveler_calculator.calculate_daily_travelers(
                airport_code, datetime.combine(risk_exposure['date'], datetime.min.time())
            )
            airport_name = MAJOR_AIRPORTS[airport_code]['name']
            airport_risk_data.append({
                'airport_code': airport_code,
                'airport_name': airport_name,
                'travelers_at_risk': travelers
            })
        
        # Sort by travelers at risk
        top_airports = sorted(
            airport_risk_data, 
            key=lambda x: x['travelers_at_risk'], 
            reverse=True
        )[:5]
        
        for i, airport in enumerate(top_airports, 1):
            st.sidebar.write(f"{i}. {airport['airport_name']}: {airport['travelers_at_risk']:,}")
    
    # Create map
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Airport Risk Map")
        risk_map = create_risk_map(risk_exposure, hurricane_analyses)
        st_folium(risk_map, width=700, height=500)
    
    with col2:
        st.subheader("Risk Summary")
        
        # Regional breakdown
        if risk_exposure['regional_breakdown']:
            st.write("**Regional Impact:**")
            for region, data in risk_exposure['regional_breakdown'].items():
                st.write(f"• {region}: {data['total_travelers']:,} travelers")
        
        # Hurricane details
        if hurricane_analyses:
            st.write("**Active Hurricanes:**")
            for track_id, analysis in hurricane_analyses.items():
                summary = analysis.get('summary', {})
                st.write(f"• {track_id}: {summary.get('current_category', 'Unknown')}")
    
    # Data table
    st.subheader("All Airports Data")
    airports_df = create_airports_dataframe(selected_date)
    st.dataframe(airports_df, use_container_width=True)

def show_seasonality_page():
    """Page 2: Seasonality Model with charts and adjustable parameters."""
    st.header("Seasonality Model")
    
    # Date picker
    selected_date = st.date_input(
        "Select Analysis Date",
        value=datetime.now().date(),
        help="Choose the date to analyze seasonality"
    )
    
    # Airport selector
    airport_options = [f"{code} - {info['name']}" for code, info in MAJOR_AIRPORTS.items()]
    selected_airport_display = st.selectbox("Select Airport", airport_options)
    selected_airport_code = selected_airport_display.split(' - ')[0]
    
    # Generate 12-month forecast
    start_date = datetime(selected_date.year, 1, 1)
    forecast_data = st.session_state.traveler_calculator.get_travelers_forecast(
        selected_airport_code, start_date, 365
    )
    
    # Monthly aggregation
    monthly_data = forecast_data.groupby(forecast_data['date'].dt.month).agg({
        'expected_travelers': 'mean',
        'seasonal_factor': 'mean',
        'holiday_multiplier': 'mean',
        'dow_multiplier': 'mean'
    }).reset_index()
    
    monthly_data['month_name'] = monthly_data['date'].map({
        1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
        7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
    })
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("12-Month Traveler Forecast")
        fig = px.line(
            monthly_data, 
            x='month_name', 
            y='expected_travelers',
            title=f"Monthly Travelers for {selected_airport_code}"
        )
        fig.update_layout(xaxis_title="Month", yaxis_title="Expected Travelers")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Seasonality Factors")
        fig = px.bar(
            monthly_data,
            x='month_name',
            y='seasonal_factor',
            title="Seasonal Multipliers"
        )
        fig.update_layout(xaxis_title="Month", yaxis_title="Seasonal Factor")
        st.plotly_chart(fig, use_container_width=True)
    
    # Regional comparison
    st.subheader("Regional Comparison")
    regional_data = []
    
    for region in ['Caribbean', 'Florida', 'US_East_Coast', 'Gulf_Coast']:
        region_airports = [
            code for code, info in MAJOR_AIRPORTS.items()
            if st.session_state.traveler_calculator._determine_region(info['lat'], info['lon']) == region
        ]
        
        if region_airports:
            region_travelers = sum(
                st.session_state.traveler_calculator.calculate_daily_travelers(code, selected_date)
                for code in region_airports
            )
            regional_data.append({
                'region': region,
                'total_travelers': region_travelers,
                'airport_count': len(region_airports)
            })
    
    if regional_data:
        regional_df = pd.DataFrame(regional_data)
        fig = px.bar(
            regional_df,
            x='region',
            y='total_travelers',
            title="Total Travelers by Region"
        )
        fig.update_layout(xaxis_title="Region", yaxis_title="Total Travelers")
        st.plotly_chart(fig, use_container_width=True)
    
    # Adjustable parameters
    st.subheader("Adjustable Parameters")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**Holiday Multipliers**")
        thanksgiving_mult = st.slider("Thanksgiving Week", 1.0, 3.0, 1.8, 0.1)
        christmas_mult = st.slider("Christmas Week", 1.0, 3.0, 2.0, 0.1)
        spring_break_mult = st.slider("Spring Break", 1.0, 2.0, 1.4, 0.1)
    
    with col2:
        st.write("**Seasonal Factors**")
        winter_mult = st.slider("Winter (Dec-Feb)", 0.5, 2.0, 1.5, 0.1)
        summer_mult = st.slider("Summer (Jun-Aug)", 0.5, 1.5, 0.8, 0.1)
        hurricane_season_mult = st.slider("Hurricane Season (Jun-Nov)", 0.5, 1.0, 0.7, 0.1)
    
    with col3:
        st.write("**Day-of-Week Factors**")
        weekend_mult = st.slider("Weekend (Fri-Sun)", 0.8, 1.5, 1.2, 0.1)
        weekday_mult = st.slider("Weekday (Mon-Thu)", 0.8, 1.2, 0.9, 0.1)
    
    # Reset button
    if st.button("Reset to Defaults"):
        st.rerun()

def show_forecast_page():
    """Page 3: 2-Week Forecast with heatmap visualization."""
    st.header("2-Week Forecast")
    
    # Date picker for forecast start
    forecast_start = st.date_input(
        "Forecast Start Date",
        value=datetime.now().date(),
        help="Choose the starting date for the 14-day forecast"
    )
    
    # Generate forecast data
    forecast_data = st.session_state.traveler_calculator.get_all_airports_forecast(
        datetime.combine(forecast_start, datetime.min.time()), 14
    )
    
    # Create pivot table for heatmap
    heatmap_data = forecast_data.pivot_table(
        index='airport_code',
        columns='date',
        values='expected_travelers',
        fill_value=0
    )
    
    # Heatmap visualization
    st.subheader("Traveler Volume Heatmap")
    fig = px.imshow(
        heatmap_data.values,
        labels=dict(x="Date", y="Airport", color="Travelers"),
        x=heatmap_data.columns.strftime('%m/%d'),
        y=heatmap_data.index,
        aspect="auto",
        color_continuous_scale="Blues"
    )
    fig.update_layout(
        title="Expected Travelers by Airport and Date",
        xaxis_title="Date",
        yaxis_title="Airport Code"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Summary statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_travelers = forecast_data['expected_travelers'].sum()
        st.metric("Total Travelers (14 days)", f"{total_travelers:,}")
    
    with col2:
        avg_daily = forecast_data.groupby('date')['expected_travelers'].sum().mean()
        st.metric("Average Daily Travelers", f"{avg_daily:,.0f}")
    
    with col3:
        peak_day = forecast_data.groupby('date')['expected_travelers'].sum().max()
        st.metric("Peak Day Travelers", f"{peak_day:,}")
    
    # Data table
    st.subheader("Detailed Forecast Data")
    
    # Add airport names to forecast data
    forecast_with_names = forecast_data.copy()
    forecast_with_names['airport_name'] = forecast_with_names['airport_code'].map(
        {code: info['name'] for code, info in MAJOR_AIRPORTS.items()}
    )
    
    # Display table
    display_columns = ['airport_code', 'airport_name', 'date', 'expected_travelers', 
                      'seasonal_factor', 'holiday_multiplier', 'dow_multiplier']
    st.dataframe(
        forecast_with_names[display_columns],
        use_container_width=True
    )
    
    # Export button
    csv = forecast_with_names.to_csv(index=False)
    st.download_button(
        label="Download Forecast Data (CSV)",
        data=csv,
        file_name=f"traveler_forecast_{forecast_start}.csv",
        mime="text/csv"
    )

def show_hurricane_modeling_page():
    """Page 4: Hurricane Risk Modeling with live/hypothetical toggle."""
    st.header("Hurricane Risk Modeling")
    
    # Initialize session state for hurricane data
    if 'hurricane_analyses' not in st.session_state:
        st.session_state.hurricane_analyses = {}
    if 'data_source' not in st.session_state:
        st.session_state.data_source = "Live Data"
    if 'selected_date' not in st.session_state:
        st.session_state.selected_date = datetime.now().date()
    
    # Data source toggle
    data_source = st.radio(
        "Data Source",
        ["Live Data", "Upload Hypothetical Scenario"],
        index=0 if st.session_state.data_source == "Live Data" else 1,
        help="Choose between live hurricane data or upload your own scenario"
    )
    
    # Update session state
    st.session_state.data_source = data_source
    
    if data_source == "Live Data":
        # Date picker for live data
        selected_date = st.date_input(
            "Select Date for Live Data",
            value=st.session_state.selected_date,
            help="Choose the date to fetch live hurricane data"
        )
        
        # Update session state
        st.session_state.selected_date = selected_date
        
        # Check if we need to reload data
        data_key = f"live_{selected_date.strftime('%Y-%m-%d')}"
        if data_key not in st.session_state:
            st.session_state[data_key] = None
        
        if st.button("Load Live Hurricane Data"):
            with st.spinner("Loading live hurricane data..."):
                try:
                    hurricane_analyses = st.session_state.hurricane_loader.load_hurricane_data(
                        source='live', date=selected_date.strftime('%Y-%m-%d')
                    )
                    st.session_state.hurricane_analyses = hurricane_analyses
                    st.session_state[data_key] = hurricane_analyses
                    st.success(f"Loaded {len(hurricane_analyses)} hurricanes")
                except Exception as e:
                    st.error(f"Failed to load live data: {e}")
        
        # Use cached data if available
        if st.session_state[data_key] is not None:
            st.session_state.hurricane_analyses = st.session_state[data_key]
            st.info(f"Using cached data for {selected_date.strftime('%Y-%m-%d')} ({len(st.session_state.hurricane_analyses)} hurricanes)")
    
    else:  # Hypothetical scenario
        st.subheader("Upload Hurricane Scenario")
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Upload CSV file with hurricane track data",
            type=['csv'],
            help="CSV should contain columns: track_id, valid_time, lat, lon, maximum_sustained_wind_speed_knots"
        )
        
        if uploaded_file is not None:
            try:
                # Validate and load data
                df = pd.read_csv(uploaded_file)
                is_valid, errors = st.session_state.hurricane_loader.validate_hypothetical_data(df)
                
                if is_valid:
                    hurricane_analyses = st.session_state.hurricane_loader.load_hurricane_data(
                        source='hypothetical', uploaded_file=uploaded_file
                    )
                    st.session_state.hurricane_analyses = hurricane_analyses
                    st.success(f"Loaded {len(hurricane_analyses)} hurricanes from uploaded data")
                else:
                    st.error("Data validation failed:")
                    for error in errors:
                        st.error(f"• {error}")
            
            except Exception as e:
                st.error(f"Failed to process uploaded file: {e}")
        
        # Template download
        st.write("**Need a template?**")
        template_csv = st.session_state.hurricane_loader.export_hypothetical_template()
        st.download_button(
            label="Download CSV Template",
            data=template_csv,
            file_name="hurricane_template.csv",
            mime="text/csv"
        )
    
    # Display hurricane tracks and risk analysis
    if st.session_state.hurricane_analyses:
        # Date range for analysis
        st.subheader("Risk Analysis Parameters")
        col1, col2 = st.columns(2)
        
        with col1:
            analysis_start = st.date_input(
                "Analysis Start Date",
                value=datetime.now().date()
            )
        
        with col2:
            analysis_days = st.slider(
                "Analysis Period (days)",
                min_value=1,
                max_value=30,
                value=14
            )
        
        # Calculate risk exposure
        if st.button("Calculate Risk Exposure"):
            with st.spinner("Calculating risk exposure..."):
                date_range = [
                    datetime.combine(analysis_start, datetime.min.time()) + timedelta(days=i)
                    for i in range(analysis_days)
                ]
                
                risk_exposure = st.session_state.risk_engine.calculate_risk_exposure(
                    st.session_state.hurricane_analyses, date_range
                )
                
                # Store results in session state
                st.session_state.risk_exposure = risk_exposure
                st.session_state.analysis_start = analysis_start
                st.session_state.analysis_days = analysis_days
                
                # Display results
                display_hurricane_risk_results(st.session_state.hurricane_analyses, risk_exposure)
    
    # Display cached results if available
    if 'risk_exposure' in st.session_state and st.session_state.risk_exposure:
        st.subheader("Previous Analysis Results")
        st.info(f"Showing results for {st.session_state.analysis_start} over {st.session_state.analysis_days} days")
        
        # Option to recalculate
        if st.button("Recalculate with New Parameters"):
            st.session_state.risk_exposure = None
            st.rerun()
        
        display_hurricane_risk_results(st.session_state.hurricane_analyses, st.session_state.risk_exposure)

def display_hurricane_risk_results(hurricane_analyses, risk_exposure):
    """Display hurricane risk analysis results."""
    st.subheader("Hurricane Track Map")
    
    # Create map with hurricane tracks
    risk_map = create_hurricane_track_map(hurricane_analyses, risk_exposure)
    st_folium(risk_map, width=700, height=500)
    
    # Risk timeline
    st.subheader("Risk Timeline")
    
    # Aggregate risk by date
    timeline_data = []
    for date, daily_risk in risk_exposure.items():
        timeline_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'total_travelers_at_risk': daily_risk['total_travelers_at_risk'],
            'airports_at_risk': len(daily_risk['airports_at_risk'])
        })
    
    timeline_df = pd.DataFrame(timeline_data)
    
    # Timeline chart
    fig = px.line(
        timeline_df,
        x='date',
        y='total_travelers_at_risk',
        title="Travelers at Risk Over Time"
    )
    fig.update_layout(xaxis_title="Date", yaxis_title="Travelers at Risk")
    st.plotly_chart(fig, use_container_width=True)
    
    # Airport breakdown
    st.subheader("Airport Risk Breakdown")
    
    # Get top risk airports
    top_airports = st.session_state.risk_engine.get_top_risk_airports(risk_exposure, top_n=10)
    
    if top_airports:
        airports_df = pd.DataFrame(top_airports)
        st.dataframe(airports_df, use_container_width=True)
    
    # Cumulative risk summary
    st.subheader("Cumulative Risk Summary")
    
    cumulative_risk = st.session_state.risk_engine.calculate_cumulative_risk(risk_exposure)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Travelers at Risk", f"{cumulative_risk['total_travelers_at_risk']:,}")
    
    with col2:
        st.metric("Unique Airports Affected", cumulative_risk['total_airports_affected'])
    
    with col3:
        st.metric("Total Risk Days", cumulative_risk['risk_summary']['total_risk_days'])
    
    with col4:
        peak_date = cumulative_risk['risk_summary']['highest_risk_day']
        st.metric("Peak Risk Day", peak_date.strftime('%Y-%m-%d'))

def load_hurricane_data_for_date(date):
    """Load hurricane data for a specific date."""
    try:
        return st.session_state.hurricane_loader.load_hurricane_data(
            source='live', date=date.strftime('%Y-%m-%d')
        )
    except Exception as e:
        st.error(f"Failed to load hurricane data: {e}")
        return {}

def calculate_current_risk(date, hurricane_analyses):
    """Calculate current risk exposure for a specific date."""
    if not hurricane_analyses:
        return {
            'total_travelers_at_risk': 0,
            'airports_at_risk': [],
            'regional_breakdown': {}
        }
    
    # Calculate risk for single date
    date_range = [datetime.combine(date, datetime.min.time())]
    risk_exposure = st.session_state.risk_engine.calculate_risk_exposure(
        hurricane_analyses, date_range
    )
    
    return risk_exposure[date_range[0]]

def create_risk_map(risk_exposure, hurricane_analyses):
    """Create map showing airport risk and hurricane tracks."""
    # Initialize map
    m = folium.Map(
        location=MAP_CENTER,
        zoom_start=5,
        tiles='OpenStreetMap'
    )
    
    # Add airports
    for airport_code, airport_info in MAJOR_AIRPORTS.items():
        is_at_risk = airport_code in risk_exposure['airports_at_risk']
        
        color = 'red' if is_at_risk else 'blue'
        travelers = st.session_state.traveler_calculator.calculate_daily_travelers(
            airport_code, datetime.combine(risk_exposure['date'], datetime.min.time())
        )
        
        folium.CircleMarker(
            location=[airport_info['lat'], airport_info['lon']],
            radius=8,
            popup=f"{airport_code}: {airport_info['name']}<br>Travelers: {travelers:,}",
            color=color,
            fill=True,
            fillOpacity=0.7
        ).add_to(m)
        
        # Add 100-mile radius circle
        folium.Circle(
            location=[airport_info['lat'], airport_info['lon']],
            radius=160900,  # 100 miles in meters
            color='gray',
            fill=False,
            opacity=0.3
        ).add_to(m)
    
    # Add hurricane tracks
    for track_id, analysis in hurricane_analyses.items():
        trajectory = analysis.get('trajectory', {})
        if trajectory and 'coordinates' in trajectory:
            coordinates = [(coord[0], coord[1]) for coord in trajectory['coordinates']]
            folium.PolyLine(
                coordinates,
                color='red',
                weight=3,
                opacity=0.8,
                popup=f"Hurricane {track_id}"
            ).add_to(m)
    
    return m

def create_hurricane_track_map(hurricane_analyses, risk_exposure):
    """Create map showing hurricane tracks and risk zones."""
    # Initialize map
    m = folium.Map(
        location=MAP_CENTER,
        zoom_start=5,
        tiles='OpenStreetMap'
    )
    
    # Add airports with risk status
    for airport_code, airport_info in MAJOR_AIRPORTS.items():
        # Check if airport is at risk on any day
        is_at_risk = any(
            airport_code in daily_risk['airports_at_risk']
            for daily_risk in risk_exposure.values()
        )
        
        color = 'red' if is_at_risk else 'blue'
        
        folium.CircleMarker(
            location=[airport_info['lat'], airport_info['lon']],
            radius=8,
            popup=f"{airport_code}: {airport_info['name']}",
            color=color,
            fill=True,
            fillOpacity=0.7
        ).add_to(m)
    
    # Add hurricane tracks
    for track_id, analysis in hurricane_analyses.items():
        trajectory = analysis.get('trajectory', {})
        if trajectory and 'coordinates' in trajectory:
            coordinates = [(coord[0], coord[1]) for coord in trajectory['coordinates']]
            folium.PolyLine(
                coordinates,
                color='red',
                weight=4,
                opacity=0.8,
                popup=f"Hurricane {track_id}"
            ).add_to(m)
    
    return m

def create_airports_dataframe(date):
    """Create dataframe with all airports and their data."""
    data = []
    
    for airport_code, airport_info in MAJOR_AIRPORTS.items():
        travelers = st.session_state.traveler_calculator.calculate_daily_travelers(
            airport_code, datetime.combine(date, datetime.min.time())
        )
        
        region = st.session_state.traveler_calculator._determine_region(
            airport_info['lat'], airport_info['lon']
        )
        
        data.append({
            'Airport Code': airport_code,
            'Name': airport_info['name'],
            'Latitude': airport_info['lat'],
            'Longitude': airport_info['lon'],
            'Region': region,
            'Expected Travelers': travelers,
            'Seasonal Factor': st.session_state.traveler_calculator.get_seasonality_factor(
                datetime.combine(date, datetime.min.time()), airport_code
            ),
            'Holiday Multiplier': st.session_state.traveler_calculator.get_holiday_multiplier(
                datetime.combine(date, datetime.min.time())
            )
        })
    
    return pd.DataFrame(data)

if __name__ == "__main__":
    main()
