import streamlit as st
import json
import os
import google.generativeai as genai
from google.cloud import vision
from google.oauth2 import service_account
from typing import Dict, List

# === MUST BE FIRST STREAMLIT COMMAND ===
st.set_page_config(page_title="AI Code Debugger", layout="wide")
# =======================================

# === SESSION STATE INITIALIZATION ===
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = {}
if "current_code" not in st.session_state:
    st.session_state.current_code = ""

# === LOAD GOOGLE CLOUD CREDENTIALS ===
credentials = None
google_api_key = os.getenv("GOOGLE_API_KEY", st.secrets.get("GEMINI_API_KEY"))

try:
    if "gcp_service_account" in st.secrets:
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"]
        )
    elif os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON"):
        credentials = service_account.Credentials.from_service_account_info(
            json.loads(os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON"))
        )
    else:
        raise ValueError("❌ Missing Google Cloud Credentials")

    genai.configure(api_key=google_api_key)

except Exception as e:
    credentials = None
    st.error(f"❌ Configuration Error: {e}")
    st.stop()

# === CHECK API KEY ===
if not google_api_key:
    st.error("❌ Missing Google API Key")
    st.info("Set 'GEMINI_API_KEY' in Streamlit secrets or 'GOOGLE_API_KEY' in environment variables")
    st.stop()

# === CONFIGURE AI MODEL ===
MODEL = genai.GenerativeModel(
    "gemini-pro",
    safety_settings={
        "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
        "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
        "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
        "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
    },
    generation_config=genai.types.GenerationConfig(
        max_output_tokens=4000,
        temperature=0.25,
    ),
)

# === CODE ANALYSIS FUNCTION ===
def analyze_code(code: str, language: str) -> Dict:
    """Analyze code using Gemini AI"""
    try:
        prompt = f"""Analyze this {language} code and provide:
        1. List of bugs with line numbers
        2. Suggested fixes
        3. Corrected code
        4. Performance optimizations
        5. Detailed explanation

        Format response as JSON:
        {{
            "bugs": ["Bug descriptions"],
            "fixes": ["Fix explanations"],
            "corrected_code": "Fixed code",
            "optimizations": ["Optimization suggestions"],
            "explanation": ["Why these fixes were made"]
        }}

        Code:
        ```{language}
        {code}
        ```
        """

        response = MODEL.generate_content(prompt)
        return json.loads(response.text) if response.text else {"error": "❌ No AI response"}

    except json.JSONDecodeError:
        return {"error": "❌ Failed to parse AI response"}
    except Exception as e:
        return {"error": f"❌ Analysis failed: {str(e)}"}

# === IMAGE CODE EXTRACTION ===
def extract_code_from_image(image) -> str:
    """Extract code from image using Google Vision"""
    try:
        client = vision.ImageAnnotatorClient(credentials=credentials)
        content = image.read()
        response = client.text_detection(image=vision.Image(content=content))

        if response.error.message:
            return f"⚠️ Vision API Error: {response.error.message}"
        return response.text_annotations[0].description.strip() if response.text_annotations else "⚠️ No text detected"
    
    except Exception as e:
        return f"⚠️ OCR Error: {str(e)}"

# === STREAMLIT UI ===
st.title("🛠️ AI-Powered Code Debugger")

# === INPUT METHOD SELECTION ===
input_method = st.radio(
    "Choose input method:", ["📷 Image Upload", "📁 File Upload", "📝 Paste Code"], horizontal=True
)

code_text = ""
language = "python"

# === IMAGE UPLOAD HANDLING ===
if input_method == "📷 Image Upload":
    image_file = st.file_uploader("Upload an image containing code", type=["png", "jpg", "jpeg"])
    if image_file:
        code_text = extract_code_from_image(image_file)
        st.code(code_text, language="python")

# === FILE UPLOAD HANDLING ===
elif input_method == "📁 File Upload":
    code_file = st.file_uploader("Upload a code file", type=["py", "java", "js", "cpp"])
    if code_file:
        code_text = code_file.read().decode("utf-8")
        ext = code_file.name.split(".")[-1]
        language = {"py": "python", "java": "java", "js": "javascript", "cpp": "cpp"}.get(ext, "python")
        st.code(code_text, language=language)

# === PASTE CODE HANDLING ===
else:
    code_text = st.text_area("Paste your code here:", height=300)
    if code_text:
        st.code(code_text, language="python")

# === CODE ANALYSIS EXECUTION ===
if st.button("🚀 Analyze Code") and code_text.strip():
    st.session_state.current_code = code_text
    with st.spinner("🔍 Analyzing code..."):
        st.session_state.analysis_results = analyze_code(code_text, language)

# === DISPLAY RESULTS ===
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

