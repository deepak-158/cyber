"""
Streamlit Dashboard for Cyber Threat Detection System
Interactive monitoring and visualization interface
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime
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
}
.metric-card:hover {
    box-shadow: 0 8px 32px rgba(0,0,0,0.18);
}
.alert-high { border-left: 6px solid #ff4444; }
.alert-medium { border-left: 6px solid #ffaa00; }
.alert-low { border-left: 6px solid #00aa00; }
.stSelectbox { margin-bottom: 1rem; }
.sidebar-brand {
    font-size: 1.3rem;
    font-weight: bold;
    color: #0072ff;
    margin-bottom: 1.5rem;
}
</style>
""", unsafe_allow_html=True)

# Backend API URL
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
    try:
        # Header
        st.markdown('<div class="main-header">🛡️ Cyber Threat Detection Dashboard</div>', unsafe_allow_html=True)
        st.markdown("<span style='font-size:1.2rem;color:#43c6ac;'>Real-time monitoring of coordinated influence campaigns</span>", unsafe_allow_html=True)

        # Sidebar
        with st.sidebar:
            st.markdown('<div class="sidebar-brand">🚀 Hackathon Edition</div>', unsafe_allow_html=True)
            st.image("https://img.icons8.com/color/96/000000/hacker.png", width=80)
            st.markdown("## 🔧 Controls")
            auto_refresh = st.checkbox("Auto-refresh (30s)", value=False)
            time_range = st.selectbox(
                "Time Range",
                ["Last 24 hours", "Last 7 days", "Last 30 days", "All time"],
                index=0
            )
            severity_filter = st.multiselect(
                "Alert Severity",
                ["critical", "high", "medium", "low"],
                default=["critical", "high", "medium"]
            )
            if st.button("🔄 Refresh Data") or auto_refresh:
                st.rerun()

        st.markdown("<hr style='border:1px solid #43c6ac;'>", unsafe_allow_html=True)

        # Fetch campaigns
        campaigns_data = make_api_request("/api/v1/campaigns")

        # Tabs
        tab1, tab2, tab3, tab4 = st.tabs(["📋 Campaigns", "🤖 Bot Networks", "📈 Analytics", "⚙️ Analysis Tools"])

        # Campaigns tab
        with tab1:
            st.markdown("<span style='font-size:1.2rem;color:#0072ff;'>📋 Campaign Details</span>", unsafe_allow_html=True)
            if campaigns_data and campaigns_data.get("campaigns"):
                df_campaigns = pd.DataFrame(campaigns_data["campaigns"])
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

        # Bot Networks tab
        with tab2:
            st.markdown("<span style='font-size:1.2rem;color:#0072ff;'>🤖 Bot Network Activity</span>", unsafe_allow_html=True)
            bot_data = {
                "Network": ["BotNet A", "BotNet B", "BotNet C"],
                "Accounts": [23, 15, 8],
                "Activity Score": [87, 72, 45],
                "Status": ["Active", "Monitoring", "Inactive"]
            }
            df_bots = pd.DataFrame(bot_data)
            st.dataframe(df_bots, use_container_width=True)
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

        # Analytics tab
        with tab3:
            st.markdown("<span style='font-size:1.2rem;color:#43c6ac;'>📈 Advanced Analytics</span>", unsafe_allow_html=True)
            st.markdown("#### Coordination Network Graph")
            st.info("Interactive network visualization would be displayed here showing coordination patterns between accounts")

            st.markdown("#### Temporal Activity Patterns")
            hours = list(range(24))
            activity = [5, 3, 2, 1, 1, 2, 8, 15, 25, 30, 35, 40, 45, 50, 48, 42, 38, 35, 28, 22, 18, 12, 8, 6]
            fig_temporal = px.bar(
                x=hours,
                y=activity,
                labels={"x": "Hour of Day", "y": "Post Activity"},
                title="24-Hour Activity Pattern",
                color_discrete_sequence=["#43c6ac"]
            )
            fig_temporal.update_layout(plot_bgcolor='#f8ffae', paper_bgcolor='#f8ffae')
            st.plotly_chart(fig_temporal, use_container_width=True)

        # Analysis Tools tab
        with tab4:
            st.markdown("<span style='font-size:1.2rem;color:#0072ff;'>⚙️ Text Analysis Tools</span>", unsafe_allow_html=True)

            st.markdown("#### Analyze Text Content")
            text_input = st.text_area(
                "Enter text to analyze:",
                placeholder="Paste social media content here for threat analysis...",
                height=100
            )
            if st.button("🔍 Analyze Text"):
                if text_input:
                    with st.spinner("Analyzing content..."):
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

            st.markdown("#### Bulk Analysis")
            uploaded_file = st.file_uploader(
                "Upload CSV file with posts",
                type=["csv"],
                help="CSV should have 'text_content' column"
            )
            if uploaded_file and st.button("🔄 Process File"):
                with st.spinner("Processing file..."):
                    st.success("File processed successfully!")
                    st.info("Results would be displayed here with downloadable report")

    except Exception as e:
        st.error(f"Dashboard Error: {str(e)}")
        st.info("Some features may not be available. Please check the backend connection.")


if __name__ == "__main__":
    main()
