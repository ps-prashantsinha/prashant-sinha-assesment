# Crop Production & Yield Dashboard

A comprehensive interactive dashboard for analyzing Indian agriculture crop production data, built with Streamlit and Plotly. This application provides real-time insights into crop yields, production trends, and identifies critical yield decline patterns across states and districts.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Data Processing Logic](#data-processing-logic)
- [Features](#features)
- [Installation & Setup](#installation--setup)
- [Deployment](#deployment)
- [Usage Guide](#usage-guide)
- [Technical Details](#technical-details)
- [File Structure](#file-structure)

---

## 🎯 Overview

This dashboard analyzes agricultural data from India, providing insights into:
- **Crop production trends** across states and districts
- **Yield efficiency** analysis (Production per unit Area)
- **Critical yield decline detection** with automated alerts
- **Interactive geographical visualizations** using choropleth maps
- **Multi-dimensional filtering** for granular analysis

**Key Success Metric**: Automatically detects and highlights states with **>10% yield decline** over 5-year periods, classified by severity (Moderate/High/Critical).

---

## 🏗️ Architecture

### Application Stack

```
┌─────────────────────────────────────┐
│     Streamlit Web Interface         │
│  (Frontend + Backend Integration)   │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      Data Processing Layer          │
│  • Pandas DataFrames                │
│  • NumPy Calculations               │
│  • Caching (@st.cache_data)         │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│    Visualization Layer              │
│  • Plotly Express                   │
│  • Plotly Graph Objects             │
│  • Interactive Charts               │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│         Data Sources                │
│  • CSV (30MB+ dataset)              │
│  • GeoJSON (India state boundaries) │
└─────────────────────────────────────┘
```

### Component Architecture

The application follows a modular design pattern:

1. **Data Layer** (`load_data()`, `load_geojson()`)
   - CSV parsing and preprocessing
   - Data type conversions
   - Yield calculation
   - Caching for performance

2. **Processing Layer** (Data transformation functions)
   - `calculate_yield_decline()`: Identifies yield decline patterns
   - `prepare_correlation_data()`: Correlation matrix computation
   - `prepare_time_series()`: Time-based aggregations
   - `get_state_average_yield()`: State-level metrics

3. **Visualization Layer** (Plotting functions)
   - Interactive Plotly charts
   - Choropleth maps
   - Multi-axis time series
   - Scatter plots and bar charts

4. **UI Layer** (`main()`)
   - Streamlit components
   - Filter controls
   - Layout management
   - User interactions

---

## 🔄 Data Processing Logic

### 1. Data Loading & Preprocessing

**Function**: `load_data()`

```python
Process Flow:
1. Load CSV → Parse columns → Strip whitespace
2. Extract Year from "YYYY-MM" format → Convert to integer
3. Calculate Yield = Production / Area
4. Handle infinity values (division by zero)
5. Clean text fields (State, District, Crop, Season)
6. Remove null Crop entries
7. Return cleaned DataFrame
```

**Key Transformations**:
- **Year Parsing**: `"2020-21"` → `2020` (integer)
- **Yield Calculation**: `Yield = Production / Area`
- **Infinity Handling**: Replace `inf` and `-inf` with `NaN`
- **Text Cleaning**: Strip whitespace from all string columns

**Caching**: Uses `@st.cache_data` decorator for performance optimization (data loaded once per session).

### 2. Yield Decline Detection

**Function**: `calculate_yield_decline(df, years=5)`

**Algorithm**:
```
For each (Crop, State) combination:
  1. Filter data for last N years
  2. Calculate average yield for:
     - Early period: First 2 years
     - Recent period: Last 2 years
  3. Compute decline percentage:
     decline_pct = ((early_yield - recent_yield) / early_yield) * 100
  4. If decline_pct > 10%:
     - Classify severity:
       • Critical: > 30%
       • High: 20-30%
       • Moderate: 10-20%
     - Add to alert list
  5. Return sorted DataFrame by decline percentage
```

**Output Schema**:
- `Crop`: Crop name
- `State`: State name
- `Decline_Percentage`: Percentage decline
- `Early_Yield`: Average yield in early period
- `Recent_Yield`: Average yield in recent period
- `Severity`: Classification (Critical/High/Moderate)

### 3. Correlation Analysis

**Function**: `prepare_correlation_data(df)`

Computes Pearson correlation coefficients between:
- Area (hectares)
- Production (tonnes)
- Yield (tonnes/hectare)

Returns a 3x3 correlation matrix for heatmap visualization.

### 4. Time Series Aggregation

**Function**: `prepare_time_series(df, group_by='Year')`

**Aggregation Logic**:
- **Area**: Sum (total cultivated area)
- **Production**: Sum (total production)
- **Yield**: Mean (average efficiency)

Groups data by specified dimension (Year, State, Crop, etc.).

---

## 🎨 Features

### Interactive Filters (Sidebar)

All filters support **multi-select** for flexible analysis:

1. **State Filter**
   - Default: Gujarat (or random state)
   - Cascades to District filter

2. **District Filter**
   - Auto-filtered based on selected states
   - Default: All districts in selected states

3. **Crop Filter**
   - Default: Rice (or random crop)
   - Supports multiple crop comparison

4. **Season Filter**
   - Options: Kharif, Rabi, Summer, etc.
   - Default: Kharif (or random season)

5. **Year Range Selector**
   - Multi-select from available years
   - Default: Last 6 years

**Filter Summary**: Displays filtered record count and date range.

### Dashboard Tab

#### 1. Correlation Matrix Heatmap
- **Type**: Plotly Heatmap
- **Purpose**: Shows relationships between Area, Production, and Yield
- **Color Scale**: RdYlGn (Red-Yellow-Green)
- **Interactivity**: Hover to see exact correlation values

#### 2. Time Series Chart
- **Type**: Multi-axis line chart (dual y-axis)
- **Primary Axis**: Area and Production
- **Secondary Axis**: Yield
- **Features**: 
  - Line + markers for trend visibility
  - Unified hover mode
  - Color-coded lines

#### 3. Top Districts Bar Chart
- **Type**: Horizontal bar chart
- **Metric**: Total production
- **Features**:
  - Top 10 districts
  - Color gradient by production volume
  - Auto-sorted (ascending order)

#### 4. Yield vs Area Scatter Plot
- **Type**: Scatter plot with size encoding
- **X-axis**: Production Area
- **Y-axis**: Yield
- **Size**: Production volume
- **Color**: Crop type
- **Sampling**: Random 5000 points (if dataset > 5000 rows)

#### 5. Yield vs Area (Aggregated)
- **Type**: Scatter plot
- **Aggregation**: By State and Crop
- **Color**: State
- **Hover Data**: Crop, Area

#### 6. Crop-wise Production Time Series
- **Type**: Multi-line chart
- **Purpose**: Compare production trends across crops
- **Features**: Markers for data points, vertical legend

### Map View Tab

#### 1. Interactive Choropleth Map
- **Data Source**: `india_state_geo.json` (GeoJSON format)
- **Color Encoding**: Average Yield by state
- **Color Scale**: YlGn (Yellow-Green)
- **Features**:
  - Hover tooltips with Yield, Production, Area
  - Auto-fit bounds to India
  - Clickable states (for future drill-down)

#### 2. District-Level Analysis
- **State Selector**: Dropdown to choose state
- **Visualizations**:
  - **Top 10 Districts**: Horizontal bar chart
  - **Year-over-Year Trend**: Dual-axis time series (Production + Yield)
  - **Statistics Table**: Aggregated metrics by district

### Critical Alerts System

**Yield Decline Detection**:
- Automatically runs on filtered data
- Displays alert metrics:
  - Total alerts count
  - Critical alerts (>30% decline)
  - Average decline percentage
- **Expandable Table**: Shows top 10 declines with full details

---

## 🚀 Installation & Setup

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- 2GB+ RAM (for large dataset processing)

### Step 1: Clone or Download Repository

```bash
# If using Git
git clone <repository-url>
cd prashant-sinha-assesment

# Or download and extract ZIP file
```

### Step 2: Create Virtual Environment (Recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**Dependencies** (from `requirements.txt`):
- `streamlit` - Web framework
- `streamlit_autorefresh` - Auto-refresh functionality
- `plotly` - Interactive visualizations
- `pandas` - Data manipulation
- `numpy` - Numerical computations

### Step 4: Verify Data Files

Ensure these files are present in the project directory:
- ✅ `India Agriculture Crop Production.csv` (30MB+)
- ✅ `india_state_geo.json` (85MB+)

---

## 🌐 Deployment

### Local Deployment

#### Option 1: Standard Run

```bash
streamlit run app.py
```

The dashboard will be available at:
- **Local URL**: http://localhost:8501
- **Network URL**: http://<your-ip>:8501

#### Option 2: Custom Port

```bash
streamlit run app.py --server.port 8080
```

#### Option 3: Headless Mode (Server)

```bash
streamlit run app.py --server.headless true
```

### Production Deployment

#### Streamlit Cloud (Recommended)

1. **Push to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <your-repo-url>
   git push -u origin main
   ```

2. **Deploy on Streamlit Cloud**:
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Connect GitHub repository
   - Select branch: `main`
   - Main file: `app.py`
   - Click "Deploy"

3. **Configuration** (optional):
   Create `.streamlit/config.toml`:
   ```toml
   [theme]
   primaryColor = "#2E7D32"
   backgroundColor = "#FFFFFF"
   secondaryBackgroundColor = "#F5F5F5"
   textColor = "#262730"
   font = "sans serif"

   [server]
   maxUploadSize = 200
   enableXsrfProtection = true
   ```

#### Docker Deployment

Create `Dockerfile`:
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

#### Heroku Deployment

1. Create `setup.sh`:
   ```bash
   mkdir -p ~/.streamlit/
   echo "\
   [server]\n\
   headless = true\n\
   port = $PORT\n\
   enableCORS = false\n\
   \n\
   " > ~/.streamlit/config.toml
   ```

2. Create `Procfile`:
   ```
   web: sh setup.sh && streamlit run app.py
   ```

3. Deploy:
   ```bash
   heroku create your-app-name
   git push heroku main
   ```

---

## 📖 Usage Guide

### Basic Workflow

1. **Launch Dashboard**:
   ```bash
   streamlit run app.py
   ```

2. **Select Filters** (Left Sidebar):
   - Choose State(s) of interest
   - Select Crop(s) to analyze
   - Pick Season(s) and Year range

3. **Explore Visualizations**:
   - **Dashboard Tab**: Overview charts and trends
   - **Map View Tab**: Geographical analysis

4. **Review Alerts**:
   - Check yield decline alerts at the top
   - Expand table for detailed analysis

### Advanced Features

#### Auto-Refresh
- Dashboard auto-refreshes every 100 seconds
- Configured via `st_autorefresh(interval=100000)`

#### Data Export
- Use Plotly's built-in export (camera icon on charts)
- Formats: PNG, SVG, JPEG

#### Performance Optimization
- Data is cached on first load
- Subsequent filter changes are instant
- Large scatter plots are sampled (5000 points max)

---

## 🔧 Technical Details

### Performance Optimizations

1. **Data Caching**:
   - `@st.cache_data` decorator on `load_data()` and `load_geojson()`
   - Cache persists across user sessions
   - Invalidates only when data files change

2. **Sampling Strategy**:
   - Scatter plots sample 5000 random points if dataset > 5000 rows
   - Maintains statistical representativeness

3. **Lazy Loading**:
   - GeoJSON loaded only when Map View tab is accessed
   - Error handling for missing files

### Data Quality Handling

- **Missing Values**: 
  - Dropped rows with null `Crop` values
  - Filled empty `Season` with empty string
  - Replaced infinity values in `Yield` with `NaN`

- **Data Validation**:
  - Year parsing with error handling
  - Type conversions (string → int for Year)
  - Whitespace trimming on all text fields

### Responsive Design

- **Wide Layout**: `layout="wide"` for maximum screen usage
- **Column Layouts**: 2-column grids for side-by-side comparisons
- **Custom CSS**: Styled alert boxes and metric cards

### Browser Compatibility

Tested on:
- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

---

## 📁 File Structure

```
prashant-sinha-assesment/
│
├── app.py                                  # Main application (658 lines)
│   ├── Data Loading & Preprocessing        # Lines 73-103
│   ├── Data Processing Functions           # Lines 106-166
│   ├── Visualization Functions             # Lines 169-371
│   └── Main Application Logic              # Lines 375-658
│
├── requirements.txt                        # Python dependencies (5 packages)
│
├── India Agriculture Crop Production.csv   # Dataset (30MB, 345K+ records)
│   └── Columns: State, District, Year, Season, Crop, Area, Production
│
├── india_state_geo.json                    # GeoJSON boundaries (85MB)
│   └── Properties: NAME_1 (state names), geometry
│
├── README.md                               # This file
│
└── .gitignore                              # Git ignore rules
```

### Code Organization

**app.py** is structured into logical sections:

1. **Imports & Configuration** (Lines 1-23)
   - Library imports
   - Streamlit page config
   - Auto-refresh setup

2. **Custom CSS** (Lines 26-62)
   - Styling for headers, alerts, metrics

3. **Constants** (Lines 64-69)
   - Data path
   - Default filter values

4. **Preprocessing Functions** (Lines 73-103)
   - `load_data()`: CSV loading and cleaning
   - `load_geojson()`: GeoJSON loading

5. **Data Processing Functions** (Lines 106-166)
   - `calculate_yield_decline()`: Alert detection
   - `get_state_average_yield()`: State metrics
   - `prepare_correlation_data()`: Correlation matrix
   - `prepare_time_series()`: Time-based aggregation

6. **Visualization Functions** (Lines 169-371)
   - `plot_correlation_matrix()`: Heatmap
   - `plot_time_series()`: Multi-line chart
   - `plot_top_districts()`: Bar chart
   - `plot_yield_vs_area()`: Scatter plot
   - `plot_yield_area_scatter()`: Aggregated scatter
   - `plot_cropwise_production()`: Crop comparison

7. **Main Application** (Lines 375-658)
   - Filter controls
   - Layout management
   - Tab navigation
   - Alert display
   - Map view with district drill-down

---

## 🎯 Key Metrics & Insights

### Success Metric Implementation

**Yield Decline Detection** (>10% over 5 years):

```python
# Severity Classification
if decline_pct > 30:
    severity = 'Critical'
elif decline_pct > 20:
    severity = 'High'
else:
    severity = 'Moderate'
```

**Display Logic**:
- Alerts shown only if `len(decline_df) > 0`
- Top 10 declines displayed in expandable table
- Metrics: Total alerts, Critical count, Average decline

### Data Insights

The dashboard enables analysis of:
- **Temporal Trends**: Year-over-year production changes
- **Spatial Patterns**: State and district comparisons
- **Crop Performance**: Yield efficiency across crops
- **Seasonal Variations**: Season-specific production
- **Correlations**: Relationships between Area, Production, Yield

---

## 🐛 Troubleshooting

### Common Issues

1. **Port Already in Use**:
   ```bash
   streamlit run app.py --server.port 8080
   ```

2. **Data File Not Found**:
   - Verify `India Agriculture Crop Production.csv` is in project root
   - Check file name spelling (case-sensitive on Linux/Mac)

3. **GeoJSON Map Not Loading**:
   - Ensure `india_state_geo.json` is present
   - Dashboard will show error message and fallback to statistics

4. **Slow Performance**:
   - Clear Streamlit cache: Press 'C' in browser
   - Reduce filter selections (fewer states/crops)
   - Check available RAM (2GB+ recommended)

5. **Module Not Found**:
   ```bash
   pip install -r requirements.txt --upgrade
   ```

---

## 📊 Dataset Information

**Source**: India Agriculture Crop Production Dataset

**Size**: 30MB+ (345,000+ records)

**Columns**:
- `State`: Indian state name
- `District`: District name
- `Year`: Year in "YYYY-MM" format (parsed to integer)
- `Season`: Growing season (Kharif, Rabi, Summer, etc.)
- `Crop`: Crop name
- `Area`: Cultivated area (hectares)
- `Production`: Total production (tonnes)

**Derived Column**:
- `Yield`: Production / Area (tonnes per hectare)

**Time Range**: Multiple years (check dashboard for exact range)

---

## 🤝 Contributing

To contribute or modify:

1. Fork the repository
2. Create a feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

---

## 📝 License

This project is created for assessment purposes.

---

## 📧 Contact

For questions or issues, please contact the repository owner.

---

**Last Updated**: December 2025

**Version**: 1.0.0
