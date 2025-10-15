# Import required libraries
import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Add parent directory to path to import our modules
sys.path.append('..')

# Import our hurricane analysis modules
from data_fetcher import HurricaneDataFetcher
from hurricane_analyzer import HurricaneAnalyzer
from airport_impact import AirportImpact
from insurance_calculator import InsuranceCalculator
from visualizer import HurricaneVisualizer
from pipeline import HurricaneImpactPipeline
# Set up plotting style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

print("✅ All imports successful!")

#--------------------------------
# Initialize the pipeline
#--------------------------------
pipeline = HurricaneImpactPipeline()



start_date = '2024-09-23'


hurricane_data = pipeline.fetcher.download_hurricane_data(start_date,force_download=True)

#results = pipeline.run_analysis(start_date)

# Display results
#print(results)