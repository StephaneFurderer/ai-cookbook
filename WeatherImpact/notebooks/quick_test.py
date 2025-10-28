#!/usr/bin/env python3
"""
Quick interactive test script for WeatherImpact.

Run this in VS Code interactive window or Python REPL.
"""

# Import everything we need
from import_helper import *

print("🌪️  WeatherImpact Interactive Session")
print("=" * 50)

# Initialize pipeline
pipeline = HurricaneImpactPipeline(outputs_dir='../outputs', data_dir='../data')
print("✅ Pipeline ready!")

# Quick test
start_date = '2024-10-23'
print(f"📅 Testing with date: {start_date}")

# Download some data
print("📥 Downloading data...")
hurricane_data = pipeline.fetcher.download_hurricane_data(start_date, force_download=True)

if hurricane_data is not None:
    print(f"✅ Got {len(hurricane_data)} records")
    print(f"📊 Columns: {list(hurricane_data.columns)}")
else:
    print("❌ No data found")

print("\n🎯 Interactive session ready!")
print("You can now use:")
print("- pipeline: HurricaneImpactPipeline instance")
print("- hurricane_data: Downloaded data (if available)")
print("- All WeatherImpact components are imported")

# Example interactive commands:
print("\n💡 Try these commands:")
print("pipeline.fetcher.download_hurricane_data('2024-09-23')")
print("pipeline.analyzer.analyze_hurricane(hurricane_data)")
print("pipeline.run_analysis('2024-09-23', '2024-09-27')")
