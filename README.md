# Corporate Treasury Dashboard

A Streamlit-based dashboard for corporate treasury management using real financial data from S&P 500 companies via Kaggle. The application provides sector-level visibility into cash positions, debt levels, and liquidity metrics.

## Table of Contents
- [Features](#features)
- [Dashboard Components](#dashboard-components)
- [Data Source](#data-source)
- [Installation](#installation)
- [Project Structure](#project-structure)
- [System Architecture](#system-architecture)
- [Code Explanation](#code-explanation)
- [Data Flow Diagram](#data-flow-diagram)
- [Component Interaction Diagram](#component-interaction-diagram)
- [Caching Mechanism](#caching-mechanism)
- [Customization Guide](#customization-guide)
- [Troubleshooting](#troubleshooting)
- [Dependencies](#dependencies)
- [License](#license)

## Features

- Real S&P 500 financial data pulled directly from Kaggle
- Robust column detection with automatic fallback for missing data
- Sector-level cash position monitoring and trend analysis
- Liquidity analysis with current and quick ratios
- Interactive filtering by sector and date range
- CSV export functionality for filtered data
- Graceful error handling with fallback data generation
- Responsive layout with multiple visualization panels

## Dashboard Components

### Key Metrics
- Total Cash Position (USD billions)
- Total Debt (USD billions)
- Net Cash Position
- Current Ratio
- Sectors Analyzed Count

### Visualizations
1. Cash Position Trend: Time series line chart showing cash balance evolution by sector
2. Sector Distribution: Pie chart displaying cash holdings distribution across sectors
3. Liquidity Ratios: Grouped bar chart comparing current and quick ratios by sector
4. Detailed Data Table: Pivot table view of cash positions with billion-dollar formatting

## Data Source

This application uses the [S&P 500 Companies with Financial Information](https://www.kaggle.com/datasets/andrewmvd/sp-500-stocks) dataset from Kaggle, which includes:
- Historical stock prices for S&P 500 companies (last 10 years)
- Company financial metrics (market capitalization, EBITDA, revenue growth)
- Sector classifications
- Daily trading data

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Internet connection (for initial dataset download)

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/corporate-treasury-dashboard.git
cd corporate-treasury-dashboard

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py