import streamlit as st
import json
import google.generativeai as genai
from google.cloud import vision
from google.oauth2 import service_account
import subprocess
from datetime import datetime
from typing import Dict, List
import os

# Initialize session state
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = {}
if 'current_code' not in st.session_state:
    st.session_state.current_code = ""
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'detected_language' not in st.session_state:
    st.session_state.detected_language = "python"  # Default language

# Load credentials correctly from GitHub Secrets
credentials_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")

if credentials_json:
    try:
        credentials_dict = json.loads(credentials_json)
        credentials = service_account.Credentials.from_service_account_info(credentials_dict)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp_credentials.json"
        print("✅ Google Cloud credentials successfully loaded!")
        print("🔍 PROJECT ID:", credentials.project_id)
        print("🔍 CLIENT EMAIL:", credentials.service_account_email)
    except Exception as e:
        print(f"⚠️ Error loading credentials: {str(e)}")
        credentials = None
else:
    print("⚠️ GOOGLE_APPLICATION_CREDENTIALS_JSON is missing!")
    credentials = None

# Test authentication
try:
    client = vision.ImageAnnotatorClient(credentials=credentials)
    print("✅ Successfully connected to Google Cloud Vision API!")
except Exception as e:
    print(f"⚠️ Failed to connect to Vision API: {str(e)}")

# Configure Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
MODEL = genai.GenerativeModel('gemini-pro',
    safety_settings={
        'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE',
        'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE',
        'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE',
        'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_NONE'
    },
    generation_config=genai.types.GenerationConfig(
        max_output_tokens=2000,
        temperature=0.25
    )
)

# AI Assistant Sidebar
def ai_assistant():
    st.sidebar.title("🧠 AI Assistant")
    st.sidebar.write("Ask coding questions or get debugging help!")
    sidebar_query = st.sidebar.text_input("Your question:")
    if sidebar_query:
        response = MODEL.generate_content(sidebar_query)
        st.sidebar.write(response.text if response else "⚠️ No response")
    st.sidebar.markdown("---")
    st.sidebar.info("💡 **Usage Tips**\n"
                    "1. Upload clear code images\n"
                    "2. Review analysis sections\n"
                    "3. Ask follow-up questions\n"
                    "4. Implement suggestions")

# Image Processing
def extract_code_from_image(image) -> str:
    """Extract code from image using Google Vision"""
    if not credentials:
        return "⚠️ Invalid credentials: Check your Google Cloud setup."

    try:
        client = vision.ImageAnnotatorClient(credentials=credentials)
        content = image.read()
        image = vision.Image(content=content)
        response = client.text_detection(image=image)
        
        if response.error.message:
            return f"⚠️ Vision API Error: {response.error.message}"
        
        if response.text_annotations:
            return response.text_annotations[0].description.strip()
        
        return "⚠️ No text detected in image."
    except Exception as e:
        return f"⚠️ OCR Error: {str(e)}"

# Code Analysis Function
def analyze_code(code: str, language: str) -> Dict:
    """Analyze code using Gemini with error handling"""
    try:
        prompt = f"""Analyze this {language} code and provide:
        1. List of bugs with line numbers
        2. Suggested fixes
        3. Corrected code
        4. Performance optimizations
        5. Detailed explanation
        
        Format response as JSON with keys:
        - bugs (list of strings)
        - fixes (list of strings)
        - corrected_code (string)
        - optimizations (list of strings)
        - explanation (list of strings)
        
        Code:\n{code}"""

        response = MODEL.generate_content(prompt)
        
        print("🔍 Debug: API Response:", response.text[:500])  # Print first 500 characters
        
        if not response.text:
            return {"error": "❌ No response from AI model"}
            
        cleaned_response = response.text.replace("```json", "").replace("```", "")
        return json.loads(cleaned_response)
        
    except json.JSONDecodeError:
        return {"error": "❌ Failed to parse AI response"}
    except Exception as e:
        return {"error": f"❌ Analysis failed: {str(e)}"}

# Streamlit UI
st.set_page_config(page_title="AI Code Debugger", layout="wide")
st.title("🛠️ AI-Powered Code Debugger")
st.write("Upload code via image/file or paste directly for analysis")

# Initialize AI Assistant
ai_assistant()

# Analysis Execution
if st.button("🚀 Analyze Code") and st.session_state.current_code.strip():
    with st.spinner("🔍 Analyzing code..."):
        st.session_state.analysis_results = analyze_code(st.session_state.current_code, st.session_state.detected_language)
        st.experimental_rerun()

# Display Analysis Results
if "error" in st.session_state.analysis_results:
    st.error(st.session_state.analysis_results["error"])
else:
    st.subheader("🔍 Analysis Results")
    
    with st.expander("🐛 Identified Bugs", expanded=True):
        for bug in st.session_state.analysis_results.get("bugs", []):
            st.error(f"- {bug}")
    
    with st.expander("🛠️ Suggested Fixes"):
        for fix in st.session_state.analysis_results.get("fixes", []):
            st.info(f"- {fix}")
    
    with st.expander("✅ Corrected Code"):
        st.code(st.session_state.analysis_results.get("corrected_code", ""), language=st.session_state.detected_language)
    
    with st.expander("⚡ Optimizations"):
        for opt in st.session_state.analysis_results.get("optimizations", []):
            st.success(f"- {opt}")
    
    with st.expander("📚 Explanation"):
        for exp in st.session_state.analysis_results.get("explanation", []):
            st.write(f"- {exp}")
