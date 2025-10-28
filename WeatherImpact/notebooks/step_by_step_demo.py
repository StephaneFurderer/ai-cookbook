# Import everything we need
# Now we can import cleanly
from WeatherImpact import (
    HurricaneDataFetcher,
    HurricaneAnalyzer,
    AirportImpact,
    InsuranceCalculator,
    HurricaneVisualizer,
    HurricaneImpactPipeline
)

# Also import common libraries
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings

# Set up plotting
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")
warnings.filterwarnings('ignore')

#--------------------------------
# Initialize the pipeline
#--------------------------------
from WeatherImpact.config import get_weatherlab_url
url = get_weatherlab_url('2024-10-23')
print(url)


pipeline = HurricaneImpactPipeline(outputs_dir='../outputs', data_dir='../data')



start_date = '2024-10-23'


hurricane_data = pipeline._download_data(start_date,force_download=True)
print(hurricane_data.items())

hurricane_analysis = pipeline.analyzer.analyze_hurricane(hurricane_data)
#print(hurricane_analysis.items())
#results = pipeline.run_analysis(start_date)

# Display results
#print(results)