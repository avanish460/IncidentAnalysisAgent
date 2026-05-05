#!/usr/bin/env python3
"""
AIrena2.0 Dashboard - Streamlit-based UI for the AI incident analysis agent.

Features:
- Real-time incident analysis
- Validation metrics display
- Incident history visualization
- Alert submission form
"""

import streamlit as st
import requests
import json
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, List, Any

# Configure page
st.set_page_config(
    page_title="AIrena2.0 - AI Incident Analysis",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
    }
    .incident-card {
        border-left: 4px solid #667eea;
        padding: 15px;
        background: #f8f9fa;
        border-radius: 5px;
        margin: 10px 0;
    }
    .severity-p1 { border-left-color: #dc3545; }
    .severity-p2 { border-left-color: #fd7e14; }
    .severity-p3 { border-left-color: #ffc107; }
    .severity-p4 { border-left-color: #28a745; }
    </style>
""", unsafe_allow_html=True)

# API Configuration
API_BASE_URL = st.secrets.get("API_BASE_URL", "http://localhost:8000")

def check_api_health() -> bool:
    """Check if API is running."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def get_metrics() -> Dict[str, Any]:
    """Fetch validation metrics from API."""
    try:
        response = requests.get(f"{API_BASE_URL}/metrics", timeout=10)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return {}

def analyze_incident(alerts: List[Dict], tickets: List[Dict]) -> Dict[str, Any]:
    """Send alerts and tickets to API for analysis."""
    try:
        payload = {
            "alerts": alerts,
            "tickets": tickets
        }
        response = requests.post(
            f"{API_BASE_URL}/analyze",
            json=payload,
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"API Error: {str(e)}")
    return {}

def get_incidents() -> List[Dict]:
    """Fetch recent incidents from database."""
    try:
        response = requests.get(f"{API_BASE_URL}/incidents?limit=10", timeout=10)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return []

# Header
st.markdown("# 🚨 AIrena2.0 - AI Incident Analysis Assistant")
st.markdown("*Intelligent incident detection, correlation, and analysis*")

# Check API status
if not check_api_health():
    st.warning("⚠️ API server is not running. Start it with: `python -m airena2.main --api`")
    st.stop()

# Sidebar
with st.sidebar:
    st.markdown("### Configuration")
    mode = st.radio(
        "Select Mode",
        ["Dashboard", "Analyze Incident", "Validation Metrics"]
    )

# Main content
if mode == "Dashboard":
    # Dashboard Overview
    col1, col2, col3 = st.columns(3)
    
    metrics = get_metrics()
    
    with col1:
        st.metric(
            "Total Feedback Records",
            metrics.get("total_feedback", 0),
            delta=metrics.get("total_feedback", 0)
        )
    
    with col2:
        st.metric(
            "Overall Accuracy",
            f"{metrics.get('overall_accuracy', 0):.1%}",
            delta=f"{metrics.get('overall_accuracy', 0):.1%}"
        )
    
    with col3:
        st.metric(
            "Routing Accuracy",
            f"{metrics.get('routing_accuracy', 0):.1%}",
            delta=f"{metrics.get('routing_accuracy', 0):.1%}"
        )
    
    st.divider()
    
    # Key Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Precision", f"{metrics.get('precision', 0):.2f}")
    with col2:
        st.metric("Recall", f"{metrics.get('recall', 0):.2f}")
    with col3:
        st.metric("False Positive Rate", f"{metrics.get('false_positive_rate', 0):.2f}")
    with col4:
        st.metric("False Negative Rate", f"{metrics.get('false_negative_rate', 0):.2f}")
    
    st.divider()
    
    # Recent Incidents
    st.markdown("### Recent Incidents")
    incidents = get_incidents()
    
    if incidents:
        for incident in incidents[:5]:
            severity = incident.get("severity", "P4")
            severity_class = f"severity-{severity.lower()}"
            
            st.markdown(f"""
            <div class="incident-card {severity_class}">
                <h4>{incident.get('title', 'Unknown')}</h4>
                <p><b>ID:</b> {incident.get('incident_id', 'N/A')} | <b>Severity:</b> {severity} | <b>Classification:</b> {incident.get('classification', 'N/A')}</p>
                <p>{incident.get('summary', 'No summary available')[:200]}...</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No recent incidents found.")

elif mode == "Analyze Incident":
    st.markdown("### Analyze Incident")
    st.markdown("Submit alerts and tickets for analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Alerts")
        num_alerts = st.number_input("Number of alerts", 1, 10, 2)
        
        alerts = []
        for i in range(num_alerts):
            with st.expander(f"Alert {i+1}"):
                alert_id = st.text_input(f"Alert ID", f"A-{i+1001}", key=f"alert_id_{i}")
                alert_source = st.text_input(f"Source", "app-server-1", key=f"alert_source_{i}")
                alert_severity = st.selectbox(f"Severity", ["critical", "high", "warning", "info"], key=f"alert_severity_{i}")
                alert_message = st.text_area(f"Message", "System alert detected", key=f"alert_message_{i}")
                
                alerts.append({
                    "id": alert_id,
                    "source": alert_source,
                    "severity": alert_severity,
                    "message": alert_message,
                    "timestamp": datetime.utcnow().isoformat(),
                    "metadata": {"service": alert_source.split("-")[0]}
                })
    
    with col2:
        st.markdown("#### Tickets")
        num_tickets = st.number_input("Number of tickets", 0, 5, 0)
        
        tickets = []
        for i in range(num_tickets):
            with st.expander(f"Ticket {i+1}"):
                ticket_id = st.text_input(f"Ticket ID", f"T-{i+2001}", key=f"ticket_id_{i}")
                ticket_priority = st.selectbox(f"Priority", ["critical", "high", "medium", "low"], key=f"ticket_priority_{i}")
                ticket_summary = st.text_input(f"Summary", "Production issue", key=f"ticket_summary_{i}")
                ticket_desc = st.text_area(f"Description", "Detailed description", key=f"ticket_desc_{i}")
                
                tickets.append({
                    "id": ticket_id,
                    "system": "ServiceNow",
                    "category": "incident",
                    "priority": ticket_priority,
                    "summary": ticket_summary,
                    "description": ticket_desc,
                    "created_at": datetime.utcnow().isoformat(),
                    "metadata": {"assignee": "ops-team"}
                })
    
    if st.button("🔍 Analyze", use_container_width=True):
        with st.spinner("Analyzing incident..."):
            result = analyze_incident(alerts, tickets)
            
            if result:
                st.success("Analysis complete!")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### Analysis Results")
                    st.markdown(f"**Incident ID:** {result.get('incident_id')}")
                    st.markdown(f"**Title:** {result.get('title')}")
                    st.markdown(f"**Severity:** {result.get('severity')}")
                    st.markdown(f"**Classification:** {result.get('classification')}")
                
                with col2:
                    st.markdown("#### Recommendations")
                    recs = result.get('recommendations', [])
                    for rec in recs:
                        st.markdown(f"- {rec}")
                
                st.markdown("#### Summary")
                st.info(result.get('summary', 'No summary available'))
                
                st.markdown("#### Root Cause Analysis")
                st.warning(result.get('rca', 'No RCA available'))
            else:
                st.error("Failed to analyze incident. Check API connection.")

elif mode == "Validation Metrics":
    st.markdown("### Validation Metrics")
    st.markdown("Phase 4 validation performance metrics")
    
    metrics = get_metrics()
    
    if metrics:
        # Overall metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Feedback",
                metrics.get("total_feedback", 0),
                f"{metrics.get('accurate_predictions', 0)} accurate"
            )
        
        with col2:
            st.metric(
                "Overall Accuracy",
                f"{metrics.get('overall_accuracy', 0):.1%}"
            )
        
        with col3:
            st.metric(
                "Correction Rate",
                f"{metrics.get('correction_rate', 0):.1%}"
            )
        
        with col4:
            st.metric(
                "Last Updated",
                metrics.get('last_updated', 'Unknown')[-10:]
            )
        
        st.divider()
        
        # Detailed metrics
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Classification Metrics")
            st.metric("Precision", f"{metrics.get('precision', 0):.3f}")
            st.metric("Recall", f"{metrics.get('recall', 0):.3f}")
            st.metric("Routing Accuracy", f"{metrics.get('routing_accuracy', 0):.3f}")
        
        with col2:
            st.markdown("#### Error Rates")
            st.metric("False Positive Rate", f"{metrics.get('false_positive_rate', 0):.3f}")
            st.metric("False Negative Rate", f"{metrics.get('false_negative_rate', 0):.3f}")
            st.metric("Severity Misclassifications", metrics.get('severity_misclassifications', 0))
            st.metric("Impact Misclassifications", metrics.get('impact_misclassifications', 0))
        
        st.divider()
        
        # Status assessment
        st.markdown("#### Validation Status")
        accuracy = metrics.get('overall_accuracy', 0)
        
        if accuracy >= 0.8:
            st.success("✅ EXCELLENT - Ready for production rollout")
        elif accuracy >= 0.7:
            st.info("✅ GOOD - Ready for limited production with monitoring")
        elif accuracy >= 0.6:
            st.warning("⚠️ FAIR - Requires additional training data and tuning")
        else:
            st.error("❌ NEEDS_IMPROVEMENT - Additional development required")
    else:
        st.warning("Unable to fetch metrics. Ensure API is running and validation data exists.")

# Footer
st.divider()
st.markdown("""
---
**AIrena2.0 v1.0** | AI-driven incident analysis assistant | Phase 4 - Validation & Rollout

For support: [GitHub](https://github.com) | [Docs](https://github.com)
""")
