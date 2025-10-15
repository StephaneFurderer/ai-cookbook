# Hurricane Impact Analysis for Air Travel Insurance

This system analyzes hurricane tracks from Google DeepMind WeatherLab to assess potential impacts on air travel and calculate insurance exposure for flight delay coverage.

## Features

- **Hurricane Data Integration**: Downloads and parses hurricane track data from Google DeepMind WeatherLab
- **Airport Impact Assessment**: Identifies airports within hurricane impact zones and estimates traveler exposure
- **Insurance Risk Modeling**: Calculates potential claims exposure for flight delay insurance
- **Interactive Visualizations**: Creates maps and dashboards showing hurricane tracks and affected areas
- **Automated Pipeline**: Daily updates via CRON scheduling

## Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Analysis on Hurricane Helene (2024)**:
   ```bash
   python pipeline.py --start-date 2024-09-23 --end-date 2024-09-27
   ```

3. **View Results**:
   - Interactive map: `outputs/2024-09-23/helene_2024_interactive_map.html`
   - Summary dashboard: `outputs/2024-09-23/helene_2024_dashboard.html`

## Data Sources

- **Hurricane Tracks**: [Google DeepMind WeatherLab](https://deepmind.google.com/science/weatherlab)
- **Airport Data**: [OurAirports Database](https://ourairports.com/data/)
- **Passenger Volume**: FAA 2023 traffic statistics

## Case Study: Hurricane Helene (2024-09-23)

Hurricane Helene developed in the Atlantic on September 23, 2024, and provides an excellent example of:
- Hurricane track prediction and uncertainty modeling
- Airport impact assessment for Atlantic region
- Insurance exposure calculation for flight delays

## Project Structure

```
WeatherImpact/
├── config.py              # Configuration settings
├── data_fetcher.py        # Download hurricane data
├── hurricane_analyzer.py  # Parse tracks and create impact zones
├── airport_impact.py      # Identify affected airports
├── insurance_calculator.py # Calculate exposure and claims
├── visualizer.py          # Create interactive maps and dashboards
├── pipeline.py            # Main orchestration script
├── schedule_daily.py      # CRON-compatible daily runner
├── data/                  # Downloaded hurricane CSV files
├── outputs/               # Generated reports and visualizations
└── notebooks/             # Jupyter notebooks for exploration
    └── helene_2024_analysis.ipynb
```

## Usage Examples

### Command Line Interface

```bash
# Analyze specific date range
python pipeline.py --start-date 2024-09-23 --end-date 2024-09-27

# Run daily automated analysis
python schedule_daily.py

# Analyze specific hurricane
python pipeline.py --hurricane-id AL972024
```

### Programmatic API

```python
from hurricane_analyzer import HurricaneAnalyzer
from airport_impact import AirportImpact
from insurance_calculator import InsuranceCalculator

# Load hurricane data
analyzer = HurricaneAnalyzer()
hurricane_data = analyzer.load_hurricane_data("2024-09-23")

# Calculate airport impacts
airport_impact = AirportImpact()
affected_airports = airport_impact.find_affected_airports(hurricane_data)

# Calculate insurance exposure
calculator = InsuranceCalculator()
exposure = calculator.calculate_exposure(affected_airports)
print(f"Total exposure: ${exposure['total_exposure']:,.2f}")
```

## Insurance Parameters

The dummy insurance company covers:
- **Policy**: Flight delays >3 hours due to weather
- **Payout**: $500 average per claim
- **Penetration**: 2% of travelers have coverage
- **Claim Rate**: 60% of covered travelers in impact zone file claims

## Output Files

- **Interactive Map**: HTML file with hurricane track, airports, and impact zones
- **Dashboard**: Summary charts and KPIs
- **CSV Reports**: Detailed exposure data by airport and date
- **JSON Data**: Structured data for further analysis

## License

This project uses data from Google DeepMind WeatherLab, which is licensed under:
- Creative Commons Attribution International License, Version 4.0 (CC BY 4.0) for historical data
- Terms of Use for data less than 48 hours old (see: https://storage.googleapis.com/weathernext-public/terms-of-use.pdf)
