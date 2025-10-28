<!-- 72dbc22d-744b-4181-800f-75729ac8c51e 1260f85e-fc01-412a-ace2-6bf286e061d2 -->
# Hurricane Impact Analysis System for Air Travel Insurance

## Overview

Create a system that fetches hurricane track data from Google DeepMind WeatherLab, identifies affected airports, estimates traveler exposure, and produces both visualizations and programmatic outputs for a dummy insurance company covering air travel delays.

## Project Structure

```
/Users/sf/Applications/ai-cookbook/
└── hurricane-impact-analysis/
    ├── README.md
    ├── requirements.txt
    ├── config.py                    # Configuration (API URLs, date ranges, airport data)
    ├── data_fetcher.py              # Download hurricane data from WeatherLab
    ├── hurricane_analyzer.py        # Parse tracks, predict paths, calculate exposure zones
    ├── airport_impact.py            # Identify affected airports and estimate travelers
    ├── insurance_calculator.py      # Calculate exposure and potential claims
    ├── visualizer.py                # Create maps and dashboards
    ├── pipeline.py                  # Main orchestration script
    ├── schedule_daily.py            # CRON-compatible daily runner
    ├── data/                        # Downloaded hurricane CSV files
    ├── outputs/                     # Generated reports and visualizations
    └── notebooks/                   # Jupyter notebooks for exploration
        └── hurricane_analysis_demo.ipynb
```

## Implementation Steps

### 1. Data Acquisition Module (`data_fetcher.py`)

- Construct scriptable URLs using pattern: `https://deepmind.google.com/science/weatherlab/download/cyclones/FNV3/ensemble_mean/paired/csv/FNV3_{YYYY_MM_DD}T00_00_paired.csv`
- Download CSV files for specified date ranges (start with recent dates like 2024-09-01 to 2025-10-15)
- Parse CSV columns: `init_time`, `track_id`, `valid_time`, `lat`, `lon`, `minimum_sea_level_pressure_hpa`, `maximum_sustained_wind_speed_knots`, radius fields
- Handle terms of use for data <48 hours old vs CC BY 4.0 for older data
- Cache downloaded files in `data/` directory with timestamps

### 2. Hurricane Analysis Module (`hurricane_analyzer.py`)

- Load and parse hurricane track data from WeatherLab CSVs
- Extract hurricane trajectories (lat/lon over time) for each `track_id`
- Calculate hurricane intensity zones based on wind radii (34kt, 50kt, 64kt circles)
- Project future positions using existing forecast data from WeatherLab ensemble means
- Create spatial impact zones (circles/ellipses) around predicted hurricane paths with time-based uncertainty

### 3. Airport Impact Module (`airport_impact.py`)

- Integrate airport database (use public dataset like OurAirports or FAA data)
- Focus on major Atlantic region airports (US East Coast, Caribbean, Central America)
- Calculate distance from each airport to hurricane track points
- Determine if airport falls within impact zones (34kt+ wind radius = flight disruptions likely)
- Estimate affected timeframes (when hurricane is within X km of airport)
- Pull daily passenger volume data (use proxy data like 2023 FAA stats: ATL ~100k/day, MIA ~50k/day, etc.)
- Calculate total travelers impacted per airport per day

### 4. Insurance Impact Calculator (`insurance_calculator.py`)

- Define dummy insurance company parameters:
  - Policy coverage: flight delay >3 hours due to weather
  - Payout per claim: $500 average
  - Penetration rate: 2% of travelers have this coverage
  - Claim rate: 60% of covered travelers in impact zone will file
- For each affected airport/date:
  - Daily travelers → Coverage holders → Expected claims → Total exposure
- Aggregate across all affected airports for total hurricane exposure
- Generate risk scores by hurricane intensity and proximity

### 5. Visualization Module (`visualizer.py`)

- **Interactive Map Dashboard:**
  - Plot hurricane tracks (past and predicted) using folium or plotly
  - Show airports as markers (colored by exposure level)
  - Display impact zones (wind radii circles) animated over time
  - Add tooltips with airport details and traveler counts
- **Exposure Summary Dashboard:**
  - Time-series chart: Expected claims over time
  - Bar chart: Top 10 affected airports by exposure
  - KPI cards: Total travelers impacted, total exposure ($), affected airports count
- Export as standalone HTML file for easy sharing

### 6. Pipeline Orchestration (`pipeline.py`)

- Command-line interface to run full analysis:
  - `python pipeline.py --start-date 2024-09-01 --end-date 2024-09-30`
- Steps:

  1. Fetch hurricane data for date range
  2. Analyze tracks and create impact zones
  3. Calculate airport impacts
  4. Compute insurance exposure
  5. Generate visualizations and reports
  6. Save outputs to `outputs/{date}/`

### 7. Daily Automation (`schedule_daily.py`)

- Script designed for CRON execution: `0 6 * * * cd /path/to/hurricane-impact-analysis && python schedule_daily.py`
- Fetch yesterday's data (using date offset)
- Run full pipeline
- Send summary report (optional: email or Slack notification)
- Archive old data/reports to prevent disk bloat

### 8. Documentation and Demo

- **README.md**: Setup instructions, usage examples, data sources
- **Jupyter Notebook**: Interactive demo showing:
  - Sample hurricane track visualization
  - Airport impact calculation walkthrough
  - Insurance exposure modeling example
  - Use recent Hurricane Milton (Oct 2024) or Hurricane Lee (Sep 2023) as case study

## Key Data Sources

1. **Hurricane Data**: Google DeepMind WeatherLab - https://deepmind.google.com/science/weatherlab (scriptable CSV URLs)
2. **Airport Data**: OurAirports database (https://ourairports.com/data/) - free CSV with global airports, coordinates
3. **Passenger Volume**: FAA or ACI traffic statistics (use 2023 annual data as daily proxy)

## Technology Stack

- **Python 3.9+**
- **Data Processing**: pandas, numpy
- **Geospatial**: geopy (distance calculations), shapely (geometric operations)
- **Visualization**: folium (maps), plotly/dash (interactive dashboards), matplotlib/seaborn (charts)
- **HTTP**: requests (fetch data)
- **Scheduling**: built-in argparse for CLI, compatible with system CRON

## Deliverables

1. ✅ **Programmatic API**: Modular Python functions to get exposure by date/hurricane
2. ✅ **Interactive Dashboard**: HTML file with map + charts showing hurricane tracks, affected airports, and financial exposure
3. ✅ **Daily Pipeline**: CRON-ready script for automated daily updates
4. ✅ **Demo Notebook**: Jupyter notebook demonstrating full workflow with real hurricane examples

## Example Output Scenario

**Hurricane:** AL972025 (from provided data)

**Date Range:** Oct 13-15, 2025

**Affected Airports:** Bermuda (BDA), potentially Azores

**Estimated Impact:**

- 2 airports within 200km of track
- ~3,000 daily travelers (smaller regional airports)
- 60 coverage holders × 60% claim rate × $500 = **~$18,000 exposure**

For major hurricanes hitting Florida coast (e.g., Hurricane Milton), exposure could reach **$5-10M** (hundreds of thousands of travelers, dozens of airports).

### To-dos

- [ ] Create project structure, requirements.txt, and README in ai-cookbook
- [ ] Build config.py with WeatherLab URL templates, date ranges, and airport parameters
- [ ] Implement data_fetcher.py to download and parse WeatherLab hurricane CSV files
- [ ] Build hurricane_analyzer.py to parse tracks, extract coordinates, and create impact zones
- [ ] Integrate OurAirports data and create airport_impact.py to identify affected airports and estimate travelers
- [ ] Create insurance_calculator.py with dummy insurance parameters and exposure calculation logic
- [ ] Build visualizer.py with interactive map and dashboard using folium/plotly
- [ ] Create pipeline.py to orchestrate full workflow with CLI interface
- [ ] Implement schedule_daily.py for CRON-compatible daily execution
- [ ] Create Jupyter notebook demonstrating analysis with real hurricane case study