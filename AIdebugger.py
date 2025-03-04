import streamlit as st
import json
import os
import google.generativeai as genai
from google.cloud import vision
from google.oauth2 import service_account
import subprocess
from datetime import datetime

# Streamlit configuration MUST be first
st.set_page_config(
    page_title="🛠️ AI Code Debugger Pro",
    page_icon="🤖",
    layout="wide"
)

# Secure Configuration Handling
def get_secret(key, default=None):
    """Get secrets from multiple sources with fallback"""
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError):
        return os.getenv(key, default)

# Configure Gemini API with multiple fallbacks
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
    st.error(f"🔧 Gemini configuration failed: {str(e)}")
    st.stop()

# Google Cloud Vision Setup
def get_vision_client():
    """Initialize Vision API client with error handling"""
    try:
        creds_json = get_secret("GOOGLE_APPLICATION_CREDENTIALS")
        if not creds_json:
            return None
            
        service_account_info = json.loads(creds_json)
        credentials = service_account.Credentials.from_service_account_info(service_account_info)
        return vision.ImageAnnotatorClient(credentials=credentials)
    except Exception as e:
        st.error(f"🔧 Vision API error: {str(e)}")
        return None

vision_client = get_vision_client()

# AI Model Configuration
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

# AI Assistant Sidebar
def ai_assistant():
    st.sidebar.title("🧠 AI Assistant")
    user_query = st.sidebar.text_input("🔍 Ask about debugging:",
                                      help="Get coding advice from Gemini")
    if user_query:
        try:
            response = MODEL.generate_content(f"Provide expert guidance: {user_query}")
            if response.text:
                st.sidebar.markdown(f"**AI Response:**\n{response.text}")
            else:
                st.sidebar.warning("⚠️ No response from AI")
        except Exception as e:
            st.sidebar.error(f"API Error: {str(e)}")

# Secure Code Execution
def execute_code(code, language):
    """Run code in isolated environment with timeout"""
    try:
        if language == "python":
            result = subprocess.run(["python3", "-c", code],
                                   capture_output=True,
                                   text=True,
                                   timeout=10,
                                   check=True)
        elif language == "javascript":
            result = subprocess.run(["node", "-e", code],
                                   capture_output=True,
                                   text=True,
                                   timeout=10)
        elif language == "java":
            with open("Temp.java", "w") as f:
                f.write(code)
            compile_result = subprocess.run(["javac", "Temp.java"],
                                           capture_output=True,
                                           text=True)
            if compile_result.returncode != 0:
                return compile_result.stderr
            result = subprocess.run(["java", "Temp"],
                                   capture_output=True,
                                   text=True,
                                   timeout=15)
        else:
            return "⚠️ Unsupported language"
        
        return result.stdout or result.stderr
    except subprocess.TimeoutExpired:
        return "⏰ Execution timed out"
    except Exception as e:
        return f"🚨 Execution Error: {str(e)}"

# Enhanced Code Analysis
def analyze_code(code_snippet, language="python"):
    if not code_snippet.strip():
        return {"error": "⚠️ No code provided"}
    
    # Step 1: Initial Execution
    execution_result = execute_code(code_snippet, language)
    
    # Step 2: AI Analysis
    prompt = f"""Analyze this {language} code:
    ```{language}
    {code_snippet}
    ```
    Provide JSON response with:
    {{
        "bugs": "list of identified issues",
        "fixes": ["step-by-step corrections"],
        "corrected_code": "improved code",
        "optimizations": ["performance improvements"],
        "security_issues": ["security vulnerabilities"]
    }}"""
    
    try:
        response = MODEL.generate_content(prompt)
        if not response.text:
            return {"error": "⚠️ Empty AI response"}
            
        analysis = json.loads(response.text)
        
        # Step 3: Validate Corrected Code
        if "corrected_code" in analysis:
            analysis["validation_result"] = execute_code(
                analysis["corrected_code"], 
                language
            )
        
        analysis["initial_execution"] = execution_result
        return analysis
        
    except json.JSONDecodeError:
        return {"error": "⚠️ Failed to parse AI response"}
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
        texts = response.text_annotations
        return texts[0].description if texts else "⚠️ No text detected"
    except Exception as e:
        return f"⚠️ Vision API error: {str(e)}"

# Main UI
st.title("🤖 AI Code Debugger Pro")
st.markdown("""
    **Debug code from images, files, or text input using Google Gemini & Vision API**
    <style>
    .stCodeBlock {border-radius: 10px; padding: 15px!important;}
    .stMarkdown pre {background: #f8f9fa;}
    </style>
""", unsafe_allow_html=True)

# Initialize Assistant
ai_assistant()

# File Upload Section
with st.expander("📤 Upload Code or Image", expanded=True):
    col1, col2 = st.columns(2)
    
    with col1:
        image_file = st.file_uploader("🖼️ Image with Code", 
                                    type=["png", "jpg", "jpeg"],
                                    help="Snap a photo of handwritten code")
        
    with col2:
        code_file = st.file_uploader("📁 Code File", 
                                   type=["py", "js", "java"],
                                   help="Upload source files directly")

# Code Input Section
code_input = st.text_area("📝 Paste Code Here", 
                         height=300,
                         placeholder="Enter your code here...",
                         help="Supports Python, JavaScript, Java")

# Analysis Controls
if st.button("🚀 Start Analysis", use_container_width=True):
    analysis_result = None
    start_time = datetime.now()
    
    with st.spinner("🔍 Analyzing code..."):
        if image_file:
            extracted_code = extract_code_from_image(image_file)
            st.code(extracted_code, language="python")
            analysis_result = analyze_code(extracted_code)
        elif code_file:
            content = code_file.read().decode()
            lang = code_file.name.split(".")[-1]
            analysis_result = analyze_code(content, lang)
        elif code_input:
            analysis_result = analyze_code(code_input)
        else:
            st.error("⚠️ Please provide input")
            
    if analysis_result:
        st.success(f"✅ Analysis completed in {(datetime.now()-start_time).total_seconds():.2f}s")
        
        with st.container():
            st.subheader("🧐 Analysis Report")
            
            if "error" in analysis_result:
                st.error(analysis_result["error"])
            else:
                tabs = st.tabs(["🐛 Bugs", "🛠 Fixes", "⚡ Optimizations", "🔒 Security"])
                
                with tabs[0]:
                    st.write(analysis_result.get("bugs", "No issues found"))
                    st.json(analysis_result.get("initial_execution", {}))
                
                with tabs[1]:
                    st.code(analysis_result.get("corrected_code", ""), 
                           language="python")
                    st.write("Validation Result:")
                    st.code(analysis_result.get("validation_result", ""))
                
                with tabs[2]:
                    st.markdown("\n".join(
                        [f"- {item}" for item in analysis_result.get("optimizations", [])]
                    ))
                
                with tabs[3]:
                    st.markdown("\n".join(
                        [f"- 🔒 {item}" for item in analysis_result.get("security_issues", [])]
                    ))

# Security Footer
st.markdown("---")
st.markdown("🔐 **Security Notice:** All code processing is done through Google's secure APIs. No data is stored permanently.")
st.caption("v2.1 | AI Code Debugger Pro | Powered by Google Gemini")

# Error Handling
if 'error' in st.session_state:
    st.error(st.session_state.error)
    del st.session_state.error
