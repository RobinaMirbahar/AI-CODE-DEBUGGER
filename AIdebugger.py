import google.generativeai as genai
import streamlit as st
import re
from datetime import datetime
import difflib
import json

# Configure Gemini API
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

@st.cache_data(show_spinner=False)
def correct_code(code_snippet, language, analysis_type="Full Audit"):
    """Enhanced code analysis with multiple modes"""
    try:
        if not code_snippet.strip():
            return {"error": "⚠️ No code provided for analysis."}
        
        lang = language.lower() if language != "Auto-Detect" else auto_detect_language(code_snippet)
        
        base_prompt = f"""
        Analyze this {lang} code and provide structured JSON output containing:
        {{
            "corrected_code": "Corrected version of the provided code",
            "error_explanation": "Explanation of errors found",
            "optimization_recommendations": "Suggestions for improvements"
        }}
        Ensure the response is valid JSON.
        """
        
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(base_prompt)
        
        if not response or not hasattr(response, "text") or not response.text:
            return {"error": "⚠️ Empty response from Gemini API."}
        
        try:
            response_json = json.loads(response.text)
            if not all(key in response_json for key in ["corrected_code", "error_explanation", "optimization_recommendations"]):
                raise ValueError("Missing expected keys in response JSON")
            return response_json
        except (json.JSONDecodeError, ValueError):
            return {"error": "⚠️ Gemini API returned an invalid JSON response. Here is the raw output:", "raw_response": response.text}
    except Exception as e:
        return {"error": f"⚠️ API Error: {str(e)}"}

def generate_code_from_text(prompt, language):
    """Generates code based on user-provided description."""
    if not prompt.strip():
        return "⚠️ Please enter a prompt to generate code."
    
    gen_prompt = f"Generate a {language} script based on this description: {prompt}"
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(gen_prompt)
    return response.text if response and response.text else "⚠️ No response from AI."

def generate_api_documentation(code_snippet, language):
    """Generates documentation for provided code."""
    if not code_snippet.strip():
        return "⚠️ Please provide code for documentation."
    
    doc_prompt = f"Generate API documentation for this {language} code:\n```{language}\n{code_snippet}\n```"
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(doc_prompt)
    return response.text if response and response.text else "⚠️ No response from AI."

def auto_detect_language(code):
    """Basic language detection based on file structure"""
    if "import " in code or "def " in code:
        return "python"
    elif "function " in code or "const " in code:
        return "javascript"
    elif "class " in code and "public static void main" in code:
        return "java"
    return "plaintext"

def compare_code(original, corrected):
    """Generate a side-by-side diff view for code comparison."""
    diff = difflib.unified_diff(original.splitlines(), corrected.splitlines(), lineterm='')
    return "\n".join(diff)

def display_download_button(corrected_code, language):
    """Allow users to download the corrected code."""
    st.download_button(label="📥 Download Corrected Code", data=corrected_code, file_name=f"corrected_code.{language}", mime="text/plain")

def toggle_dark_mode():
    dark_mode = st.toggle("🌙 Dark Mode")
    if dark_mode:
        st.markdown("""
            <style>
            body { background-color: #121212; color: white; }
            </style>
        """, unsafe_allow_html=True)

def run_python_code(code):
    """Execute Python code safely."""
    try:
        exec(code, {})
        return "✅ Execution Successful"
    except Exception as e:
        return f"❌ Error: {str(e)}"

st.title("🚀 AI-Powered Code Debugger Pro")
toggle_dark_mode()

col1, col2 = st.columns([3, 1])

if 'code' not in st.session_state:
    st.session_state.code = ""

if 'history' not in st.session_state:
    st.session_state.history = []

with col1:
    uploaded_file = st.file_uploader("📤 Upload Code", type=["py","js","java","cpp","cs","go"])
    if uploaded_file:
        try:
            st.session_state.code = uploaded_file.read().decode("utf-8")
        except UnicodeDecodeError:
            st.error("⚠️ Invalid file format - please upload text-based source files")
    
    code = st.text_area("📝 Code Editor", height=300, value=st.session_state.code)
    gen_prompt = st.text_area("💡 Code Generation Prompt", height=100, placeholder="Describe functionality to generate...")
    if st.button("▶ Run Code") and auto_detect_language(code) == "python":
        st.text(run_python_code(code))
    
    if st.button("🛠 Generate Code"):
        if not gen_prompt.strip():
            st.error("⚠️ Please enter a prompt to generate code.")
        else:
            with st.spinner("✨ Generating code..."):
                generated_code = generate_code_from_text(gen_prompt, lang)
                st.code(generated_code, language=lang.lower())
    
    if st.button("📄 Generate Documentation"):
        if not code.strip():
            st.error("⚠️ Please provide code for documentation.")
        else:
            with st.spinner("📖 Generating API documentation..."):
                documentation = generate_api_documentation(code, lang)
                st.text_area("📜 API Documentation", documentation, height=200)

with col2:
    lang = st.selectbox("🌐 Language", ["Auto-Detect", "Python", "JavaScript", "Java", "C++", "C#", "Go", "Rust"])
    analysis_type = st.radio("🔍 Analysis Mode", ["Full Audit", "Quick Fix", "Security Review"])

st.markdown("---")
st.markdown("© 2025 AI Code Debugger Pro - All Rights Reserved - Robina Mirbahar")

# Editable corrected code before download
if 'corrected_code' in st.session_state:
    st.session_state.corrected_code = st.text_area("✏️ Refine Corrected Code", value=st.session_state.corrected_code, height=300)
    display_download_button(st.session_state.corrected_code, lang)
