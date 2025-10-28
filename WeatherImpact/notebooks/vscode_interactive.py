# %% [markdown]
# # VS Code Interactive Demo for WeatherImpact
# 
# This file uses VS Code's native interactive features with `# %%` cell markers.
# 
# **How to use:**
# 1. Click "Run Cell" above each cell
# 2. Or press `Ctrl+Shift+Enter` to run the current cell
# 3. Results appear in the interactive window below

# %%
# Import everything we need
from WeatherImpact import (
    HurricaneImpactPipeline,
    HurricaneDataFetcher,
    HurricaneAnalyzer,
    AirportImpact,
    InsuranceCalculator,
    HurricaneVisualizer
)

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

print("✅ All imports successful!")

# %%
# Initialize the pipeline
pipeline = HurricaneImpactPipeline(outputs_dir='../outputs', data_dir='../data')
print("✅ Pipeline initialized successfully!")
print(f"Pipeline type: {type(pipeline).__name__}")

# %%
# Test data download
start_date = '2024-10-23'
print(f"📅 Testing with date: {start_date}")

hurricane_data = pipeline.fetcher.download_hurricane_data(start_date, force_download=True)

if hurricane_data is not None:
    print(f"✅ Downloaded {len(hurricane_data)} hurricane records")
    print(f"📊 Data columns: {list(hurricane_data.columns)}")
    print("\nFirst few rows:")
    print(hurricane_data.head())
else:
    print("❌ No hurricane data found")

# %%
# Test hurricane analysis
if 'hurricane_data' in locals() and hurricane_data is not None:
    hurricane_analysis = pipeline.analyzer.analyze_hurricane(hurricane_data)
    print("✅ Hurricane analysis complete!")
    print(f"📈 Analysis keys: {list(hurricane_analysis.keys())}")
    
    if 'track_data' in hurricane_analysis:
        track_data = hurricane_analysis['track_data']
        print(f"\n📍 Track data shape: {track_data.shape}")
else:
    print("❌ No data to analyze")

# %%
# Test individual components
print("🧪 Testing individual components:")

components = [
    ("DataFetcher", HurricaneDataFetcher),
    ("Analyzer", HurricaneAnalyzer),
    ("AirportImpact", AirportImpact),
    ("InsuranceCalculator", InsuranceCalculator),
    ("Visualizer", HurricaneVisualizer)
]

for name, component_class in components:
    try:
        component = component_class()
        print(f"✅ {name}: {type(component).__name__}")
    except Exception as e:
        print(f"❌ {name}: Error - {e}")

# %%
# Interactive exploration
if 'hurricane_data' in locals() and hurricane_data is not None:
    print("🔍 Interactive exploration available!")
    print(f"Variables available:")
    print(f"- pipeline: {type(pipeline).__name__}")
    print(f"- hurricane_data: DataFrame with {len(hurricane_data)} rows")
    print(f"- hurricane_analysis: {list(hurricane_analysis.keys()) if 'hurricane_analysis' in locals() else 'Not available'}")
    
    print("\n💡 You can now explore these variables in the interactive window!")
else:
    print("❌ No data available for exploration")

# %%
# Quick visualization test
if 'hurricane_data' in locals() and hurricane_data is not None:
    plt.figure(figsize=(10, 6))
    
    # Plot wind speed over time if available
    if 'wind_speed' in hurricane_data.columns:
        plt.plot(hurricane_data['wind_speed'])
        plt.title('Wind Speed Over Time')
        plt.xlabel('Time Index')
        plt.ylabel('Wind Speed (knots)')
        plt.show()
        print("📊 Wind speed plot generated!")
    else:
        print("📊 No wind speed data available for plotting")
else:
    print("❌ No data available for visualization")
