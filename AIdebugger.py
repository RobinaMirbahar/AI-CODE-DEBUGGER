import streamlit as st
import json
import os
import re
import google.generativeai as genai
from google.cloud import vision
from google.oauth2 import service_account

# Set page config FIRST
st.set_page_config(page_title="AI Code Debugger", layout="wide")

# ========== SIDEBAR (STATIC CONTENT) ==========
with st.sidebar:
    st.title("🧠 AI Assistant")
    st.markdown("---")
    
    # Display chat history
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    st.markdown("---")
    st.subheader("💡 Usage Tips")
    st.markdown("""
    1. Upload clear code images
    2. Review analysis sections
    3. Ask follow-up questions
    4. Implement suggestions
    """)

# ========== MAIN APP (DYNAMIC CONTENT) ==========
# Chat input should be in main area
user_query = st.chat_input("Ask coding questions...")

# Rest of your existing code for credentials initialization, 
# analysis functions, and main interface components...
# [Keep all other code the same except the chat input placement]

# Handle chat after main content
if user_query and 'MODEL' in globals():
    try:
        st.session_state.chat_history.append({"role": "user", "content": user_query})
        response = MODEL.generate_content(user_query)
        if response.text:
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": response.text
            })
            st.rerun()
    except Exception as e:
        st.sidebar.error(f"Chat error: {str(e)}")
