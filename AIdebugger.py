import streamlit as st
import json
import google.generativeai as genai
from google.cloud import vision
from google.oauth2 import service_account
from typing import Dict, List
import os

# Initialize session state
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = {}
if 'current_code' not in st.session_state:
    st.session_state.current_code = ""

def get_credentials():
    """Enhanced credential handling with detailed error reporting"""
    credentials_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
    
    if not credentials_json:
        st.error("❌ Missing Google Cloud credentials in environment variables")
        st.info("Ensure GOOGLE_APPLICATION_CREDENTIALS_JSON is set with valid service account JSON")
        return None

    try:
        credentials_dict = json.loads(credentials_json)
        required_fields = ["type", "project_id", "private_key_id", 
                          "private_key", "client_email", "client_id"]
        
        missing = [field for field in required_fields if field not in credentials_dict]
        if missing:
            st.error(f"❌ Invalid credentials: Missing fields {', '.join(missing)}")
            return None
            
        credentials = service_account.Credentials.from_service_account_info(credentials_dict)
        
        # Test credentials with Vision API
        vision.ImageAnnotatorClient(credentials=credentials).get_iam_policy()
        return credentials
        
    except json.JSONDecodeError:
        st.error("❌ Invalid JSON format in credentials")
        return None
    except Exception as e:
        st.error(f"❌ Credential verification failed: {str(e)}")
        return None

# Initialize credentials
credentials = get_credentials()

# Configure Gemini API
try:
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
except Exception as e:
    st.error(f"❌ Gemini API configuration failed: {str(e)}")
    MODEL = None

def analyze_code(code: str, language: str) -> Dict:
    """Improved code analysis with robust error handling"""
    if not MODEL:
        return {"error": "❌ AI model not initialized"}
    
    try:
        prompt = f"""As a senior software engineer, analyze this {language} code:
{code}

Provide JSON response with these keys:
- bugs: list of strings with line numbers
- fixes: list of strings with concrete solutions
- corrected_code: full corrected code as string
- optimizations: list of performance improvements
- explanation: list of technical explanations

Example format:
{{
    "bugs": ["Line 5: Missing semicolon"],
    "fixes": ["Add ';' at line 5"],
    "corrected_code": "...",
    "optimizations": ["Use more efficient data structure"],
    "explanation": ["The code fails because..."]
}}"""

        response = MODEL.generate_content(prompt)
        
        if not response.text:
            return {"error": "❌ Empty response from AI model"}
            
        # Clean and validate response
        cleaned = response.text.strip().replace("```json", "").replace("```", "")
        try:
            result = json.loads(cleaned)
            required_keys = {"bugs", "fixes", "corrected_code", "optimizations", "explanation"}
            if not required_keys.issubset(result.keys()):
                return {"error": "❌ Invalid response format from AI"}
            return result
        except json.JSONDecodeError:
            return {"error": f"❌ Failed to parse JSON. Raw response: {cleaned[:200]}"}
            
    except Exception as e:
        return {"error": f"❌ Analysis failed: {str(e)}"}

def extract_code_from_image(image) -> str:
    """Enhanced OCR processing with better error handling"""
    if not credentials:
        return "⚠️ Invalid credentials: Check your Google Cloud setup."

    try:
        client = vision.ImageAnnotatorClient(credentials=credentials)
        content = image.read()
        img = vision.Image(content=content)
        response = client.text_detection(image=img)
        
        if response.error.message:
            return f"⚠️ Vision API Error: {response.error.message}"
            
        if not response.text_annotations:
            return "⚠️ No text detected in image"
            
        try:
            return response.text_annotations[0].description.strip()
        except IndexError:
            return "⚠️ Empty text annotations from API"
        except AttributeError:
            return "⚠️ Invalid API response format"
            
    except Exception as e:
        return f"⚠️ OCR processing failed: {str(e)}"

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
