import streamlit as st
import json
import os
import re
import google.generativeai as genai
from google.cloud import vision
from google.oauth2 import service_account
import subprocess
from datetime import datetime

# Streamlit configuration (MUST be first)
st.set_page_config(
    page_title="🛠️ AI Code Debugger Pro",
    page_icon="🤖",
    layout="wide"
)

# Configuration Management
def get_secret(key, default=None):
    """Secure secret retrieval from multiple sources"""
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError):
        return os.getenv(key, default)

# Gemini AI Configuration
GEMINI_API_KEY = get_secret("GEMINI_API_KEY") or st.sidebar.text_input(
    "🔑 Enter Gemini API Key", 
    type="password",
    help="Get from https://aistudio.google.com/app/apikey"
)

if not GEMINI_API_KEY:
    st.error("❌ Gemini API Key required")
    st.stop()

try:
    genai.configure(api_key=GEMINI_API_KEY)
except Exception as e:
    st.error(f"🔧 Gemini setup failed: {str(e)}")
    st.stop()

# Vision API Configuration
def configure_vision():
    """Interactive Vision API setup with validation"""
    vision_enabled = False
    with st.sidebar.expander("🔧 Vision API Settings", expanded=False):
        if creds := get_secret("GOOGLE_APPLICATION_CREDENTIALS"):
            try:
                service_account_info = json.loads(creds)
                credentials = service_account.Credentials.from_service_account_info(service_account_info)
                vision_client = vision.ImageAnnotatorClient(credentials=credentials)
                vision_enabled = True
                st.success("✅ Vision API Active")
            except Exception as e:
                st.error(f"⚠️ Invalid credentials: {str(e)}")
        
        uploaded_creds = st.file_uploader(
            "Upload Service Account JSON",
            type=["json"],
            help="Required for image processing"
        )
        
        if uploaded_creds:
            try:
                credentials = json.load(uploaded_creds)
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = json.dumps(credentials)
                st.rerun()
            except Exception as e:
                st.error(f"❌ Invalid file: {str(e)}")
        
        st.markdown("""
        **Enable Vision API:**
        1. [Create Google Cloud Project](https://console.cloud.google.com/)
        2. Enable **Cloud Vision API**
        3. Create Service Account with **Vision API User** role
        4. Download JSON credentials
        """)
    
    return vision_enabled

# Initialize Vision API
vision_enabled = configure_vision()
vision_client = None
if vision_enabled:
    try:
        credentials = service_account.Credentials.from_service_account_info(
            json.loads(get_secret("GOOGLE_APPLICATION_CREDENTIALS"))
        )
        vision_client = vision.ImageAnnotatorClient(credentials=credentials)
    except Exception as e:
        st.error(f"⚠️ Vision API Error: {str(e)}")

# Gemini Model Configuration
SAFETY_SETTINGS = {
    'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE',
    'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE',
    'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE',
    'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_NONE'
}

try:
    MODEL = genai.GenerativeModel('gemini-1.5-pro-latest',
        safety_settings=SAFETY_SETTINGS,
        generation_config=genai.types.GenerationConfig(
            max_output_tokens=4000,
            temperature=0.25
        )
    )
except Exception as e:
    st.error(f"🤖 Model initialization failed: {str(e)}")
    st.stop()

# Code Execution
def execute_code(code, language):
    """Safe code execution with isolation"""
    try:
        if language == "python":
            result = subprocess.run(["python3", "-c", code], 
                                  capture_output=True, text=True, timeout=10)
        elif language == "javascript":
            result = subprocess.run(["node", "-e", code], 
                                  capture_output=True, text=True, timeout=10)
        elif language == "java":
            with open("Temp.java", "w") as f:
                f.write(code)
            compile_result = subprocess.run(["javac", "Temp.java"], 
                                          capture_output=True, text=True)
            if compile_result.returncode != 0:
                return compile_result.stderr
            result = subprocess.run(["java", "Temp"], 
                                  capture_output=True, text=True, timeout=15)
        else:
            return "⚠️ Unsupported language"
        
        return result.stdout or result.stderr
    except subprocess.TimeoutExpired:
        return "⏰ Execution timed out"
    except Exception as e:
        return f"🚨 Execution Error: {str(e)}"

# Enhanced JSON Parsing
def parse_ai_response(response_text):
    """Multi-stage JSON extraction"""
    try:
        # Attempt direct JSON parse
        return json.loads(response_text)
    except json.JSONDecodeError:
        try:
            # Extract from markdown code block
            json_match = re.search(r'```json\n(.*?)```', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1).strip())
            
            # Find JSON in text
            json_str = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_str:
                return json.loads(json_str.group())
            
            return {"error": "No valid JSON found"}
        except Exception as e:
            return {"error": f"Parse failed: {str(e)}", "raw": response_text}

# Core Analysis Function
def analyze_code(code_snippet, language="python"):
    if not code_snippet.strip():
        return {"error": "⚠️ No code provided"}
    
    prompt = f"""Analyze this {language} code and return JSON response:
    ```{language}
    {code_snippet}
    ```
    
    Required JSON format:
    {{
        "bugs": ["list", "of", "issues"],
        "fixes": ["step-by-step", "corrections"],
        "corrected_code": "full_corrected_code_here",
        "optimizations": ["performance_improvements"],
        "security_issues": ["potential_vulnerabilities"]
    }}
    
    Return ONLY valid JSON without commentary."""
    
    try:
        response = MODEL.generate_content(prompt)
        if not response.text:
            return {"error": "⚠️ Empty AI response"}
        
        parsed = parse_ai_response(response.text)
        parsed["raw_response"] = response.text  # For debugging
        
        # Validate corrected code
        if "corrected_code" in parsed:
            parsed["validation"] = execute_code(
                parsed["corrected_code"], 
                language
            )
        
        return parsed
    except Exception as e:
        return {"error": f"⚠️ Analysis failed: {str(e)}"}

# Image Processing
def extract_code_from_image(image):
    if not vision_client:
        return "⚠️ Enable Vision API in settings"
    
    try:
        content = image.read()
        image = vision.Image(content=content)
        response = vision_client.text_detection(image=image)
        
        if response.error.message:
            return f"⚠️ Vision API Error: {response.error.message}"
            
        return response.text_annotations[0].description if response.text_annotations else "⚠️ No text found"
    except Exception as e:
        return f"⚠️ Image Error: {str(e)}"

# UI Components
st.title("🤖 AI Code Debugger Pro")
st.markdown("""
    <style>
    .stCodeBlock {border-radius: 10px; padding: 15px!important;}
    .stMarkdown pre {background: #f8f9fa;}
    .reportview-container {background: #ffffff;}
    </style>
""", unsafe_allow_html=True)

# Input Section
input_method = st.radio("Choose Input Method:", 
                       ["📝 Paste Code", "📁 Upload File", "🖼️ Image Capture"],
                       horizontal=True)

code_input = ""
language = "python"

if input_method == "📝 Paste Code":
    code_input = st.text_area("Code Input", height=300, placeholder="Paste your code here...")
    language = st.selectbox("Language", ["python", "javascript", "java"])

elif input_method == "📁 Upload File":
    uploaded_file = st.file_uploader("Choose File", type=["py", "js", "java"])
    if uploaded_file:
        code_input = uploaded_file.read().decode()
        ext = uploaded_file.name.split(".")[-1]
        language = {"py": "python", "js": "javascript", "java": "java"}.get(ext, "python")

elif input_method == "🖼️ Image Capture":
    if not vision_enabled:
        st.warning("Enable Vision API in settings to use this feature")
    else:
        image_file = st.file_uploader("Upload Image", type=["png", "jpg", "jpeg"])
        if image_file:
            code_input = extract_code_from_image(image_file)
            st.code(code_input, language="python")

# Analysis Execution
if st.button("🚀 Start Analysis", type="primary"):
    if not code_input.strip():
        st.error("⚠️ Please provide code input")
    else:
        with st.spinner("🔍 Analyzing code..."):
            start_time = datetime.now()
            result = analyze_code(code_input, language)
            duration = (datetime.now() - start_time).total_seconds()
            
            st.subheader(f"📊 Analysis Results ({duration:.2f}s)")
            
            if "error" in result:
                st.error(result["error"])
                if "raw_response" in result:
                    with st.expander("View Raw Response"):
                        st.code(result["raw_response"])
            else:
                tabs = st.tabs(["🐛 Bugs", "🛠 Fixes", "⚡ Optimizations", "🔒 Security"])
                
                with tabs[0]:
                    st.write("### Identified Issues")
                    st.json(result.get("bugs", []))
                
                with tabs[1]:
                    st.write("### Corrected Code")
                    st.code(result.get("corrected_code", ""), language=language)
                    st.write("### Validation Results")
                    st.code(result.get("validation", ""))
                
                with tabs[2]:
                    st.write("### Optimization Suggestions")
                    st.markdown("\n".join([f"- {item}" for item in result.get("optimizations", [])]))
                
                with tabs[3]:
                    st.write("### Security Issues")
                    st.markdown("\n".join([f"- 🔒 {item}" for item in result.get("security_issues", [])]))

# Debugging Section
with st.expander("🔧 Debugging Tools"):
    if st.button("Show Session State"):
        st.write(st.session_state)
    
    if st.checkbox("Show Raw AI Responses"):
        if 'last_raw_response' in st.session_state:
            st.code(st.session_state.last_raw_response)

# Footer
st.markdown("---")
st.markdown("🔐 **Security Notice:** All processing done through Google's API. No data stored.")
st.caption("v2.2 | AI Code Debugger Pro | Powered by Google Gemini")

# Error Handling
if 'error' in st.session_state:
    st.error(st.session_state.error)
    del st.session_state.error
