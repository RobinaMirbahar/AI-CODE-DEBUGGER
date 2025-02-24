import streamlit as st
import json
import os
import re
import google.generativeai as genai
from google.cloud import vision
from google.oauth2 import service_account
from typing import Dict, List

# Initialize page configuration
st.set_page_config(page_title="AI Code Debugger", layout="wide")

# ========== SESSION STATE INITIALIZATION ==========
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = {}
if 'current_code' not in st.session_state:
    st.session_state.current_code = ""

# ========== SIDEBAR COMPONENTS ==========
with st.sidebar:
    st.title("🧠 AI Assistant")
    st.markdown("---")
    
    # Display chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    st.markdown("---")
    st.subheader("💡 Usage Tips")
    st.markdown("""
    1. Choose input method (Image/File/Text)
    2. Upload or paste your code
    3. Click 'Analyze Code'
    4. Review suggestions
    5. Ask follow-up questions
    """)

# ========== CREDENTIALS INITIALIZATION ==========
try:
    credentials = None
    google_api_key = os.getenv("GOOGLE_API_KEY")
    
    if cred_json := os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON"):
        credentials_dict = json.loads(cred_json)
        required_fields = ["type", "project_id", "private_key_id", 
                         "private_key", "client_email", "client_id"]
        
        if missing := [f for f in required_fields if f not in credentials_dict]:
            st.error(f"Missing credentials: {', '.join(missing)}")
            st.stop()
            
        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict,
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
    
    genai.configure(api_key=google_api_key)
except Exception as e:
    st.error(f"Initialization error: {str(e)}")
    st.stop()

# ========== AI MODEL CONFIGURATION ==========
MODEL_CONFIG = {
    'safety_settings': {
        'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE',
        'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE',
        'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE',
        'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_NONE'
    },
    'generation_config': genai.types.GenerationConfig(
        max_output_tokens=4000,
        temperature=0.25
    )
}

MODEL = genai.GenerativeModel('gemini-pro', **MODEL_CONFIG)

# ========== CORE FUNCTIONS ==========
def analyze_code(code: str, language: str) -> Dict:
    """Analyze code using Gemini with enhanced error handling"""
    try:
        prompt = f"""**CODE ANALYSIS REQUEST**
Return JSON in this EXACT format:
{{
    "bugs": ["Line 5: Missing semicolon"],
    "fixes": ["Add semicolon at line 5"],
    "corrected_code": "function example() {{\\n  console.log('fixed');\\n}}",
    "optimizations": ["Use const instead of let"],
    "explanation": ["Semicolons are required..."]
}}

**RULES:**
1. Strict JSON format
2. Escape special characters
3. Maintain array consistency
4. Use double quotes

**{language.upper()} CODE:**
{code}
"""
        response = MODEL.generate_content(prompt)
        
        if not response.text:
            return {"error": "Empty AI response"}

        # Clean and validate response
        raw_text = response.text.strip()
        cleaned = re.sub(r'(?i)^\s*(```json|```)', '', raw_text)
        cleaned = re.sub(r'[\x00-\x1F]', '', cleaned)  # Remove control chars
        
        # Repair common JSON issues
        repaired = (
            cleaned.replace("'", '"')
            .replace("True", "true")
            .replace("False", "false")
            .replace("None", "null")
            .replace(",\n}", "\n}")
        )
        
        return json.loads(repaired)
        
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON format: {str(e)}"}
    except Exception as e:
        return {"error": f"Analysis failed: {str(e)}"}

def extract_code_from_image(image) -> str:
    """Extract text from image using Vision API"""
    try:
        client = vision.ImageAnnotatorClient(credentials=credentials)
        content = image.read()
        image = vision.Image(content=content)
        
        response = client.text_detection(image=image)
        
        if response.error.message:
            return f"Vision API Error: {response.error.message}"
            
        if not response.text_annotations:
            return "No text detected in image"
            
        return response.text_annotations[0].description.strip()
        
    except Exception as e:
        return f"OCR Error: {str(e)}"

# ========== MAIN INTERFACE ==========
st.title("🛠️ AI-Powered Code Debugger")

# Input method selection
input_method = st.radio(
    "SELECT INPUT METHOD:",
    ["📷 Upload Image", "📁 Upload File", "📝 Paste Code"],
    horizontal=True,
    index=2
)

code_text = ""
language = "python"

# Handle image upload
if input_method == "📷 Upload Image":
    img_file = st.file_uploader(
        "Upload Code Screenshot",
        type=["png", "jpg", "jpeg"],
        help="Upload a clear image of your code"
    )
    if img_file:
        with st.spinner("Extracting code from image..."):
            code_text = extract_code_from_image(img_file)
            if "Error" in code_text:
                st.error(code_text)
            else:
                st.subheader("Extracted Code")
                st.code(code_text, language="text")

# Handle file upload
elif input_method == "📁 Upload File":
    code_file = st.file_uploader(
        "Upload Code File",
        type=["py", "java", "js", "cpp", "html"],
        help="Supported formats: Python, Java, JavaScript, C++, HTML"
    )
    if code_file:
        code_text = code_file.read().decode("utf-8")
        ext = code_file.name.split(".")[-1]
        language = {
            "py": "python", 
            "java": "java", 
            "js": "javascript",
            "cpp": "cpp",
            "html": "html"
        }.get(ext, "text")
        st.subheader("Uploaded Code")
        st.code(code_text, language=language)

# Handle code paste
else:
    code_text = st.text_area(
        "Paste Your Code Here:",
        height=300,
        placeholder="// Paste your code here...\nfunction example() {\n  // Your code\n}",
        help="Paste any code snippet for analysis"
    )
    if code_text:
        st.subheader("Code Preview")
        st.code(code_text, language="text")

# Analysis trigger
if code_text.strip():
    if st.button("🚀 Analyze Code", use_container_width=True):
        st.session_state.current_code = code_text
        with st.spinner("Analyzing code..."):
            st.session_state.analysis_results = analyze_code(code_text, language)

# Display results
if st.session_state.analysis_results:
    results = st.session_state.analysis_results
    
    if "error" in results:
        st.error(f"Analysis Error: {results['error']}")
    else:
        st.subheader("🔍 Analysis Results")
        
        with st.expander("🐛 Identified Bugs", expanded=True):
            for bug in results.get("bugs", []):
                st.error(f"- {bug}")
        
        with st.expander("🔧 Suggested Fixes"):
            for fix in results.get("fixes", []):
                st.info(f"- {fix}")
        
        with st.expander("✨ Optimized Code"):
            st.code(results.get("corrected_code", ""), language=language)
        
        with st.expander("📖 Detailed Explanation"):
            for exp in results.get("explanation", []):
                st.write(f"- {exp}")

# Chat interface at bottom
user_query = st.chat_input("Ask questions about the code...")

# Handle chat interactions
if user_query and MODEL:
    try:
        st.session_state.chat_history.append({"role": "user", "content": user_query})
        
        with st.spinner("Generating response..."):
            response = MODEL.generate_content(user_query)
            
            if response.text:
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response.text
                })
                st.rerun()
                
    except Exception as e:
        st.error(f"Chat error: {str(e)}")
