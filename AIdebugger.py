import streamlit as st
import json
import google.generativeai as genai
from google.cloud import vision
from google.oauth2 import service_account
import os

# --- MUST BE FIRST STREAMLIT COMMAND ---
st.set_page_config(page_title="AI Code Debugger", layout="wide")

# --- Load Credentials ---
try:
    # ✅ Load Google API Key from Secrets
    GOOGLE_API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=GOOGLE_API_KEY)

    # ✅ Load Google Cloud Credentials
    credentials_info = st.secrets["gcp_service_account"]
    CREDENTIALS = service_account.Credentials.from_service_account_info(credentials_info)

    st.success(f"✅ Credentials Loaded for Google Cloud Project: {credentials_info['project_id']}")

except KeyError as e:
    st.error(f"❌ Missing Secret: {e} - Please check Streamlit secrets")
    st.stop()
except Exception as e:
    st.error(f"❌ Credential Load Error: {str(e)}")
    st.stop()
