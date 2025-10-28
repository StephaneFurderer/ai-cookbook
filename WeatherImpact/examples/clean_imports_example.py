#!/usr/bin/env python3
"""
Example showing clean imports for WeatherImpact.

This demonstrates the proper way to import and use WeatherImpact modules.
"""

# Method 1: Import the package and use it
from WeatherImpact import HurricaneImpactPipeline

def main():
    """Example using clean imports."""
    print("=" * 60)
    print("WEATHERIMPACT - CLEAN IMPORTS EXAMPLE")
    print("=" * 60)
    
    # Initialize the pipeline
    pipeline = HurricaneImpactPipeline()
    print("✅ Pipeline initialized successfully")
    
    # You can also import individual components
    from WeatherImpact import HurricaneDataFetcher, HurricaneAnalyzer
    
    # Initialize individual components
    fetcher = HurricaneDataFetcher()
    analyzer = HurricaneAnalyzer()
    
    print("✅ Individual components imported successfully")
    print("\nAvailable components:")
    print("- HurricaneDataFetcher")
    print("- HurricaneAnalyzer")
    print("- AirportImpact")
    print("- InsuranceCalculator")
    print("- HurricaneVisualizer")
    print("- HurricaneImpactPipeline")
    
    print("\n" + "=" * 60)
    print("CLEAN IMPORTS WORKING!")
    print("=" * 60)

if __name__ == "__main__":
    main()
