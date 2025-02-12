import streamlit as st
import os
import json

# Check if secrets exist
try:
    st.write("🔍 Checking Streamlit Secrets...")

    # Check GEMINI_API_KEY
    gemini_api_key = st.secrets["GEMINI_API_KEY"]
    st.success(f"✅ GEMINI_API_KEY Loaded: {gemini_api_key[:10]}...")

    # Check Google Cloud credentials
    credentials_info = st.secrets["gcp_service_account"]
    st.success(f"✅ Google Cloud Project: {credentials_info['project_id']}")

except Exception as e:
    st.error(f"❌ ERROR: {str(e)}")
