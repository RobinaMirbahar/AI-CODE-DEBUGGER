import streamlit as st
import json
import os
import re
import google.generativeai as genai
from google.cloud import vision
from google.oauth2 import service_account
from typing import Dict, List

# Set page config FIRST
st.set_page_config(page_title="AI Code Debugger", layout="wide")

# Initialize session state
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = {}
if 'current_code' not in st.session_state:
    st.session_state.current_code = ""
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Load credentials
credentials = None
google_api_key = os.getenv("GOOGLE_API_KEY")

try:
    if cred_json := os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON"):
        credentials_dict = json.loads(cred_json)
        required_fields = ["type", "project_id", "private_key_id", 
                          "private_key", "client_email", "client_id"]
        
        missing = [f for f in required_fields if f not in credentials_dict]
        if missing:
            st.error(f"Missing credential fields: {', '.join(missing)}")
            st.stop()
            
        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict,
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        
    genai.configure(api_key=google_api_key)
except Exception as e:
    st.error(f"Initialization error: {str(e)}")
    st.stop()

# Validate services
if not credentials:
    st.error("❌ Google Cloud credentials not configured")
    st.stop()

if not google_api_key:
    st.error("❌ Google API key missing")
    st.stop()

# Configure AI model
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

# ========== SIDEBAR ==========
with st.sidebar:
    st.title("🧠 AI Assistant")
    
    # Chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    sidebar_query = st.chat_input("Ask coding questions...")
    if sidebar_query and MODEL:
        # Add user question to history
        st.session_state.chat_history.append({
            "role": "user",
            "content": sidebar_query
        })
        
        # Generate response
        try:
            response = MODEL.generate_content(sidebar_query)
            if response.text:
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response.text
                })
                st.rerun()
        except Exception as e:
            st.error(f"Error generating response: {str(e)}")
    
    st.markdown("---")
    st.subheader("💡 Usage Tips")
    st.markdown("""
    1. Upload clear code images
    2. Review analysis sections
    3. Ask follow-up questions
    4. Implement suggestions
    """)
    
    st.markdown("---")
    st.subheader("📝 Feedback")
    feedback = st.text_area("Help us improve:")
    if st.button("Send Feedback"):
        st.success("Thank you for your feedback!")

# ========== MAIN CONTENT ==========
st.title("🛠️ AI-Powered Code Debugger")

def analyze_code(code: str, language: str) -> Dict:
    """Analyze code with enhanced JSON parsing"""
    try:
        prompt = f"""**CODE ANALYSIS REQUEST**
Analyze this {language} code and provide output in EXACTLY this JSON format:
{{
    "bugs": ["list of bugs with line numbers"],
    "fixes": ["specific fixes"],
    "corrected_code": "full corrected code as string",
    "optimizations": ["performance improvements"],
    "explanation": ["technical explanations"]
}}

**RULES:**
1. Output ONLY valid JSON
2. No markdown formatting
3. Escape double quotes
4. No comments
5. Validate JSON syntax

**CODE:**
{code}
"""
        response = MODEL.generate_content(prompt)
        
        if not response.text:
            return {"error": "❌ Empty AI response"}

        # Enhanced cleaning
        raw_response = response.text.strip()
        cleaned = re.sub(r'^```json\s*|\s*```\s*$', '', raw_response, flags=re.IGNORECASE)
        
        try:
            parsed = json.loads(cleaned)
            required_keys = {"bugs", "fixes", "corrected_code", 
                            "optimizations", "explanation"}
            
            if not required_keys.issubset(parsed.keys()):
                missing = required_keys - parsed.keys()
                return {"error": f"❌ Missing keys: {', '.join(missing)}"}
                
            return parsed
            
        except json.JSONDecodeError as jde:
            return {"error": f"❌ JSON Error: {str(jde)}\nContext: {cleaned[:200]}..."}
            
    except Exception as e:
        return {"error": f"❌ Analysis failed: {str(e)}"}

def extract_code_from_image(image) -> str:
    """Extract code from image with error handling"""
    try:
        client = vision.ImageAnnotatorClient(credentials=credentials)
        content = image.read()
        img = vision.Image(content=content)
        response = client.text_detection(image=img)
        
        if response.error.message:
            return f"⚠️ Vision API Error: {response.error.message}"
            
        return response.text_annotations[0].description.strip() if response.text_annotations else "⚠️ No text detected"
        
    except Exception as e:
        return f"⚠️ OCR Error: {str(e)}"

# Input Methods
input_method = st.radio("Choose input method:", 
                       ["📷 Image", "📁 File", "📝 Paste"],
                       horizontal=True)

code_text = ""
language = "python"

# Handle Image Upload
if input_method == "📷 Image":
    img_file = st.file_uploader("Upload Code Image", type=["png", "jpg", "jpeg"])
    if img_file:
        code_text = extract_code_from_image(img_file)
        st.code(code_text, language="text")

# Handle File Upload
elif input_method == "📁 File":
    code_file = st.file_uploader("Upload Code File", type=["py", "java", "js"])
    if code_file:
        code_text = code_file.read().decode("utf-8")
        ext = code_file.name.split(".")[-1]
        language = {"py": "python", "java": "java", "js": "javascript"}.get(ext, "text")
        st.code(code_text, language=language)

# Handle Paste Code
else:
    code_text = st.text_area("Paste Code Here:", height=300)
    if code_text:
        st.code(code_text, language="text")

# Analysis
if st.button("🚀 Analyze Code") and code_text.strip():
    st.session_state.current_code = code_text
    with st.spinner("🔍 Analyzing..."):
        st.session_state.analysis_results = analyze_code(code_text, language)

# Display Results
if st.session_state.analysis_results:
    results = st.session_state.analysis_results
    
    if "error" in results:
        st.error(results["error"])
    else:
        st.subheader("🔍 Analysis Results")
        
        with st.expander("🐛 Bugs", expanded=True):
            for bug in results.get("bugs", []):
                st.error(f"- {bug}")
        
        with st.expander("🛠️ Fixes"):
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
