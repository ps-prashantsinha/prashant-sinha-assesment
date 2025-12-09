import io
import random
import warnings
from datetime import datetime

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from streamlit_autorefresh import st_autorefresh


warnings.filterwarnings("ignore")
st_autorefresh(interval=100000, limit=None, key="datarefresh")


st.set_page_config(
    page_title="Crop Production & Yield Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2E7D32;
        text-align: center;
        margin-bottom: 1rem;
    }
    .alert-box {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border-left: 5px solid;
    }
    .alert-danger {
        background-color: #ffebee;
        border-color: #c62828;
    }
    .alert-warning {
        background-color: #fff3e0;
        border-color: #ef6c00;
    }
    .alert-info {
        background-color: #e3f2fd;
        border-color: #1565c0;
    }
    .metric-card {
        background-color: #f5f5f5;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    </style>
""", 
unsafe_allow_html=True
)

DATA_PATH = "India Agriculture Crop Production.csv"

DEFAULT_STATE = 'Gujarat'
DEFAULT_CROP = 'Rice'
DEFAULT_SEASON = 'Kharif'
DEFAULT_YEARS_LIST = range(2016,2021,1)

# ==================== PREPROCESSING ====================

@st.cache_data
def load_data():
    """Load and preprocess the agriculture dataset"""
    df = pd.read_csv(DATA_PATH)
    
    df.columns = df.columns.str.strip()
    # print(df.info())
    
    # Parse Year column from "YYYY-MM" format to integer year
    df['Year'] = df['Year'].astype(str).str.split('-').str[0].astype(int)
    
    # Calculate Yield (Production per unit Area)
    df['Yield'] = df['Production'] / df['Area']
    df['Yield'] = df['Yield'].replace([np.inf, -np.inf], np.nan)
    
    # Clean text fields
    df['State'] = df['State'].str.strip()
    df['District'] = df['District'].str.strip()
    df['Crop'] = df['Crop'].str.strip()
    df['Season'] = df['Season'].fillna('').str.strip()
    
    df = df.dropna(subset=['Crop'])

    return df

@st.cache_data
def load_geojson():
    import json
    with open('india_state_geo.json', 'r', encoding='utf-8') as f:
        return json.load(f)

# ==================== DATA PROCESSING FUNCTIONS ====================

def calculate_yield_decline(df, years=5):
    """ Identify states with >10% yield decline over specified years """
    current_year = df['Year'].max()
    start_year = current_year - years
    
    # Filter data for the period
    period_data = df[(df['Year'] >= start_year) & (df['Year'] <= current_year)]
    
    decline_list = []
    
    for crop in period_data['Crop'].unique():
        for state in period_data['State'].unique():
            subset = period_data[(period_data['Crop'] == crop) & 
                                (period_data['State'] == state)]
            
            if len(subset) < 2:
                continue
            
            # Calculate average yield for first and last 2 years
            early_years = subset[subset['Year'] <= start_year + 2]['Yield'].mean()
            recent_years = subset[subset['Year'] >= current_year - 2]['Yield'].mean()
            
            if pd.notna(early_years) and pd.notna(recent_years) and early_years > 0:
                decline_pct = ((early_years - recent_years) / early_years) * 100
                
                if decline_pct > 10:  # Only include declines > 10%
                    severity = 'Critical' if decline_pct > 30 else 'High' if decline_pct > 20 else 'Moderate'
                    decline_list.append({
                        'Crop': crop,
                        'State': state,
                        'Decline_Percentage': round(decline_pct, 2),
                        'Early_Yield': round(early_years, 2),
                        'Recent_Yield': round(recent_years, 2),
                        'Severity': severity
                    })
    
    if decline_list:
        return pd.DataFrame(decline_list).sort_values('Decline_Percentage', ascending=False)
    else:
        # Return empty DataFrame with proper columns
        return pd.DataFrame(columns=['Crop', 'State', 'Decline_Percentage', 'Early_Yield', 'Recent_Yield', 'Severity'])

def get_state_average_yield(df, crop, year):
    """Calculate state-level average yield for a specific crop and year"""
    subset = df[(df['Crop'] == crop) & (df['Year'] == year)]
    return subset.groupby('State')['Yield'].mean().to_dict()

def prepare_correlation_data(df):
    """Prepare data for correlation matrix"""
    corr_data = df[['Area', 'Production', 'Yield']].corr()
    return corr_data

def prepare_time_series(df, group_by='Year'):
    """Aggregate data for time series visualization"""
    ts_data = df.groupby(group_by).agg({
        'Area': 'sum',
        'Production': 'sum',
        'Yield': 'mean'
    }).reset_index()
    return ts_data

# ==================== VISUALIZATION FUNCTIONS ====================

def plot_correlation_matrix(df):
    """Display correlation matrix heatmap"""
    corr_data = prepare_correlation_data(df)
    
    fig = go.Figure(data=go.Heatmap(
        z=corr_data.values,
        x=corr_data.columns,
        y=corr_data.columns,
        colorscale='RdYlGn',
        zmid=0,
        text=corr_data.values.round(3),
        texttemplate='%{text}',
        textfont={"size": 14},
        colorbar=dict(title="Correlation")
    ))
    
    fig.update_layout(
        title="Correlation Matrix",
        height=400,
        xaxis_title="",
        yaxis_title=""
    )
    
    return fig

def plot_time_series(df):
    """Create multi-line time series chart"""
    ts_data = prepare_time_series(df)
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Area and Production on primary y-axis
    fig.add_trace(
        go.Scatter(x=ts_data['Year'], y=ts_data['Area'], 
                  name='Area', mode='lines+markers',
                  line=dict(color='#1976D2', width=2)),
        secondary_y=False
    )
    
    fig.add_trace(
        go.Scatter(x=ts_data['Year'], y=ts_data['Production'], 
                  name='Production', mode='lines+markers',
                  line=dict(color='#388E3C', width=2)),
        secondary_y=False
    )
    
    # Yield on secondary y-axis
    fig.add_trace(
        go.Scatter(x=ts_data['Year'], y=ts_data['Yield'], 
                  name='Yield', mode='lines+markers',
                  line=dict(color='#D32F2F', width=2)),
        secondary_y=True
    )
    
    fig.update_xaxes(title_text="Year")
    fig.update_yaxes(title_text="Area / Production", secondary_y=False)
    fig.update_yaxes(title_text="Yield", secondary_y=True)
    
    fig.update_layout(
        title="Time Series - Area, Production & Yield",
        height=400,
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig

def plot_top_districts(df, top_n=10):
    """Bar chart of top producing districts"""
    district_prod = df.groupby('District')['Production'].sum().reset_index()
    district_prod = district_prod.nlargest(top_n, 'Production')
    
    fig = go.Figure(go.Bar(
        x=district_prod['Production'],
        y=district_prod['District'],
        orientation='h',
        marker=dict(
            color=district_prod['Production'],
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="Production")
        ),
        text=district_prod['Production'].round(0),
        textposition='auto'
    ))
    
    fig.update_layout(
        title=f"Top {top_n} Producing Districts",
        xaxis_title="Total Production",
        yaxis_title="District",
        height=400,
        yaxis={'categoryorder': 'total ascending'}
    )
    
    return fig

def plot_yield_vs_area(df):
    """Scatter plot of Yield vs Production Area"""
    # Sample data if too large
    plot_data = df.dropna(subset=['Area', 'Yield', 'Production'])
    if len(plot_data) > 5000:
        plot_data = plot_data.sample(5000, random_state=42)
    
    fig = px.scatter(
        plot_data,
        x='Area',
        y='Yield',
        size='Production',
        color='Crop',
        hover_data=['State', 'District', 'Year'],
        title="Yield vs Production Area",
        labels={'Area': 'Production Area', 'Yield': 'Yield (Production/Area)'}
    )
    
    fig.update_layout(height=400)
    
    return fig

def plot_yield_map(df):
    """Choropleth map of yield by state"""
    state_yield = df.groupby('State').agg({
        'Yield': 'mean',
        'Production': 'sum',
        'Area': 'sum'
    }).reset_index()
    
    fig = px.choropleth(
        state_yield,
        locations='State',
        locationmode='country names',
        color='Yield',
        hover_name='State',
        hover_data={'Yield': ':.2f', 'Production': ':.0f', 'Area': ':.0f'},
        title="Average Yield by State",
        color_continuous_scale='YlGn',
        scope='asia'
    )
    
    fig.update_geos(
        center=dict(lat=20.5937, lon=78.9629),
        projection_scale=4
    )
    
    fig.update_layout(height=500)
    
    return fig

def plot_yield_area_scatter(yield_prod):
    """Scatter plot of Yield vs Production Area (Aggregated by State and Crop)"""
    # Aggregate data by State and Crop
    # yield_prod = df.groupby(['State', 'District' 'Crop']).agg({
    #     'Area': 'sum',
    #     'Production': 'sum',
    #     'Yield': 'mean'
    # }).reset_index()
    
    # Remove any rows with missing values
    yield_prod = yield_prod.dropna(subset=['Area', 'Yield'])
    
    # if len(yield_prod) > 1000:
    #     yield_prod = yield_prod.sample(1000, random_state=42)
    
    fig = px.scatter(
        yield_prod,
        x='Area',
        y='Yield',
        # size='Production',
        color='State',
        hover_data=['Crop', 'Area'],
        title="Yield vs Production Area",
        labels={
            'Area': 'Production Area', 
            'Yield': 'Yield'
            # 'Production': 'Total Production'
        }
    )
    
    fig.update_layout(height=400)
    
    return fig



def plot_cropwise_production(df):
    """Time series of crop-wise production"""
    crop_ts = df.groupby(['Year', 'Crop'])['Production'].sum().reset_index()
    
    fig = px.line(
        crop_ts,
        x='Year',
        y='Production',
        color='Crop',
        title="Crop-wise Production Over Time",
        markers=True
    )
    
    fig.update_layout(
        height=400,
        hovermode='x unified',
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02)
    )
    
    return fig

# ==================== MAIN APPLICATION ====================

def main():
    st.markdown(
        '<div class="main-header">Crop Production & Yield Dashboard</div>',
        unsafe_allow_html=True
    )
    
    with st.spinner('Loading data...'):
        df = load_data()
        india_geojson = load_geojson()
    
    st.sidebar.header("Filters")
    
    # State filter
    all_states = sorted(df['State'].unique().tolist())
    default_states = random.sample(all_states, 1)
    selected_states = st.sidebar.multiselect(
        "State (multi-select)",
        options=all_states,
        default=DEFAULT_STATE or default_states
    )
    
    # Filter districts based on selected states
    if selected_states:
        available_districts = sorted(df[df['State'].isin(selected_states)]['District'].unique().tolist())
    else:
        available_districts = sorted(df['District'].unique().tolist())
    
    selected_districts = st.sidebar.multiselect(
        "District (multi-select)",
        options=available_districts,
        default=available_districts
    )
    
    # Crop filter
    all_crops = sorted(df['Crop'].unique().tolist())
    selected_crops = st.sidebar.multiselect(
        "Crop (multi-select)",
        options=all_crops,
        default=DEFAULT_CROP or random.sample(all_crops, 1)
    )
    
    # Season filter
    all_seasons = sorted(df['Season'].dropna().unique().tolist())
    selected_seasons = st.sidebar.multiselect(
        "Season (multi-select)",
        options=all_seasons,
        default=DEFAULT_SEASON or random.sample(all_seasons, 1)
    )
    
    # Year filter
    # Year column is already parsed as integer in load_data()
    df_clean_year = df.dropna(subset=['Year'])
    if len(df_clean_year) > 0:
        min_year = int(df_clean_year['Year'].min())
        max_year = int(df_clean_year['Year'].max())
        selected_years = st.sidebar.multiselect(
            "Year Selector (multi-select)",
            options=list(range(min_year, max_year + 1)),
            default=list(range(max_year - 5, max_year + 1))
        )
    else:
        selected_years = []
    
    # Apply filters to the data
    filtered_df = df.copy()

    if selected_states:
        filtered_df = filtered_df[filtered_df['State'].isin(selected_states)]
    if selected_districts:
        filtered_df = filtered_df[filtered_df['District'].isin(selected_districts)]
    if selected_crops:
        filtered_df = filtered_df[filtered_df['Crop'].isin(selected_crops)]
    if selected_seasons:
        filtered_df = filtered_df[filtered_df['Season'].isin(selected_seasons)]
    if selected_years:
        filtered_df = filtered_df[filtered_df['Year'].isin(selected_years)]
    
    # Display filter summary
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Filtered Records:** {len(filtered_df):,}")
    st.sidebar.markdown(f"**Date Range:** {filtered_df['Year'].min():.0f} - {filtered_df['Year'].max():.0f}")
    
    # Calculate yield decline
    decline_df = calculate_yield_decline(filtered_df, years=5)
    
    # SUCCESS METRICS: Display alerts for yield decline
    if len(decline_df) > 0:
        st.markdown("### 🚨 Critical Alerts: Yield Decline Detection")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Alerts", len(decline_df))
        with col2:
            critical_count = len(decline_df[decline_df['Severity'] == 'Critical'])
            st.metric("Critical (>30%)", critical_count)
        with col3:
            avg_decline = decline_df['Decline_Percentage'].mean()
            st.metric("Avg Decline", f"{avg_decline:.1f}%")
        
        # Show top 5 declines
        with st.expander("📊 View Detailed Decline Analysis", expanded=True):
            st.dataframe(
                decline_df.head(10),
                width='stretch',
                hide_index=True
            )
    
    # Navigation tabs
    tab1, tab2 = st.tabs(["📊 Dashboard", "🗺️ Map View"])
    
    with tab1:
        # Correlation Matrix and Time Series
        col1, col2 = st.columns(2)
        
        with col1:
            st.plotly_chart(plot_correlation_matrix(filtered_df), width='stretch')
        with col2:
            st.plotly_chart(plot_time_series(filtered_df), width='stretch')
        
        # Top Districts and Yield vs Area
        col1, col2 = st.columns(2)
        
        with col1:
            st.plotly_chart(plot_top_districts(filtered_df), width='stretch')
        with col2:
            st.plotly_chart(plot_yield_vs_area(filtered_df), width='stretch')
        
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(plot_yield_area_scatter(filtered_df), width='stretch')
        with col2:
            # Crop-wise Production
            st.plotly_chart(plot_cropwise_production(filtered_df), width='stretch')
    
    with tab2:
        st.markdown("### 🗺️ Interactive India State Map")
        
        try:            
            # Prepare state-level data
            state_data = filtered_df.groupby('State').agg({
                'Yield': 'mean',
                'Production': 'sum',
                'Area': 'sum'
            }).reset_index()
            
            # Create choropleth map using the GeoJSON
            fig_map = px.choropleth(
                state_data,
                geojson=india_geojson,
                locations='State',
                featureidkey='properties.NAME_1',
                color='Yield',
                hover_name='State',
                hover_data={'Yield': ':.2f', 'Production': ':.0f', 'Area': ':.0f', 'State': False},
                title="Click on a state to view district-level details",
                color_continuous_scale='YlGn',
                labels={'Yield': 'Average Yield'}
            )
            
            fig_map.update_geos(
                fitbounds="locations",
                visible=False
            )
            
            fig_map.update_layout(
                height=600,
                margin={"r":0,"t":30,"l":0,"b":0}
            )
            
            # Display the map
            st.plotly_chart(fig_map, use_container_width=True, key='india_state_map')
            
        except FileNotFoundError:
            st.error("GeoJSON file 'india_state_geo.json' not found. Please ensure the file is in the correct location.")
            st.info("Displaying state-level statistics instead.")
        except Exception as e:
            st.error(f"Error loading map: {str(e)}")
        
        # State selection for district view
        st.markdown("---")
        st.markdown("### 📊 District-Level Analysis")
        
        # Let user select a state
        available_states = sorted(filtered_df['State'].unique().tolist())
        selected_state_for_districts = st.selectbox(
            "Select a State to view district-level details:",
            options=available_states,
            index=0 if len(available_states) > 0 else None
        )
        
        if selected_state_for_districts:
            # Filter data for selected state
            state_df = filtered_df[filtered_df['State'] == selected_state_for_districts]
            
            # District-level production bars and trends
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"#### Top Districts in {selected_state_for_districts}")
                district_prod = state_df.groupby('District')['Production'].sum().reset_index()
                district_prod = district_prod.nlargest(10, 'Production')
                
                fig_district_bar = go.Figure(go.Bar(
                    x=district_prod['Production'],
                    y=district_prod['District'],
                    orientation='h',
                    marker=dict(
                        color=district_prod['Production'],
                        colorscale='Viridis',
                        showscale=True
                    ),
                    text=district_prod['Production'].round(0),
                    textposition='auto'
                ))
                
                fig_district_bar.update_layout(
                    title=f"Top 10 Districts by Production",
                    xaxis_title="Total Production",
                    yaxis_title="District",
                    height=400,
                    yaxis={'categoryorder': 'total ascending'}
                )
                
                st.plotly_chart(fig_district_bar, use_container_width=True)
            
            with col2:
                st.markdown(f"#### Year-over-Year Trend in {selected_state_for_districts}")
                # Year-over-year trend
                year_trend = state_df.groupby('Year').agg({
                    'Production': 'sum',
                    'Area': 'sum',
                    'Yield': 'mean'
                }).reset_index()
                
                fig_trend = make_subplots(specs=[[{"secondary_y": True}]])
                
                fig_trend.add_trace(
                    go.Scatter(
                        x=year_trend['Year'],
                        y=year_trend['Production'],
                        name='Production',
                        mode='lines+markers',
                        line=dict(color='#388E3C', width=2)
                    ),
                    secondary_y=False
                )
                
                fig_trend.add_trace(
                    go.Scatter(
                        x=year_trend['Year'],
                        y=year_trend['Yield'],
                        name='Yield',
                        mode='lines+markers',
                        line=dict(color='#D32F2F', width=2)
                    ),
                    secondary_y=True
                )
                
                fig_trend.update_xaxes(title_text="Year")
                fig_trend.update_yaxes(title_text="Production", secondary_y=False)
                fig_trend.update_yaxes(title_text="Yield", secondary_y=True)
                
                fig_trend.update_layout(
                    title="Production & Yield Trend Over Time",
                    height=400,
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig_trend, use_container_width=True)
            
            # District statistics table
            st.markdown(f"#### District Statistics for {selected_state_for_districts}")
            district_stats = state_df.groupby('District').agg({
                'Production': 'sum',
                'Area': 'sum',
                'Yield': 'mean'
            }).round(2).reset_index()
            district_stats.columns = ['District', 'Total Production', 'Total Area', 'Avg Yield']
            district_stats = district_stats.sort_values('Total Production', ascending=False)
            st.dataframe(district_stats, use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()
