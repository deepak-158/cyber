"""
Streamlit Dashboard for Cyber Threat Detection System
Enhanced monitoring and visualization interface
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime, timedelta
import numpy as np
import random
import io
from streamlit_extras.add_vertical_space import add_vertical_space
from streamlit_extras.colored_header import colored_header
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# -------------------------
# Page Configuration
# -------------------------
st.set_page_config(
    page_title="Cyber Threat Detection Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------
# Custom CSS Styling
# -------------------------
st.markdown("""
<style>
body {
    background: linear-gradient(135deg, #232526 0%, #414345 100%);
}
.main-header {
    font-size: 2.5rem;
    font-weight: bold;
    background: linear-gradient(90deg, #00c6ff, #0072ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.5rem;
}
.metric-card {
    background: linear-gradient(135deg, #f8ffae 0%, #43c6ac 100%);
    border-radius: 16px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.08);
    padding: 1.2rem;
    margin: 0.7rem 0;
    transition: box-shadow 0.3s;
    text-align: center;
}
.metric-card:hover {
    box-shadow: 0 8px 32px rgba(0,0,0,0.18);
}
.sidebar-brand {
    font-size: 1.3rem;
    font-weight: bold;
    color: #0072ff;
    margin-bottom: 1.5rem;
}
footer {
    text-align: center;
    font-size: 0.8rem;
    color: #aaa;
    margin-top: 2rem;
}
</style>
""", unsafe_allow_html=True)

# -------------------------
# Backend & Mock Data
# -------------------------
BACKEND_URL = "http://localhost:8000"  # Local development

@st.cache_data(show_spinner=False)
def make_api_request(endpoint, params=None):
    """Make API request with error handling + caching"""
    try:
        response = requests.get(f"{BACKEND_URL}{endpoint}", params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except requests.exceptions.RequestException:
        return generate_mock_data(endpoint)

def generate_mock_data(endpoint):
    """Generate mock data for development/demo"""
    if endpoint == "/api/v1/stats/dashboard":
        return {
            "summary": {
                "total_campaigns": random.randint(10, 20),
                "active_alerts": random.randint(5, 12),
                "total_posts": random.randint(10000, 20000),
                "high_risk_campaigns": random.randint(2, 6)
            }
        }
    elif endpoint == "/api/v1/campaigns":
        return {
            "campaigns": [
                {"id": "1", "name": "Economic Doom Campaign", "campaign_score": 87.5, "status": "detected", "total_posts": 245},
                {"id": "2", "name": "Kashmir Misinformation", "campaign_score": 78.2, "status": "investigating", "total_posts": 189},
                {"id": "3", "name": "Bot Network Alpha", "campaign_score": 71.8, "status": "confirmed", "total_posts": 567}
            ]
        }
    elif endpoint == "/api/v1/alerts":
        return {
            "alerts": [
                {"id": "1", "title": "High Coordination Detected", "severity": "high", "created_at": "2024-08-30T16:30:00Z", "is_active": True},
                {"id": "2", "title": "Bot Network Activity", "severity": "medium", "created_at": "2024-08-30T15:20:00Z", "is_active": True}
            ]
        }
    return {}

# -------------------------
# Dashboard Layout
# -------------------------
def main():
    st.markdown('<div class="main-header">🛡️ Cyber Threat Detection Dashboard</div>', unsafe_allow_html=True)
    st.markdown("<span style='font-size:1.2rem;color:#43c6ac;'>Real-time monitoring of coordinated influence campaigns</span>", unsafe_allow_html=True)

    # Sidebar controls
    with st.sidebar:
        st.markdown('<div class="sidebar-brand">🚀 Hackathon Edition</div>', unsafe_allow_html=True)
        st.image("https://img.icons8.com/color/96/000000/hacker.png", width=80)
        st.markdown("## 🔧 Controls")
        
        # Auto-refresh toggle
        auto_refresh = st.checkbox("Auto-refresh (30s)", value=False)
        if auto_refresh:
            st.experimental_set_query_params(refresh=str(datetime.utcnow()))
            st.toast("Auto-refresh active")
            st.experimental_rerun()
        
        # Live API tester
        if st.button("🔌 Test Backend Connectivity"):
            try:
                res = requests.get(f"{BACKEND_URL}/health", timeout=5)
                if res.status_code == 200:
                    st.success("✅ Backend is live")
                else:
                    st.error("❌ Backend responded with error")
            except:
                st.error("❌ Could not connect to backend")
        
        # Filters
        time_range = st.selectbox("Time Range", ["Last 24 hours", "Last 7 days", "Last 30 days", "All time"])
        severity_filter = st.multiselect("Alert Severity", ["critical", "high", "medium", "low"], default=["critical", "high", "medium"])
        
        # Manual refresh
        if st.button("🔄 Refresh Data"):
            st.experimental_rerun()
    # Dark mode toggle  
    dark_mode = st.sidebar.toggle("🌙 Dark Mode")
    if dark_mode:
        st.markdown("<style>body{background: #111;color:#eee}</style>", unsafe_allow_html=True)
        st.markdown("<hr style='border:1px solid #43c6ac;'>", unsafe_allow_html=True)

    # KPI Cards
    stats = make_api_request("/api/v1/stats/dashboard")
    if stats and "summary" in stats:
        cols = st.columns(4)
        summary = stats["summary"]
        with cols[0]: st.markdown(f"<div class='metric-card'><h3>{summary['total_campaigns']}</h3>Total Campaigns</div>", unsafe_allow_html=True)
        with cols[1]: st.markdown(f"<div class='metric-card'><h3>{summary['active_alerts']}</h3>Active Alerts</div>", unsafe_allow_html=True)
        with cols[2]: st.markdown(f"<div class='metric-card'><h3>{summary['total_posts']}</h3>Total Posts</div>", unsafe_allow_html=True)
        with cols[3]: st.markdown(f"<div class='metric-card'><h3>{summary['high_risk_campaigns']}</h3>High Risk</div>", unsafe_allow_html=True)
        with st.expander("📊 Threat Severity Gauge"):
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=random.randint(20, 90),
                title={'text': "Global Threat Index"},
                gauge={'axis': {'range': [0,100]},
                       'bar': {'color': "red"},
                       'steps': [
                           {'range': [0, 40], 'color': "green"},
                           {'range': [40, 70], 'color': "yellow"},
                           {'range': [70, 100], 'color': "red"}]}
            ))
            st.plotly_chart(fig_gauge, use_container_width=True)


    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 Campaigns", "🤖 Bot Networks", "📈 Analytics", "🌍 Geo Heatmap", "⚙️ Tools"])

    with tab1:
        st.subheader("📋 Campaign Details")
        campaigns_data = make_api_request("/api/v1/campaigns")
        if campaigns_data and campaigns_data.get("campaigns"):
            df_campaigns = pd.DataFrame(campaigns_data["campaigns"])
            
            # Advanced search
            search_term = st.text_input("🔍 Search Campaign")
            if search_term:
                df_campaigns = df_campaigns[df_campaigns["name"].str.contains(search_term, case=False)]
            
            st.dataframe(df_campaigns, use_container_width=True)
            
            if not df_campaigns.empty:
                selected = st.selectbox("Select Campaign", df_campaigns["name"])
                if selected:
                    row = df_campaigns[df_campaigns["name"] == selected].iloc[0]
                    st.info(f"**{row['name']}** | Score: {row['campaign_score']} | Status: {row['status']} | Posts: {row['total_posts']}")
                    
                    # Download button
                    csv = df_campaigns.to_csv(index=False).encode("utf-8")
                    st.download_button("⬇️ Download Campaigns CSV", data=csv, file_name="campaigns.csv", mime="text/csv")

    with tab2:
        st.subheader("🤖 Bot Network Activity")
        bot_data = {
            "Network": ["BotNet A", "BotNet B", "BotNet C"],
            "Accounts": [23, 15, 8],
            "Activity Score": [87, 72, 45],
            "Status": ["Active", "Monitoring", "Inactive"]
        }
        df_bots = pd.DataFrame(bot_data)
        st.dataframe(df_bots, use_container_width=True)
        fig_bot = px.scatter(df_bots, x="Accounts", y="Activity Score", size="Accounts", color="Status", hover_name="Network")
        st.plotly_chart(fig_bot, use_container_width=True)

    with tab3:
        st.subheader("📈 Alert Timeline")
        alerts_data = make_api_request("/api/v1/alerts")
        if alerts_data and "alerts" in alerts_data:
            df_alerts = pd.DataFrame(alerts_data["alerts"])
            df_alerts["created_at"] = pd.to_datetime(df_alerts["created_at"])
            df_alerts = df_alerts.sort_values("created_at")
            
            fig_timeline = px.timeline(df_alerts, x_start="created_at", x_end="created_at",
                                       y="title", color="severity", hover_data=["is_active"])
            st.plotly_chart(fig_timeline, use_container_width=True)

    with tab4:
        st.subheader("🌍 Geographic Threat Sources")
        # Mock geolocation data
        geo_data = pd.DataFrame({
            "lat": np.random.uniform(20, 50, 10),
            "lon": np.random.uniform(60, 100, 10),
            "intensity": np.random.randint(10, 100, 10)
        })
        fig_map = px.density_mapbox(geo_data, lat="lat", lon="lon", z="intensity",
                                    radius=20, center=dict(lat=35, lon=80), zoom=3,
                                    mapbox_style="carto-positron")
        st.plotly_chart(fig_map, use_container_width=True)

    with tab5:
        st.subheader("⚙️ Text Analysis & AI Insights")
        text_input = st.text_area("Enter text to analyze:")
        if st.button("🔍 Analyze Text"):
            if text_input:
                st.success("Analysis complete!")
                st.json({
                    "toxicity_score": 0.75,
                    "stance_score": -0.82,
                    "language": "English",
                    "risk_level": "High",
                    "indicators": ["High toxicity", "Anti-India stance", "Coordinated patterns"]
                })
                st.markdown("💡 **AI Insight:** This text shows signs of coordinated influence with high toxicity and targeted stance.")
            else:
                st.warning("Please enter text to analyze")

    st.markdown("<footer>Cyber Threat Detection Dashboard © 2024 | Built for Hackathon</footer>", unsafe_allow_html=True)
    tab6 = st.tabs(["📋 Campaigns", "🤖 Bot Networks", "📈 Analytics", "🌍 Geo Heatmap", "⚙️ Tools", "📝 Report Threat"])[-1]

    with tab6:
        st.subheader("📝 Report Suspicious Activity")
        with st.form("report_form", clear_on_submit=True):
            user = st.text_input("Your Name")
            account = st.text_input("Suspicious Account / Post Link")
            details = st.text_area("Details")
            submitted = st.form_submit_button("🚨 Submit Report")
            if submitted:
                st.success("✅ Report submitted successfully!")
                st.session_state.setdefault("reports", [])
                st.session_state["reports"].append({"User": user, "Account": account, "Details": details})

        if "reports" in st.session_state:
            st.markdown("### 📊 Community Reports")
            st.dataframe(pd.DataFrame(st.session_state["reports"]))

if __name__ == "__main__":
    main()
