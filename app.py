import streamlit as st
import json
import pandas as pd
import time
import os
from datetime import datetime

# --- CONFIG & STYLING ---
st.set_page_config(page_title="Skelar AI Operations", layout="wide")

# Custom CSS to mimic a professional support desk
st.markdown("""
    <style>
    .agent-reply { background-color: #f0f2f6; padding: 10px; border-radius: 10px; margin: 5px 0; }
    .customer-msg { background-color: #e1f5fe; padding: 10px; border-radius: 10px; margin: 5px 0; text-align: right; }
    .stButton>button { width: 100%; border-radius: 5px; }
    .risk-high { color: #ff4b4b; font-weight: bold; }
    .risk-low { color: #2ecc71; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA LOADING HELPERS ---
def load_json(path, default=[]):
    # Using os.path.join to handle relative paths safely
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error loading {path}: {e}")
            return default
    return default

# Relative paths (assuming app.py is in the root of your hackaton-skelar folder)
dataset = load_json("data/dataset_clean.json")
copilot_results = load_json("copilot_results.json")
audit_data = load_json("detailed_operational_audit.json")
kb_data = load_json("potential_kb_articles.json")

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("SKELAR AI")
page = st.sidebar.radio("Navigate to:", ["Agent Workspace (Copilot)", "Supervisor Dashboard", "Knowledge Base"])

# --- PAGE 1: AGENT WORKSPACE ---
if page == "Agent Workspace (Copilot)":
    st.title(" Agent Copilot Workspace")
    
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Active Conversation")
        if not dataset:
            st.warning("No chat data found. Please run your generation scripts first.")
        else:
            chat_ids = [c['id'] for c in dataset]
            selected_id = st.selectbox("Select Incoming Ticket:", chat_ids)
            current_chat = next(c for c in dataset if c['id'] == selected_id)

            chat_container = st.container(height=400, border=True)
            for msg in current_chat['messages']:
                div_class = "customer-msg" if msg['role'] == "customer" else "agent-reply"
                chat_container.markdown(f"<div class='{div_class}'><b>{msg['role'].upper()}:</b> {msg['text']}</div>", unsafe_allow_html=True)

            st.text_area("Your Response", placeholder="Type your message here...", height=100)
            c_btn1, c_btn2 = st.columns(2)
            if c_btn1.button("Send Message", type="primary"):
                st.success("Message sent!")
            c_btn2.button("Internal Note")

    with col2:
        st.subheader(" AI Insights")
        analysis = next((item for item in copilot_results if item['chat_id'] == selected_id), None)
        
        if analysis:
            with st.expander("Analysis & Intent", expanded=True):
                st.write(f"**Intent:** {analysis.get('intent', 'N/A')}")
                st.write(f"**Confidence:** {analysis.get('confidence', '0%')}")
                risk = analysis.get('risk_level', 'low').lower()
                
                # FIXED: Moved logic outside the f-string to avoid quote errors
                risk_class = "risk-high" if risk == "high" else "risk-low"
                st.markdown(f"**Risk Level:** <span class='{risk_class}'>{risk.upper()}</span>", unsafe_allow_html=True)

            st.subheader("Suggested Actions")
            suggested_action = analysis.get('suggested_action', "General Support")
            
            if st.button(f"⚡ Execute: {suggested_action}"):
                with st.status(f"Running {suggested_action} workflow..."):
                    time.sleep(1)
                    st.write("Accessing Database...")
                    time.sleep(1)
                    st.write("Processing Action...")
                st.success(f"Action '{suggested_action}' completed!")
                st.balloons()

            with st.expander("Draft AI Reply"):
                st.info(analysis.get('suggested_reply', "No draft available."))
                if st.button("Copy to Editor"):
                    st.toast("Draft copied!")

# --- PAGE 2: SUPERVISOR DASHBOARD ---
elif page == "Supervisor Dashboard":
    st.title(" Operational Health Dashboard")
    
    if not audit_data:
        st.error("Audit data missing. Run your audit script to generate metrics.")
    else:
        df = pd.DataFrame([
            {
                "ID": i["chat_id"],
                "Customer": i["customer_name"],
                "Priority": i["prioritization"]["level"],
                "Risk": i["copilot_analysis"]["risk_level"],
                "Automation": i["system_execution"]["status"]
            } for i in audit_data
        ])

        m1, m2, m3 = st.columns(3)
        m1.metric("Total Tickets", len(df))
        m2.metric("High Risk Alerts", len(df[df['Risk'] == 'high']))
        m3.metric("Auto-Resolved", len(df[df['Automation'].str.contains("Executed", na=False)]))

        st.divider()
        col_left, col_right = st.columns(2)
        with col_left:
            st.subheader("Priority Distribution")
            st.bar_chart(df['Priority'].value_counts())
        with col_right:
            st.subheader("High Risk Tickets")
            st.table(df[df['Risk'] == 'high'].head(5))

# --- PAGE 3: KNOWLEDGE BASE ---
elif page == "Knowledge Base":
    st.title(" Self-Learning Knowledge Base")
    st.write("Workflows extracted from high-quality human resolutions.")

    if not kb_data:
        st.info("No KB articles generated yet.")
    else:
        for i, article in enumerate(kb_data):
            with st.container(border=True):
                st.markdown(f"### Intent: {article.get('intent')}")
                st.write(f"**Status:** {article.get('status')}")
                st.write("**Resolution Steps:**")
                for step in article.get('resolution_steps', []):
                    st.markdown(f"- {step}")
                if st.button("Approve for Automation", key=f"btn_{i}"):
                    st.success("Workflow Approved!")

# --- FOOTER ---
st.sidebar.divider()
# FIXED: Removed st.experimental_user and replaced with a static string
st.sidebar.caption("Skelar Hackathon 2026 | Agent: Sofiia Mikhailova")