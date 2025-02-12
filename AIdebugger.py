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

# Load credentials from GitHub Secrets
credentials_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")

if credentials_json:
    credentials = json.loads(credentials_json)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS_JSON"] = json.dumps(credentials)
    print("✅ Google Cloud credentials successfully loaded from GitHub Secrets!")
else:
    print("⚠️ GOOGLE_APPLICATION_CREDENTIALS_JSON is missing! Add it as a GitHub secret.")

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

def parse_analysis_response(response_text: str, language: str) -> Dict:
    """Parse AI response into structured format"""
    sections = {
        "bugs": [], "fixes": [], 
        "corrected_code": "", 
        "optimizations": [], 
        "explanation": []
    }
    
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

# Image Processing
def extract_code_from_image(image) -> str:
    """Extract code from image using Google Vision"""
    if not credentials_json:
        return "⚠️ Invalid credentials"
    
    try:
        client = vision.ImageAnnotatorClient(credentials=credentials)
        content = image.read()
        image = vision.Image(content=content)
        response = client.text_detection(image=image)
        return '\n'.join([line.strip() for line in response.text_annotations[0].description.split('\n') if line.strip()])
    except Exception as e:
        return f"⚠️ OCR Error: {str(e)}"

# Streamlit UI
st.set_page_config(page_title="AI Code Debugger", layout="wide")
st.title("🛠️ AI-Powered Code Debugger")
st.write("Upload code via image/file or paste directly for analysis")

# Input Methods
input_method = st.radio("Choose input method:", 
                       ["📷 Image Upload", "📁 File Upload", "📝 Paste Code"],
                       horizontal=True)

code_text = ""
language = "python"

# Handle Image Upload
if input_method == "📷 Image Upload":
    image_file = st.file_uploader("Upload code image", type=["png", "jpg", "jpeg"])
    if image_file:
        code_text = extract_code_from_image(image_file)
        st.code(code_text, language="python")

# Handle File Upload
elif input_method == "📁 File Upload":
    code_file = st.file_uploader("Upload code file", type=["py", "java", "js"])
    if code_file:
        code_text = code_file.read().decode("utf-8")
        ext = code_file.name.split(".")[-1]
        language = {"py": "python", "java": "java", "js": "javascript"}.get(ext, "python")
        st.code(code_text, language=language)

# Handle Paste Code
else:
    code_text = st.text_area("Paste your code here:", height=300)
    if code_text:
        st.code(code_text, language="python")

# Analysis Execution
if st.button("🚀 Analyze Code") and code_text.strip():
    st.session_state.current_code = code_text
    with st.spinner("🔍 Analyzing code..."):
        st.session_state.analysis_results = analyze_code(code_text, language)

# Display Results
if st.session_state.analysis_results:
    if "error" in st.session_state.analysis_results:
        st.error(st.session_state.analysis_results["error"])
    else:
        st.subheader("🔍 Analysis Results")
        results = st.session_state.analysis_results
        
        with st.expander("🐛 Identified Bugs", expanded=True):
            for bug in results.get("bugs", []):
                st.error(f"- {bug}")
        
        with st.expander("🛠️ Suggested Fixes"):
            for fix in results.get("fixes", []):
                st.info(f"- {fix}")
        
        with st.expander("✅ Corrected Code"):
            st.code(results.get("corrected_code", ""), language=language)
        
        with st.expander("⚡ Optimizations"):
            for opt in results.get("optimizations", []):
                st.success(f"- {opt}")
        
        with st.expander("📚 Explanation"):
            for exp in results.get("explanation", []):
                st.write(f"- {exp}")
