import os
import streamlit as st
import google.generativeai as genai
import json
import re
import time
from pygments.lexers import guess_lexer, PythonLexer

# ======================
# Configuration
# ======================
DEBUG_PROMPT = """Analyze and debug this {language} code:
{code}

Return JSON format:
{{
  "metadata": {{"analysis_time": float, "complexity": "low/medium/high"}},
  "issues": {{
    "syntax_errors": [{{"line": int, "message": str, "fix": str}}],
    "logical_errors": [{{"line": int, "message": str, "fix": str}}],
    "security_issues": [{{"line": int, "message": str, "fix": str}}]
  }},
  "improvements": {{
    "corrected_code": str,
    "optimizations": [str],
    "security_fixes": [str]
  }}
}}

IMPORTANT: Return ONLY valid JSON. Do not include any additional text or explanations."""

# ======================
# API Setup
# ======================
def initialize_debugger():
    """Proper API configuration with valid endpoints"""
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            st.error("❌ Missing API Key! Set GEMINI_API_KEY as an environment variable.")
            st.stop()
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-1.5-pro')
    except Exception as e:
        st.error(f"🔌 Connection Failed: {str(e)}")
        st.stop()

# ======================
# Debugging Core
# ======================
def debug_code(code: str, language: str, model) -> dict:
    """Execute code analysis with API calls"""
    for attempt in range(3):
        try:
            prompt = DEBUG_PROMPT.format(language=language, code=code)
            response = model.generate_content(prompt)
            return validate_response(response.text)
        except Exception as e:
            if attempt == 2:
                return {"error": f"API Error: {str(e)}"}
            time.sleep(2)

def validate_response(response_text: str) -> dict:
    """Validate and parse API response JSON"""
    try:
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if not json_match:
            return {"error": "No valid JSON found in API response"}
        json_str = json_match.group().strip()
        response_data = json.loads(json_str)
        return response_data
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON format: {str(e)}"}

# ======================
# Auto-Detect Language
# ======================
def detect_language(code: str, selected_language: str) -> str:
    """Detect the programming language or fallback to user selection"""
    try:
        lexer = guess_lexer(code)
        return "python" if isinstance(lexer, PythonLexer) else lexer.name.lower()
    except Exception:
        return selected_language.lower()

# ======================
# Streamlit Interface
# ======================
def main():
    st.set_page_config(page_title="AI Code Debugger Pro", page_icon="🐞", layout="wide")
    st.title("🐞 AI Code Debugger Pro")
    st.write("Analyze and debug your code using Gemini AI.")

    model = initialize_debugger()
    if model is None:
        st.stop()

    uploaded_file = st.file_uploader("📤 Upload a code file", type=["py", "js", "java", "cpp", "cs", "go"])
    code = uploaded_file.read().decode("utf-8") if uploaded_file else st.text_area("📜 Paste your code here:", height=300)

    language = st.selectbox("🌐 Select Programming Language:", ["Auto-Detect", "python", "javascript", "java", "cpp", "cs", "go"])
    if language == "Auto-Detect":
        language = detect_language(code, language)
        st.write(f"🔍 Detected Language: **{language.capitalize()}**")

    if st.button("🚀 Analyze Code"):
        if not code.strip():
            st.warning("⚠️ Please input some code to analyze.")
            return
        with st.spinner("🔍 Analyzing..."):
            result = debug_code(code, language.lower(), model)
            if "error" in result:
                st.error(f"❌ Error: {result['error']}")
            else:
                display_results(result, language.lower())

# ======================
# Display Results
# ======================
def display_results(data: dict, lang: str):
    """Display analysis results"""
    st.subheader("📊 Metadata")
    st.write(f"**Analysis Time:** {data['metadata']['analysis_time']:.2f} seconds")
    st.write(f"**Code Complexity:** {data['metadata']['complexity'].capitalize()}")

    with st.expander("🚨 Detailed Issues"):
        st.subheader("🔴 Syntax Errors")
        for err in data['issues']['syntax_errors']:
            st.markdown(f"**Line {err['line']}:** {err['message']}")
            st.code(f"Fix: {err['fix']}", language=lang)
        st.subheader("🟠 Logical Errors")
        for err in data['issues']['logical_errors']:
            st.markdown(f"**Line {err['line']}:** {err['message']}")
            st.code(f"Fix: {err['fix']}", language=lang)
        st.subheader("🔒 Security Issues")
        for err in data['issues']['security_issues']:
            st.markdown(f"**Line {err['line']}:** {err['message']}")
            st.code(f"Fix: {err['fix']}", language=lang)
    
    st.subheader("✅ Corrected Code")
    st.code(data['improvements']['corrected_code'], language=lang)

if __name__ == "__main__":
    main()
