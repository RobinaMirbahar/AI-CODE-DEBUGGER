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
        max_output_tokens=4000,
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

# Code Analysis Functions
def analyze_code(code_snippet: str, language: str = "python") -> Dict:
    """Perform code analysis with error handling"""
    if not code_snippet.strip():
        return {"error": "⚠️ No code provided"}

    prompt = f"""Analyze this {language} code and provide:
    ```{language}
    {code_snippet}
    ```
    Format response as:
    ### BUGS
    - [List line-specific issues]
    ### FIXES
    - [Step-by-step solutions]
    ### CORRECTED_CODE
    ```{language}
    [Corrected code]
    ```
    ### OPTIMIZATIONS
    - [Performance improvements]
    ### EXPLANATION
    - [Technical rationale]
    """
    
    try:
        response = MODEL.generate_content(prompt)
        return parse_analysis_response(response.text, language) if response else {"error": "⚠️ Empty response"}
    except Exception as e:
        return {"error": f"Analysis failed: {str(e)}"}

# Parse AI Response
def parse_analysis_response(response_text: str, language: str) -> Dict:
    """Parse AI response into structured format"""
    sections = {"bugs": [], "fixes": [], "corrected_code": "", "optimizations": [], "explanation": []}
    current_section = None
    
    for line in response_text.split('\n'):
        if "CORRECTED_CODE" in line:
            current_section = "corrected_code"
            continue
        if line.startswith("###"):
            current_section = line[4:].lower().replace(" ", "_")
            continue
        if current_section and line.strip():
            if current_section == "corrected_code":
                sections["corrected_code"] += line + "\n"
            else:
                sections[current_section].append(line.strip())
    
    sections["corrected_code"] = sections["corrected_code"].strip()
    return sections
