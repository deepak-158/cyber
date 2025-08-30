"""
Streamlit Dashboard for Cyber Threat Detection System
Interactive monitoring and visualization interface
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import json
from datetime import datetime, timedelta
import numpy as np

# Page configuration
st.set_page_config(
    page_title="Cyber Threat Detection Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .alert-high { border-left: 5px solid #ff4444; }
    .alert-medium { border-left: 5px solid #ffaa00; }
    .alert-low { border-left: 5px solid #00aa00; }
    .stSelectbox { margin-bottom: 1rem; }
</style>
""", unsafe_allow_html=True)

# Backend API URL
# BACKEND_URL = "http://backend:8000"  # Docker internal URL
BACKEND_URL = "http://localhost:8000"  # Local development

def make_api_request(endpoint, params=None):
    """Make API request with error handling"""
    try:
        response = requests.get(f"{BACKEND_URL}{endpoint}", params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Connection Error: {str(e)}")
        return generate_mock_data(endpoint)

def generate_mock_data(endpoint):
    """Generate mock data for development/demo"""
    if endpoint == "/api/v1/stats/dashboard":
        return {
            "summary": {
                "total_campaigns": 15,
                "active_alerts": 7,
                "total_posts": 12847,
                "high_risk_campaigns": 3
            },
            "recent_high_risk": [
                {"id": "1", "name": "Economic Doom Campaign", "score": 87.5, "detected_at": "2024-08-30T14:30:00Z"},
                {"id": "2", "name": "Kashmir Misinformation", "score": 78.2, "detected_at": "2024-08-30T12:15:00Z"},
                {"id": "3", "name": "Bot Network Alpha", "score": 71.8, "detected_at": "2024-08-30T09:45:00Z"}
            ]
        }
    elif endpoint == "/api/v1/alerts":
        return {
            "alerts": [
                {"id": "1", "title": "High Coordination Detected", "severity": "high", "created_at": "2024-08-30T16:30:00Z", "is_active": True},
                {"id": "2", "title": "Bot Network Activity", "severity": "medium", "created_at": "2024-08-30T15:20:00Z", "is_active": True},
                {"id": "3", "title": "Burst Activity Anomaly", "severity": "medium", "created_at": "2024-08-30T14:10:00Z", "is_active": True}
            ]
        }
    elif endpoint == "/api/v1/campaigns":
        return {
            "campaigns": [
                {"id": "1", "name": "Economic Doom Campaign", "campaign_score": 87.5, "status": "detected", "total_posts": 245},
                {"id": "2", "name": "Kashmir Misinformation", "campaign_score": 78.2, "status": "investigating", "total_posts": 189},
                {"id": "3", "name": "Bot Network Alpha", "campaign_score": 71.8, "status": "confirmed", "total_posts": 567}
            ]
        }
    return {}

def main():
    """Main dashboard function"""
    
    # Header
    st.markdown("# 🛡️ Cyber Threat Detection Dashboard")
    st.markdown("### Real-time monitoring of coordinated influence campaigns")
    
    # Sidebar
    with st.sidebar:
        st.markdown("## 🔧 Controls")
        
        # Auto-refresh toggle
        auto_refresh = st.checkbox("Auto-refresh (30s)", value=False)
        
        # Time range filter
        time_range = st.selectbox(
            "Time Range",
            ["Last 24 hours", "Last 7 days", "Last 30 days", "All time"],
            index=0
        )
        
        # Severity filter
        severity_filter = st.multiselect(
            "Alert Severity",
            ["critical", "high", "medium", "low"],
            default=["critical", "high", "medium"]
        )
        
        # Refresh button
        if st.button("🔄 Refresh Data") or auto_refresh:
            st.rerun()
    
    # Main content
    try:
        # Dashboard statistics
        stats_data = make_api_request("/api/v1/stats/dashboard")
        
        if stats_data:
            # Key metrics row
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Active Campaigns",
                    stats_data["summary"]["total_campaigns"],
                    delta=2,
                    delta_color="inverse"
                )
            
            with col2:
                st.metric(
                    "Active Alerts",
                    stats_data["summary"]["active_alerts"],
                    delta=-1,
                    delta_color="normal"
                )
            
            with col3:
                st.metric(
                    "Posts Analyzed",
                    f"{stats_data['summary']['total_posts']:,}",
                    delta=847,
                    delta_color="normal"
                )
            
            with col4:
                st.metric(
                    "High Risk Campaigns",
                    stats_data["summary"]["high_risk_campaigns"],
                    delta=1,
                    delta_color="inverse"
                )
        
        # Two-column layout
        left_col, right_col = st.columns([2, 1])
        
        with left_col:
            # Campaign analysis chart
            st.markdown("### 📊 Campaign Risk Analysis")
            
            campaigns_data = make_api_request("/api/v1/campaigns")
            if campaigns_data and campaigns_data.get("campaigns"):
                df_campaigns = pd.DataFrame(campaigns_data["campaigns"])
                
                # Risk distribution pie chart
                fig_pie = px.pie(
                    values=[
                        len(df_campaigns[df_campaigns["campaign_score"] >= 80]),
                        len(df_campaigns[(df_campaigns["campaign_score"] >= 60) & (df_campaigns["campaign_score"] < 80)]),
                        len(df_campaigns[df_campaigns["campaign_score"] < 60])
                    ],
                    names=["High Risk (80+)", "Medium Risk (60-79)", "Low Risk (<60)"],
                    color_discrete_sequence=["#ff4444", "#ffaa00", "#00aa00"],
                    title="Campaign Risk Distribution"
                )
                st.plotly_chart(fig_pie, use_container_width=True)
                
                # Campaign scores over time (mock time series)
                dates = pd.date_range(start="2024-08-25", end="2024-08-30", freq="D")
                scores_data = {
                    "Date": dates,
                    "High Risk": [2, 1, 3, 2, 3, 3],
                    "Medium Risk": [1, 2, 1, 3, 2, 1],
                    "Low Risk": [0, 1, 0, 1, 1, 2]
                }
                
                fig_trend = px.line(
                    pd.DataFrame(scores_data),
                    x="Date",
                    y=["High Risk", "Medium Risk", "Low Risk"],
                    title="Campaign Detection Trends",
                    color_discrete_map={
                        "High Risk": "#ff4444",
                        "Medium Risk": "#ffaa00", 
                        "Low Risk": "#00aa00"
                    }
                )
                st.plotly_chart(fig_trend, use_container_width=True)
        
        with right_col:
            # Active alerts
            st.markdown("### 🚨 Active Alerts")
            
            alerts_data = make_api_request("/api/v1/alerts", {"active_only": True})
            if alerts_data and alerts_data.get("alerts"):
                for alert in alerts_data["alerts"][:5]:
                    severity_class = f"alert-{alert['severity']}"
                    
                    with st.container():
                        st.markdown(f"""
                        <div class="metric-card {severity_class}">
                            <strong>{alert['title']}</strong><br>
                            <small>Severity: {alert['severity'].upper()}</small><br>
                            <small>{alert['created_at'][:16]}</small>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("No active alerts")
        
        # Detailed analysis tabs
        st.markdown("---")
        
        tab1, tab2, tab3, tab4 = st.tabs(["📋 Campaigns", "🤖 Bot Networks", "📈 Analytics", "⚙️ Analysis Tools"])
        
        with tab1:
            st.markdown("### Campaign Details")
            
            if campaigns_data and campaigns_data.get("campaigns"):
                df_campaigns = pd.DataFrame(campaigns_data["campaigns"])
                
                # Campaign table
                st.dataframe(
                    df_campaigns[["name", "campaign_score", "status", "total_posts"]],
                    column_config={
                        "name": "Campaign Name",
                        "campaign_score": st.column_config.ProgressColumn(
                            "Risk Score",
                            help="Campaign risk score (0-100)",
                            min_value=0,
                            max_value=100
                        ),
                        "status": "Status",
                        "total_posts": "Posts"
                    },
                    use_container_width=True
                )
                
                # Campaign details
                if st.button("View Selected Campaign Details"):
                    selected_campaign = st.selectbox("Select Campaign", df_campaigns["name"])
                    if selected_campaign:
                        campaign_row = df_campaigns[df_campaigns["name"] == selected_campaign].iloc[0]
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Risk Score:** {campaign_row['campaign_score']}")
                            st.write(f"**Status:** {campaign_row['status']}")
                        with col2:
                            st.write(f"**Total Posts:** {campaign_row['total_posts']}")
                            st.write(f"**Campaign ID:** {campaign_row['id']}")
        
        with tab2:
            st.markdown("### Bot Network Analysis")
            
            # Mock bot network data
            bot_data = {
                "Network": ["Network Alpha", "Network Beta", "Network Gamma"],
                "Accounts": [23, 15, 8],
                "Activity Score": [87, 72, 45],
                "Status": ["Active", "Monitoring", "Inactive"]
            }
            
            df_bots = pd.DataFrame(bot_data)
            st.dataframe(df_bots, use_container_width=True)
            
            # Bot activity visualization
            fig_bot = px.scatter(
                df_bots,
                x="Accounts",
                y="Activity Score",
                size="Accounts",
                color="Status",
                hover_name="Network",
                title="Bot Network Activity vs Size"
            )
            st.plotly_chart(fig_bot, use_container_width=True)
        
        with tab3:
            st.markdown("### Advanced Analytics")
            
            # Network graph placeholder
            st.markdown("#### Coordination Network Graph")
            st.info("Interactive network visualization would be displayed here showing coordination patterns between accounts")
            
            # Temporal analysis
            st.markdown("#### Temporal Activity Patterns")
            
            # Mock hourly activity data
            hours = list(range(24))
            activity = [5, 3, 2, 1, 1, 2, 8, 15, 25, 30, 35, 40, 45, 50, 48, 42, 38, 35, 28, 22, 18, 12, 8, 6]
            
            fig_temporal = px.bar(
                x=hours,
                y=activity,
                labels={"x": "Hour of Day", "y": "Post Activity"},
                title="24-Hour Activity Pattern"
            )
            st.plotly_chart(fig_temporal, use_container_width=True)
        
        with tab4:
            st.markdown("### Text Analysis Tools")
            
            # Single text analysis
            st.markdown("#### Analyze Text Content")
            
            text_input = st.text_area(
                "Enter text to analyze:",
                placeholder="Paste social media content here for threat analysis...",
                height=100
            )
            
            if st.button("🔍 Analyze Text"):
                if text_input:
                    with st.spinner("Analyzing content..."):
                        # Mock analysis result
                        analysis_result = {
                            "toxicity_score": 0.75,
                            "stance_score": -0.82,
                            "language": "English",
                            "risk_level": "High",
                            "indicators": ["High toxicity", "Anti-India stance", "Coordinated language patterns"]
                        }
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.metric("Toxicity Score", f"{analysis_result['toxicity_score']:.2f}")
                            st.metric("Stance Score", f"{analysis_result['stance_score']:.2f}")
                        
                        with col2:
                            st.metric("Language", analysis_result['language'])
                            st.metric("Risk Level", analysis_result['risk_level'])
                        
                        st.markdown("**Risk Indicators:**")
                        for indicator in analysis_result['indicators']:
                            st.write(f"- {indicator}")
                else:
                    st.warning("Please enter text to analyze")
            
            # Bulk analysis
            st.markdown("#### Bulk Analysis")
            
            uploaded_file = st.file_uploader(
                "Upload CSV file with posts",
                type=["csv"],
                help="CSV should have 'text_content' column"
            )
            
            if uploaded_file and st.button("🔄 Process File"):
                with st.spinner("Processing file..."):
                    # Mock file processing
                    st.success("File processed successfully!")
                    st.info("Results would be displayed here with downloadable report")
    
    except Exception as e:
        st.error(f"Dashboard Error: {str(e)}")
        st.info("Some features may not be available. Please check the backend connection.")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "🛡️ **Cyber Threat Detection System** | "
        "Built with ❤️ for cybersecurity research | "
        f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    # Auto-refresh logic
    if auto_refresh:
        import time
        time.sleep(30)
        st.rerun()

if __name__ == "__main__":
    main()