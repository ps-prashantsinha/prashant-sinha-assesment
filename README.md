# Crop Production & Yield Dashboard

An interactive dashboard for analyzing Indian agriculture crop production data using Streamlit and Plotly. The application provides insights into crop yields, production trends, and identifies critical yield decline patterns across states and districts.

## Overview

This dashboard analyzes agricultural data from India to provide insights into crop production trends, yield efficiency, and critical yield decline detection. The key success metric is the automatic detection of states with more than 10% yield decline over 5-year periods, classified by severity (Moderate/High/Critical).

## How It Works

The application is built with Streamlit and uses Plotly for interactive visualizations. It processes a 30MB+ CSV dataset containing 345,000+ records of Indian agriculture data.

### Data Processing Pipeline

**Data Loading and Preprocessing**

The `load_data()` function handles the initial data processing:

1. Loads the CSV file and strips whitespace from column names
2. Parses the Year column from "YYYY-MM" format to integer (e.g., "2020-21" becomes 2020)
3. Calculates Yield as Production divided by Area
4. Handles division by zero by replacing infinity values with NaN
5. Cleans text fields (State, District, Crop, Season) by stripping whitespace
6. Removes rows where Crop is null
7. Returns a cleaned DataFrame

The function uses Streamlit's `@st.cache_data` decorator so data is loaded only once per session.

**Yield Decline Detection Algorithm**

The `calculate_yield_decline()` function identifies problematic yield trends:

For each combination of Crop and State:
- Filters data for the specified time period (default 5 years)
- Calculates average yield for the early period (first 2 years)
- Calculates average yield for the recent period (last 2 years)
- Computes decline percentage: ((early_yield - recent_yield) / early_yield) * 100
- If decline exceeds 10%, classifies severity:
  - Critical: decline > 30%
  - High: decline between 20-30%
  - Moderate: decline between 10-20%
- Returns a sorted DataFrame with Crop, State, Decline_Percentage, Early_Yield, Recent_Yield, and Severity

**Correlation Analysis**

The `prepare_correlation_data()` function computes Pearson correlation coefficients between Area, Production, and Yield, returning a 3x3 correlation matrix used for the heatmap visualization.

**Time Series Aggregation**

The `prepare_time_series()` function groups data by a specified dimension (typically Year) and aggregates:
- Area: Sum of total cultivated area
- Production: Sum of total production
- Yield: Mean average efficiency

### Application Architecture

The code is organized into four layers:

**Data Layer** - Functions that load and cache data:
- `load_data()`: CSV parsing and preprocessing
- `load_geojson()`: GeoJSON loading for map visualization

**Processing Layer** - Functions that transform data:
- `calculate_yield_decline()`: Identifies yield decline patterns
- `prepare_correlation_data()`: Correlation matrix computation
- `prepare_time_series()`: Time-based aggregations
- `get_state_average_yield()`: State-level metrics

**Visualization Layer** - Functions that create charts:
- `plot_correlation_matrix()`: Heatmap showing relationships
- `plot_time_series()`: Multi-line chart with dual y-axis
- `plot_top_districts()`: Horizontal bar chart
- `plot_yield_vs_area()`: Scatter plot with size encoding
- `plot_yield_area_scatter()`: Aggregated scatter plot
- `plot_cropwise_production()`: Multi-line crop comparison

**UI Layer** - The `main()` function that handles:
- Filter controls in the sidebar
- Layout management with tabs and columns
- User interactions and state management

## Features

### Filters

All filters in the sidebar support multi-select:

- State: Default is Gujarat, cascades to District filter
- District: Auto-filtered based on selected states
- Crop: Default is Rice, supports multiple crop comparison
- Season: Options include Kharif, Rabi, Summer
- Year Range: Multi-select from available years, default is last 6 years

The sidebar displays a summary showing filtered record count and date range.

### Dashboard Tab

**Correlation Matrix Heatmap**
Shows Pearson correlation between Area, Production, and Yield using a Red-Yellow-Green color scale. Hover to see exact values.

**Time Series Chart**
Multi-axis line chart with Area and Production on the primary y-axis and Yield on the secondary y-axis. Includes markers and unified hover mode.

**Top Districts Bar Chart**
Horizontal bar chart showing the top 10 producing districts with color gradient by production volume.

**Yield vs Area Scatter Plot**
Scatter plot where x-axis is Production Area, y-axis is Yield, size represents Production volume, and color represents Crop type. If dataset has more than 5000 rows, it randomly samples 5000 points for performance.

**Yield vs Area Aggregated**
Scatter plot aggregated by State and Crop, colored by State.

**Crop-wise Production Time Series**
Multi-line chart comparing production trends across different crops over time.

### Map View Tab

**Interactive Choropleth Map**
Uses the `india_state_geo.json` file to display a choropleth map where states are colored by average yield (Yellow-Green scale). Hover tooltips show Yield, Production, and Area. The map auto-fits to India's boundaries.

**District-Level Analysis**
After selecting a state from the dropdown:
- Top 10 Districts bar chart showing production
- Year-over-Year Trend with dual-axis (Production and Yield)
- Statistics table with aggregated metrics by district

### Critical Alerts System

The yield decline detection runs automatically on filtered data and displays:
- Total number of alerts
- Count of critical alerts (>30% decline)
- Average decline percentage
- Expandable table showing top 10 declines with full details

## Installation and Setup

Requirements:
- Python 3.11 or higher
- pip package manager
- 2GB+ RAM for processing the large dataset

**Step 1: Get the code**

Clone the repository or download and extract the ZIP file.

**Step 2: Create virtual environment (recommended)**

Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

macOS/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

**Step 3: Install dependencies**

```bash
pip install -r requirements.txt
```

The requirements.txt includes:
- streamlit (web framework)
- streamlit_autorefresh (auto-refresh functionality)
- plotly (interactive visualizations)
- pandas (data manipulation)
- numpy (numerical computations)

**Step 4: Verify data files**

Make sure these files are in the project directory:
- India Agriculture Crop Production.csv (30MB+)
- india_state_geo.json (85MB+)

## Running the Application

**Local deployment:**

Standard run:
```bash
streamlit run app.py
```

The dashboard will be available at http://localhost:8501

Custom port:
```bash
streamlit run app.py --server.port 8080
```

Headless mode for servers:
```bash
streamlit run app.py --server.headless true
```

**Streamlit Cloud deployment:**

1. Push code to GitHub
2. Go to share.streamlit.io
3. Connect your GitHub repository
4. Select branch (main) and main file (app.py)
5. Click Deploy

**Docker deployment:**

Create a Dockerfile:
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

Build and run:
```bash
docker build -t crop-dashboard .
docker run -p 8501:8501 crop-dashboard
```

## Performance Optimizations

**Data Caching**
The `@st.cache_data` decorator is used on `load_data()` and `load_geojson()`. Cache persists across user sessions and only invalidates when data files change.

**Sampling Strategy**
Scatter plots sample 5000 random points if the dataset exceeds 5000 rows to maintain performance while preserving statistical representativeness.

**Lazy Loading**
The GeoJSON file is loaded only when the Map View tab is accessed, with error handling for missing files.

## Data Quality Handling

**Missing Values:**
- Rows with null Crop values are dropped
- Empty Season values are filled with empty string
- Infinity values in Yield (from division by zero) are replaced with NaN

**Data Validation:**
- Year column is parsed with error handling
- Type conversions are applied (string to int for Year)
- All text fields have whitespace trimmed

## Dataset Information

Source: India Agriculture Crop Production Dataset
Size: 30MB+ with 345,000+ records

Columns:
- State: Indian state name
- District: District name
- Year: Year in "YYYY-MM" format (parsed to integer)
- Season: Growing season (Kharif, Rabi, Summer, etc.)
- Crop: Crop name
- Area: Cultivated area in hectares
- Production: Total production in tonnes

Derived column:
- Yield: Production / Area (tonnes per hectare)
