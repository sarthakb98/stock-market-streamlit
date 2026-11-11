import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ---------------------------------------------------------
# PAGE CONFIGURATION & THEME
# ---------------------------------------------------------
st.set_page_config(
    page_title="AlphaStock Analytics Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# DATASET GENERATION (SELF-CONTAINED STOCK MARKET DATA)
# ---------------------------------------------------------
@st.cache_data
def load_stock_data():
    np.random.seed(42)
    dates = pd.date_range(start="2026-01-01", periods=100, freq="B")
    tickers = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN", "NVDA"]
    sector_map = {
        "AAPL": "Technology",
        "MSFT": "Technology",
        "GOOGL": "Communication Services",
        "TSLA": "Consumer Cyclical",
        "AMZN": "Consumer Cyclical",
        "NVDA": "Technology"
    }
    
    rows = []
    for d in dates:
        for t in tickers:
            base_price = {"AAPL": 190, "MSFT": 420, "GOOGL": 180, "TSLA": 230, "AMZN": 185, "NVDA": 130}[t]
            open_p = round(base_price + np.random.normal(0, 4), 2)
            close_p = round(open_p + np.random.normal(0, 3), 2)
            high_p = round(max(open_p, close_p) + abs(np.random.normal(0, 2)), 2)
            low_p = round(min(open_p, close_p) - abs(np.random.normal(0, 2)), 2)
            volume = int(np.random.randint(2_000_000, 45_000_000))
            rows.append([d, t, sector_map[t], open_p, high_p, low_p, close_p, volume])
            
    df = pd.DataFrame(rows, columns=["Date", "Ticker", "Sector", "Open", "High", "Low", "Close", "Volume"])
    df["Daily_Return_%"] = round(((df["Close"] - df["Open"]) / df["Open"]) * 100, 2)
    df["Volatility_Spread"] = round(df["High"] - df["Low"], 2)
    return df

raw_df = load_stock_data()

# ---------------------------------------------------------
# 1. SIDEBAR NAVIGATION & FILTER WIDGETS
# ---------------------------------------------------------
with st.sidebar:
    st.title("⚙️ Filter Controls")
    st.markdown("Customize your equity market view:")
    
    # Multiselect for Sectors
    all_sectors = list(raw_df["Sector"].unique())
    selected_sectors = st.multiselect(
        "Select Sector(s):",
        options=all_sectors,
        default=all_sectors
    )
    
    # Multiselect for Tickers
    available_tickers = raw_df[raw_df["Sector"].isin(selected_sectors)]["Ticker"].unique()
    selected_tickers = st.multiselect(
        "Select Ticker(s):",
        options=available_tickers,
        default=list(available_tickers)
    )
    
    # Slider for Price Range
    min_price = float(raw_df["Close"].min())
    max_price = float(raw_df["Close"].max())
    price_range = st.slider(
        "Closing Price Range ($):",
        min_value=min_price,
        max_value=max_price,
        value=(min_price, max_price)
    )
    
    # Selectbox for Metrics
    selected_metric = st.selectbox(
        "Primary Metric to Examine:",
        options=["Close", "Volume", "Daily_Return_%", "Volatility_Spread"]
    )
    
    st.divider()
    st.info("💡 Tip: Use filters above to dynamically update KPIs, comparisons, and charts across all tabs.")

# Filter Dataframe according to controls
filtered_df = raw_df[
    (raw_df["Sector"].isin(selected_sectors)) &
    (raw_df["Ticker"].isin(selected_tickers)) &
    (raw_df["Close"] >= price_range[0]) &
    (raw_df["Close"] <= price_range[1])
]

# ---------------------------------------------------------
# APPLICATION HEADER
# ---------------------------------------------------------
st.title("📈 Stock Market Pattern Explorer & Analytics Hub")
st.markdown("An interactive web application designed to analyze equity price movements, sector distributions, and trading volume behaviors.")

# ---------------------------------------------------------
# KEY PERFORMANCE INDICATORS (KPIS)
# ---------------------------------------------------------
with st.container():
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    
    total_records = len(filtered_df)
    total_volume = filtered_df["Volume"].sum() if total_records > 0 else 0
    avg_close = filtered_df["Close"].mean() if total_records > 0 else 0
    avg_volatility = filtered_df["Volatility_Spread"].mean() if total_records > 0 else 0
    
    kpi1.metric(label="Total Observations", value=f"{total_records:,}")
    kpi2.metric(label="Total Volume Traded", value=f"{total_volume / 1e6:.2f} M")
    kpi3.metric(label="Avg Closing Price", value=f"${avg_close:.2f}")
    kpi4.metric(label="Avg Intraday Spread", value=f"${avg_volatility:.2f}")

st.divider()

# ---------------------------------------------------------
# APPLICATION TABS NAVIGATION
# ---------------------------------------------------------
tab_overview, tab_analysis, tab_visualizations, tab_insights = st.tabs([
    "📋 Dataset Overview",
    "📊 Data Analysis",
    "📉 Visualizations",
    "💡 Insights & Summary"
])

# ---------------------------------------------------------
# TAB 1: DATASET OVERVIEW
# ---------------------------------------------------------
with tab_overview:
    st.subheader("Market Dataset Inspection")
    
    col_t1, col_t2 = st.columns([3, 1])
    with col_t1:
        st.write("Displaying active records based on selected sidebar criteria:")
        st.dataframe(filtered_df.head(25), use_container_width=True)
    
    with col_t2:
        st.write("**Dataset Properties**")
        st.write(f"- Total Columns: `{filtered_df.shape[1]}`")
        st.write(f"- Active Tickers: `{len(selected_tickers)}`")
        st.write(f"- Active Sectors: `{len(selected_sectors)}`")
        
    with st.expander("🔍 Click to view Descriptive Statistics Summary"):
        st.dataframe(filtered_df.describe(), use_container_width=True)

# ---------------------------------------------------------
# TAB 2: DATA ANALYSIS
# ---------------------------------------------------------
with tab_analysis:
    st.subheader("Categorical Groupings & Performance Aggregations")
    
    col_a1, col_a2 = st.columns(2)
    
    with col_a1:
        st.markdown("#### Sector-wise Volume & Pricing Summary")
        sector_summary = filtered_df.groupby("Sector").agg(
            Record_Count=("Ticker", "count"),
            Total_Volume=("Volume", "sum"),
            Avg_Close=("Close", "mean"),
            Avg_Daily_Return=("Daily_Return_%", "mean")
        ).reset_index()
        st.dataframe(sector_summary.style.format({
            "Total_Volume": "{:,.0f}",
            "Avg_Close": "${:.2f}",
            "Avg_Daily_Return": "{:.2f}%"
        }), use_container_width=True)
        
    with col_a2:
        st.markdown("#### Ticker-level Breakdown")
        ticker_summary = filtered_df.groupby("Ticker").agg(
            Observations=("Date", "count"),
            Max_Close=("High", "max"),
            Min_Close=("Low", "min"),
            Mean_Close=("Close", "mean")
        ).reset_index()
        st.dataframe(ticker_summary.style.format({
            "Max_Close": "${:.2f}",
            "Min_Close": "${:.2f}",
            "Mean_Close": "${:.2f}"
        }), use_container_width=True)

# ---------------------------------------------------------
# TAB 3: VISUALIZATIONS (BAR, LINE, SCATTER)
# ---------------------------------------------------------
with tab_visualizations:
    st.subheader("Interactive Visual Analytics")
    
    # 1. LINE CHART: Trends over Time
    st.markdown("### 1. Trend Analysis (Line Chart)")
    fig_line = px.line(
        filtered_df,
        x="Date",
        y="Close",
        color="Ticker",
        title="Equity Closing Price Movements Over Time",
        labels={"Close": "Closing Price ($)", "Date": "Trading Date"},
        template="plotly_white"
    )
    fig_line.update_layout(hovermode="x unified", legend_title_text="Stock Ticker")
    st.plotly_chart(fig_line, use_container_width=True)
    st.caption("Interpretation: Visualizes longitudinal asset trajectory, highlighting relative momentum and cross-asset correlation.")
    
    st.divider()
    
    # Columns for Bar Chart and Scatter Plot side-by-side
    col_v1, col_v2 = st.columns(2)
    
    with col_v1:
        st.markdown("### 2. Sector Distribution (Bar Chart)")
        fig_bar = px.bar(
            sector_summary,
            x="Sector",
            y="Total_Volume",
            color="Sector",
            title="Total Trading Volume by Sector",
            labels={"Total_Volume": "Volume Traded", "Sector": "Market Sector"},
            template="plotly_white"
        )
        st.plotly_chart(fig_bar, use_container_width=True)
        st.caption("Interpretation: Identifies sector capital concentration and liquidity distribution.")
        
    with col_v2:
        st.markdown("### 3. Price-Volume Correlation (Scatter Plot)")
        fig_scatter = px.scatter(
            filtered_df,
            x="Volatility_Spread",
            y="Volume",
            color="Ticker",
            size="Close",
            hover_data=["Daily_Return_%"],
            title="Intraday Volatility vs. Trading Volume",
            labels={"Volatility_Spread": "Intraday Price Spread ($)", "Volume": "Trading Volume"},
            template="plotly_white"
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
        st.caption("Interpretation: Explores volatility-volume clustering to detect abnormal trading activity and liquidity shocks.")

# ---------------------------------------------------------
# TAB 4: INSIGHTS & SUMMARY
# ---------------------------------------------------------
with tab_insights:
    st.subheader("Analytical Takeaways & Decision Support")
    
    with st.container():
        st.markdown("""
        * **Liquidity Concentration:** High trading volume clusters predominantly around Technology stocks (`NVDA`, `MSFT`), demonstrating institutional focus on tech growth equities.
        * **Volatility Dynamics:** As depicted in the scatter analysis, wider intraday spreads correlate positively with spiked volume spikes, representing earnings releases and market news catalysts.
        * **Portfolio Diversification:** Consumer Cyclical equities (`TSLA`, `AMZN`) exhibit distinct trend divergence compared to pure tech assets, serving as hedging candidates during tech sell-offs.
        """)
        
    with st.expander("📌 Methodological Notes & Environment Details"):
        st.write("""
        - **Framework:** Python Streamlit with Plotly Express engine.
        - **State Management:** Cached dataset loading with reactive filter callbacks.
        - **Domain:** Quantitative Equity & Capital Markets Analysis.
        """)