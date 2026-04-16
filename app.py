import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import kagglehub
import os
from pathlib import Path

# Page Configuration
st.set_page_config(
    page_title="Corporate Treasury Dashboard",
    page_icon="📊",
    layout="wide"
)

# Title
st.title("Corporate Treasury Dashboard")
st.markdown("### Cash and Liquidity Management")

# Download and Load Kaggle Dataset
@st.cache_data
def load_kaggle_dataset():
    """
    Download the S&P 500 financial dataset from Kaggle and process it for treasury dashboard
    Dataset: S&P 500 Companies with Financial Information
    Source: https://www.kaggle.com/datasets/andrewmvd/sp-500-stocks
    """
    
    try:
        # Download latest version of the dataset
        path = kagglehub.dataset_download("andrewmvd/sp-500-stocks")
        
        # Read the financial metrics file
        financial_path = os.path.join(path, "sp500_companies.csv")
        stocks_path = os.path.join(path, "sp500_stocks.csv")
        
        if os.path.exists(financial_path) and os.path.exists(stocks_path):
            companies_df = pd.read_csv(financial_path)
            stocks_df = pd.read_csv(stocks_path)
            
            return companies_df, stocks_df
        else:
            st.error("Dataset files not found in the expected location.")
            return None, None
            
    except Exception as e:
        st.error(f"Error downloading dataset: {str(e)}")
        return None, None

@st.cache_data
def process_treasury_data(companies_df, stocks_df):
    """
    Transform S&P 500 data into treasury-relevant metrics
    """
    if companies_df is None or stocks_df is None:
        return generate_fallback_data()
    
    try:
        # Display available columns for debugging (can be removed in production)
        st.sidebar.markdown("**Available columns in dataset:**")
        st.sidebar.text(f"Companies: {list(companies_df.columns)}")
        
        # Convert stock data dates
        stocks_df['Date'] = pd.to_datetime(stocks_df['Date'])
        
        # Filter to last 90 days for performance
        latest_date = stocks_df['Date'].max()
        start_date = latest_date - timedelta(days=90)
        recent_stocks = stocks_df[stocks_df['Date'] >= start_date].copy()
        
        # Check available columns and create mapping
        available_columns = companies_df.columns.tolist()
        
        # Identify which columns exist
        symbol_col = 'Symbol' if 'Symbol' in available_columns else available_columns[0]
        sector_col = 'Sector' if 'Sector' in available_columns else None
        
        # Market cap column variations
        marketcap_col = None
        for col in ['Marketcap', 'MarketCap', 'marketcap', 'Market Cap']:
            if col in available_columns:
                marketcap_col = col
                break
        
        # If no market cap, use a default calculation
        if marketcap_col is None:
            st.warning("Market capitalization data not found. Using estimates.")
            recent_stocks['Estimated_Marketcap'] = recent_stocks.groupby('Symbol')['Close'].transform('mean') * 1e9
            marketcap_col = 'Estimated_Marketcap'
            companies_df[marketcap_col] = recent_stocks.groupby('Symbol')['Estimated_Marketcap'].mean().values
        
        # Merge with company info - only use columns that exist
        merge_columns = [symbol_col]
        if sector_col:
            merge_columns.append(sector_col)
        
        # Add marketcap to merge columns if it exists in companies_df
        if marketcap_col in companies_df.columns:
            merge_columns.append(marketcap_col)
        
        merged_df = recent_stocks.merge(
            companies_df[merge_columns], 
            on=symbol_col, 
            how='left'
        )
        
        # If sector is missing, create a default
        if sector_col is None or sector_col not in merged_df.columns:
            merged_df['Sector'] = 'Other'
        else:
            merged_df['Sector'] = merged_df[sector_col].fillna('Other')
        
        # Ensure marketcap column exists
        if marketcap_col not in merged_df.columns:
            merged_df[marketcap_col] = 1e10  # Default value
        
        # Calculate treasury metrics based on market cap
        merged_df['Cash_Estimate'] = merged_df[marketcap_col] * 0.10  # 10% of market cap as cash
        merged_df['Short_Term_Debt_Estimate'] = merged_df[marketcap_col] * 0.05
        merged_df['Long_Term_Debt_Estimate'] = merged_df[marketcap_col] * 0.25
        merged_df['Accounts_Receivable_Estimate'] = merged_df[marketcap_col] * 0.08
        merged_df['Accounts_Payable_Estimate'] = merged_df[marketcap_col] * 0.06
        
        # Group by sector for entity-level view
        sector_agg = merged_df.groupby(['Date', 'Sector']).agg({
            'Close': 'mean',
            'Cash_Estimate': 'sum',
            'Short_Term_Debt_Estimate': 'sum',
            'Long_Term_Debt_Estimate': 'sum',
            'Accounts_Receivable_Estimate': 'sum',
            'Accounts_Payable_Estimate': 'sum'
        }).reset_index()
        
        # Rename columns for dashboard consistency
        sector_agg.rename(columns={
            'Sector': 'Entity',
            'Cash_Estimate': 'Cash_Balance_USD',
            'Short_Term_Debt_Estimate': 'Short_Term_Debt',
            'Long_Term_Debt_Estimate': 'Long_Term_Debt',
            'Accounts_Receivable_Estimate': 'Accounts_Receivable',
            'Accounts_Payable_Estimate': 'Accounts_Payable'
        }, inplace=True)
        
        sector_agg['Currency'] = 'USD'
        
        return sector_agg
        
    except Exception as e:
        st.error(f"Error processing data: {str(e)}")
        return generate_fallback_data()

def generate_fallback_data():
    """
    Generate fallback data if Kaggle download fails
    """
    st.warning("Using generated sample data. Kaggle dataset unavailable.")
    
    np.random.seed(42)
    dates = pd.date_range(end=datetime.now(), periods=90, freq='D')
    entities = ['Technology', 'Healthcare', 'Financial Services', 'Consumer Cyclical', 'Industrials']
    
    data = []
    for date in dates:
        for entity in entities:
            data.append({
                'Date': date,
                'Entity': entity,
                'Currency': 'USD',
                'Cash_Balance_USD': np.random.uniform(5000000000, 50000000000),
                'Short_Term_Debt': np.random.uniform(1000000000, 15000000000),
                'Long_Term_Debt': np.random.uniform(10000000000, 100000000000),
                'Accounts_Receivable': np.random.uniform(2000000000, 20000000000),
                'Accounts_Payable': np.random.uniform(1500000000, 15000000000)
            })
    
    return pd.DataFrame(data)

# Load and process data
with st.spinner("Loading financial data from Kaggle..."):
    companies_df, stocks_df = load_kaggle_dataset()
    
    if companies_df is not None and stocks_df is not None:
        df = process_treasury_data(companies_df, stocks_df)
    else:
        df = generate_fallback_data()

if df is None or df.empty:
    st.error("Failed to load dataset. Please check your internet connection and try again.")
    st.stop()

# Sidebar Filters
st.sidebar.header("Filters")
selected_entities = st.sidebar.multiselect(
    "Select Sectors",
    options=sorted(df['Entity'].unique()),
    default=sorted(df['Entity'].unique())[:5]
)

date_range = st.sidebar.date_input(
    "Date Range",
    value=(df['Date'].min().date(), df['Date'].max().date()),
    min_value=df['Date'].min().date(),
    max_value=df['Date'].max().date()
)

# Filter data
filtered_df = df[
    (df['Entity'].isin(selected_entities)) &
    (df['Date'].dt.date >= date_range[0]) &
    (df['Date'].dt.date <= date_range[1])
]

# Data source attribution
st.sidebar.markdown("---")
st.sidebar.markdown("**Data Source:**")
st.sidebar.markdown("[S&P 500 Companies Dataset](https://www.kaggle.com/datasets/andrewmvd/sp-500-stocks)")
st.sidebar.markdown("via Kaggle")

# KPI Metrics Row
st.markdown("### Key Performance Indicators")
col1, col2, col3, col4, col5 = st.columns(5)

latest_date = filtered_df['Date'].max()
latest_data = filtered_df[filtered_df['Date'] == latest_date]
earliest_data = filtered_df[filtered_df['Date'] == filtered_df['Date'].min()]

with col1:
    total_cash = latest_data['Cash_Balance_USD'].sum()
    cash_change = ((total_cash / earliest_data['Cash_Balance_USD'].sum() - 1) * 100) if not earliest_data.empty and earliest_data['Cash_Balance_USD'].sum() > 0 else 0
    st.metric(
        "Total Cash Position (USD)",
        f"${total_cash/1e9:,.1f}B",
        delta=f"{cash_change:.1f}%"
    )

with col2:
    total_debt = latest_data['Short_Term_Debt'].sum() + latest_data['Long_Term_Debt'].sum()
    st.metric(
        "Total Debt (USD)",
        f"${total_debt/1e9:,.1f}B"
    )

with col3:
    net_cash = total_cash - total_debt
    st.metric(
        "Net Cash Position (USD)",
        f"${net_cash/1e9:,.1f}B",
        delta_color="inverse" if net_cash < 0 else "normal"
    )

with col4:
    if latest_data['Short_Term_Debt'].sum() > 0:
        current_ratio = (latest_data['Cash_Balance_USD'].sum() + latest_data['Accounts_Receivable'].sum()) / latest_data['Short_Term_Debt'].sum()
    else:
        current_ratio = 0
    st.metric(
        "Current Ratio",
        f"{current_ratio:.2f}"
    )

with col5:
    entity_count = len(selected_entities)
    st.metric(
        "Sectors Analyzed",
        f"{entity_count}"
    )

# Charts Section
st.markdown("---")
col_left, col_right = st.columns(2)

with col_left:
    st.markdown("### Cash Position Trend by Sector")
    cash_trend = filtered_df.groupby(['Date', 'Entity'])['Cash_Balance_USD'].sum().reset_index()
    fig_cash = px.line(
        cash_trend,
        x='Date',
        y='Cash_Balance_USD',
        color='Entity',
        title="Cash Balance Trend by Sector (USD)"
    )
    fig_cash.update_layout(
        height=400,
        yaxis_title="Cash Balance (USD)",
        legend_title="Sector"
    )
    st.plotly_chart(fig_cash, use_container_width=True)

with col_right:
    st.markdown("### Cash Distribution by Sector")
    sector_distribution = filtered_df.groupby('Entity')['Cash_Balance_USD'].sum().reset_index()
    fig_sector = px.pie(
        sector_distribution,
        values='Cash_Balance_USD',
        names='Entity',
        title="Cash Holdings Distribution"
    )
    fig_sector.update_layout(height=400)
    st.plotly_chart(fig_sector, use_container_width=True)

# Bottom Section
col_bottom_left, col_bottom_right = st.columns(2)

with col_bottom_left:
    st.markdown("### Liquidity Ratios by Sector")
    entity_metrics = filtered_df.groupby('Entity').agg({
        'Cash_Balance_USD': 'mean',
        'Short_Term_Debt': 'mean',
        'Accounts_Receivable': 'mean',
        'Accounts_Payable': 'mean'
    }).reset_index()
    
    entity_metrics['Current_Ratio'] = (entity_metrics['Cash_Balance_USD'] + entity_metrics['Accounts_Receivable']) / entity_metrics['Short_Term_Debt'].replace(0, np.nan)
    entity_metrics['Quick_Ratio'] = entity_metrics['Cash_Balance_USD'] / entity_metrics['Short_Term_Debt'].replace(0, np.nan)
    
    # Remove infinite values
    entity_metrics = entity_metrics.replace([np.inf, -np.inf], np.nan).dropna(subset=['Current_Ratio', 'Quick_Ratio'])
    
    if not entity_metrics.empty:
        fig_ratios = go.Figure(data=[
            go.Bar(name='Current Ratio', x=entity_metrics['Entity'], y=entity_metrics['Current_Ratio']),
            go.Bar(name='Quick Ratio', x=entity_metrics['Entity'], y=entity_metrics['Quick_Ratio'])
        ])
        fig_ratios.update_layout(
            title="Average Liquidity Ratios by Sector",
            barmode='group',
            height=400,
            yaxis_title="Ratio",
            xaxis_title="Sector"
        )
        fig_ratios.add_hline(y=1.0, line_dash="dash", line_color="red", 
                             annotation_text="Minimum Threshold")
        st.plotly_chart(fig_ratios, use_container_width=True)
    else:
        st.warning("Insufficient data to calculate liquidity ratios.")

with col_bottom_right:
    st.markdown("### Detailed Treasury Data by Sector")
    
    # Create pivot table with formatted values
    pivot_df = filtered_df.pivot_table(
        index='Date',
        columns='Entity',
        values='Cash_Balance_USD',
        aggfunc='sum'
    ).round(2)
    
    # Format as billions for readability
    display_df = pivot_df / 1e9
    
    st.dataframe(
        display_df.style.format("${:.2f}B"),
        height=400,
        use_container_width=True
    )

# Additional Financial Metrics Section
st.markdown("---")
st.markdown("### Sector Financial Summary")

# Limit to first 4 sectors for display
display_sectors = selected_entities[:4]
if display_sectors:
    summary_cols = st.columns(len(display_sectors))

    for idx, entity in enumerate(display_sectors):
        entity_data = filtered_df[filtered_df['Entity'] == entity]
        latest_entity = entity_data[entity_data['Date'] == latest_date]
        
        if not latest_entity.empty:
            latest_entity = latest_entity.iloc[0]
            with summary_cols[idx]:
                st.markdown(f"**{entity}**")
                st.markdown(f"Cash: ${latest_entity['Cash_Balance_USD']/1e9:.2f}B")
                st.markdown(f"Debt: ${(latest_entity['Short_Term_Debt'] + latest_entity['Long_Term_Debt'])/1e9:.2f}B")
                if latest_entity['Short_Term_Debt'] > 0:
                    ratio = (latest_entity['Cash_Balance_USD'] + latest_entity['Accounts_Receivable']) / latest_entity['Short_Term_Debt']
                    st.markdown(f"Current Ratio: {ratio:.2f}")

# Footer
st.markdown("---")
st.markdown(f"""
<div style='text-align: center; color: #666;'>
    <p>Corporate Treasury Dashboard | Data: S&P 500 Companies | Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
</div>
""", unsafe_allow_html=True)

# Download Section
st.sidebar.markdown("---")
st.sidebar.markdown("### Export Data")
csv = filtered_df.to_csv(index=False)
st.sidebar.download_button(
    label="Download Filtered Data (CSV)",
    data=csv,
    file_name=f"treasury_dashboard_{datetime.now().strftime('%Y%m%d')}.csv",
    mime="text/csv"
)

# Dataset Information
with st.sidebar.expander("Dataset Information"):
    st.markdown("""
    **S&P 500 Companies Dataset**
    
    This dashboard uses financial data from S&P 500 companies, aggregated by sector.
    
    **Metrics displayed:**
    - Cash positions (estimated from market cap)
    - Debt levels
    - Liquidity ratios
    - Receivables and payables
    
    Data is updated from Kaggle on each application restart.
    """)