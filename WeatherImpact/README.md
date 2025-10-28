# Hurricane Risk API

FastAPI service that calculates traveler risk exposure from hurricane impacts using data from the weather-lab-data-api.

## Features

- Calculate traveler risk profiles for airports based on hurricane proximity
- Support for single date and date range analysis
- Returns JSON responses suitable for n8n pipeline integration
- Deployed on Railway

## API Endpoints

### Health Check
```
GET /api/v1/health
```

### Analyze Risk (Single Date)
```
POST /api/v1/analyze
{
  "date": "2024-10-23",
  "days": 1
}
```

### Analyze Risk Range (Forecast)
```
POST /api/v1/analyze-range
{
  "start_date": "2024-10-23",
  "days": 14
}
```

## Response Format

```json
{
  "meta": {
    "start_date": "2024-10-23",
    "end_date": "2024-11-05",
    "total_days": 14,
    "analysis_timestamp": "2024-10-23T12:00:00Z"
  },
  "daily_risk": [
    {
      "date": "2024-10-23",
      "total_travelers_at_risk": 45000,
      "airports_affected": 3,
      "active_hurricanes": 1,
      "airports_at_risk": [
        {
          "airport_code": "MIA",
          "airport_name": "Miami International",
          "travelers_at_risk": 25000,
          "distance_to_hurricane_km": 85.3,
          "risk_level": "high"
        }
      ]
    }
  ]
}
```

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the server:
```bash
uvicorn main:app --reload
```

3. Access API docs:
```
http://localhost:8000/docs
```

## Environment Variables

- `WEATHER_LAB_API_URL`: URL of the weather-lab-data-api (default: production URL)
- `RISK_RADIUS_KM`: Risk radius in kilometers (default: 160.9)
- `LOG_LEVEL`: Logging level (default: INFO)

## Deployment

The API is deployed on Railway using Dockerfile.
