import streamlit as st
import json
import google.generativeai as genai
from google.cloud import vision
from google.oauth2 import service_account
import os

# --- MUST BE FIRST STREAMLIT COMMAND ---
st.set_page_config(page_title="AI Code Debugger", layout="wide")
# ---------------------------------------

# Initialize session state
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = {}
if 'current_code' not in st.session_state:
    st.session_state.current_code = ""

# --- Credential Handling (No Streamlit commands here) ---
CREDENTIALS = None
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

try:
    # Load Google Cloud credentials
    credentials_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
    if credentials_json:
        creds_dict = json.loads(credentials_json)
        CREDENTIALS = service_account.Credentials.from_service_account_info(creds_dict)
        
    # Configure Gemini
    if GOOGLE_API_KEY:
        genai.configure(api_key=GOOGLE_API_KEY)
        
except Exception as cred_error:
    st.error("⚠️ Initialization Error - Check configuration")
    st.stop()

# --- Streamlit UI Starts Here ---
st.title("🛠️ AI-Powered Code Debugger")

def validate_services():
    """Check required services are available"""
    errors = []
    if not CREDENTIALS:
        errors.append("Google Cloud credentials not configured")
    if not GOOGLE_API_KEY:
        errors.append("Google API key missing")
    return errors

# Show configuration errors at top
if service_errors := validate_services():
    st.error("CRITICAL CONFIGURATION ISSUES:")
    for error in service_errors:
        st.write(f"- {error}")
    st.stop()

# --- Rest of Application Code ---
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

def analyze_code(code: str, language: str) -> dict:
    """Code analysis implementation"""
    try:
        prompt = f"""Analyze this {language} code and provide JSON response with:
        - bugs (list)
        - fixes (list)
        - corrected_code (str)
        - optimizations (list)
        - explanation (list)
        
        Code:\n{code}"""
        
        response = MODEL.generate_content(prompt)
        if response and response.text:
            return json.loads(response.text.strip("```json "))
        else:
            return {"error": "No response from AI model"}
    except json.JSONDecodeError:
        return {"error": "❌ Failed to parse AI response"}
    except Exception as e:
        return {"error": str(e)}

def extract_code_from_image(image):
    """Image processing implementation"""
    try:
        client = vision.ImageAnnotatorClient(credentials=CREDENTIALS)
        content = image.read()
        response = client.text_detection(image=vision.Image(content=content))
        return response.text_annotations[0].description.strip() if response.text_annotations else ""
    except Exception as e:
        return f"Error: {str(e)}"

# Streamlit UI Configuration
st.set_page_config(page_title="AI Code Debugger", layout="wide")
st.title("🛠️ AI-Powered Code Debugger")

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
    results = st.session_state.analysis_results
    
    if "error" in results:
        st.error(results["error"])
    else:
        st.subheader("🔍 Analysis Results")
        
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
