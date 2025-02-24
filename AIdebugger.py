import streamlit as st
import json
import os
import re
import google.generativeai as genai
from google.cloud import vision
from google.oauth2 import service_account
from google.api_core.exceptions import GoogleAPICallError, RetryError

# Initialize page configuration
st.set_page_config(page_title="AI Code Debugger", layout="wide")

# ========== SESSION STATE ==========
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = {}
if 'current_code' not in st.session_state:
    st.session_state.current_code = ""

# ========== SIDEBAR ==========
with st.sidebar:
    st.title("🧠 AI Assistant")
    st.markdown("---")
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    st.markdown("---")
    st.subheader("💡 Usage Tips")
    st.markdown("""
    1. Upload images under 5MB
    2. Supported formats: PNG, JPG
    3. Clear code screenshots work best
    4. Ask follow-up questions below
    """)

# ========== CREDENTIALS ==========
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

# ========== AI CONFIG ==========
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

# ========== CORE FUNCTIONS ==========
def extract_code_from_image(image) -> str:
    """Robust OCR with timeout and size checks"""
    try:
        # Validate image size
        max_size = 5 * 1024 * 1024  # 5MB
        content = image.read()
        if len(content) > max_size:
            return "Error: Image size exceeds 5MB limit"

        # Process image
        client = vision.ImageAnnotatorClient(credentials=credentials)
        response = client.text_detection(
            image=vision.Image(content=content),
            timeout=15  # 15 second timeout
        )

        if response.error.message:
            return f"API Error: {response.error.message}"
            
        return response.text_annotations[0].description.strip() if response.text_annotations else "No text detected"

    except (GoogleAPICallError, RetryError) as e:
        return f"API Error: {str(e)}"
    except Exception as e:
        return f"Processing Error: {str(e)}"

def analyze_code(code: str, language: str) -> dict:
    """Code analysis with robust error handling"""
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
1. Output ONLY valid JSON
2. Escape special characters
3. Maintain array lengths

**{language.upper()} CODE:**
{code}
"""
        response = MODEL.generate_content(prompt)
        raw_text = response.text.strip()
        
        # Clean JSON response
        cleaned = re.sub(r'(?i)^\s*(```json|```)', '', raw_text)
        cleaned = re.sub(r'[\x00-\x1F]', '', cleaned)
        
        return json.loads(cleaned)
        
    except json.JSONDecodeError:
        return {"error": "Failed to parse AI response"}
    except Exception as e:
        return {"error": f"Analysis failed: {str(e)}"}

# ========== MAIN INTERFACE ==========
st.title("🛠️ AI-Powered Code Debugger")

# Input method selection
input_method = st.radio("Input Method:", 
                       ["📷 Image", "📁 File", "📝 Paste"],
                       horizontal=True)

code_text = ""
language = "python"

# Image processing
if input_method == "📷 Image":
    img_file = st.file_uploader("Upload Code Image", type=["png", "jpg", "jpeg"])
    if img_file:
        with st.spinner("Extracting code (max 15 seconds)..."):
            code_text = extract_code_from_image(img_file)
        
        if "Error" in code_text:
            st.error(code_text)
            st.session_state.analysis_results = {}
        else:
            st.code(code_text, language="text")

# File upload
elif input_method == "📁 File":
    code_file = st.file_uploader("Upload Code File", type=["py", "java", "js"])
    if code_file:
        code_text = code_file.read().decode("utf-8")
        ext = code_file.name.split(".")[-1]
        language = {"py": "python", "java": "java", "js": "javascript"}.get(ext, "text")
        st.code(code_text, language=language)

# Code paste
else:
    code_text = st.text_area("Paste Code Here:", height=300)
    if code_text:
        st.code(code_text, language="text")

# Analysis
if code_text.strip() and not code_text.startswith("Error"):
    if st.button("🚀 Analyze Code"):
        st.session_state.current_code = code_text
        with st.spinner("Analyzing..."):
            st.session_state.analysis_results = analyze_code(code_text, language)

# Display results
if st.session_state.analysis_results:
    results = st.session_state.analysis_results
    
    if "error" in results:
        st.error(results["error"])
    else:
        with st.expander("🐛 Bugs", expanded=True):
            for bug in results.get("bugs", []):
                st.error(f"- {bug}")
        
        with st.expander("🛠️ Fixes"):
            for fix in results.get("fixes", []):
                st.info(f"- {fix}")
        
        with st.expander("✅ Corrected Code"):
            st.code(results.get("corrected_code", ""), language=language)
        
        with st.expander("📚 Explanation"):
            for exp in results.get("explanation", []):
                st.write(f"- {exp}")

# Chat interface
user_query = st.chat_input("Ask coding questions...")
if user_query:
    try:
        st.session_state.chat_history.append({"role": "user", "content": user_query})
        response = MODEL.generate_content(user_query)
        st.session_state.chat_history.append({"role": "assistant", "content": response.text})
        st.rerun()
    except Exception as e:
        st.error(f"Chat error: {str(e)}")
