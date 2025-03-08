import os
import streamlit as st
import google.generativeai as genai
import json
import re
import time

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
}}"""

# ======================
# API Setup
# ======================
def initialize_debugger():
    """Proper API configuration with valid endpoints"""
    try:
        # Fetch API key from Streamlit secrets or environment variables
        if "GEMINI" in st.secrets:
            api_key = st.secrets["GEMINI"]["api_key"]
        else:
            api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            st.error("❌ Missing API Key! Check your `.streamlit/secrets.toml` or environment variables.")
            st.stop()

        # Configure Generative AI API
        genai.configure(api_key=api_key)

        # Use the correct model version
        return genai.GenerativeModel('gemini-1.5-pro')

    except Exception as e:
        st.error(f"🔌 Connection Failed: {str(e)}")
        st.stop()

# Initialize the model
model = initialize_debugger()
if model is None:
    st.error("❌ Failed to initialize the model. Check your API key and configuration.")
    st.stop()

# ======================
# Debugging Core
# ======================
def debug_code(code: str, language: str) -> dict:
    """Execute code analysis with proper API calls"""
    try:
        # Generate the prompt for debugging
        prompt = DEBUG_PROMPT.format(language=language, code=code)
        
        # Send the prompt to the model
        response = model.generate_content(prompt)
        
        # Print raw response for debugging
        print("Raw API Response:", response.text)

        # Validate and parse the response
        return validate_response(response.text)

    except Exception as e:
        return {"error": f"API Error: {str(e)}"}

def validate_response(response_text: str) -> dict:
    """Validate and parse API response JSON"""
    try:
        # Extract JSON from the response
        json_str = re.search(r'\{.*\}', response_text, re.DOTALL)
        if not json_str:
            print("⚠️ No JSON found in response. Full Response:", response_text)
            return {"error": "API response is not in JSON format"}

        # Parse JSON
        response_data = json.loads(json_str.group())

        # Ensure expected keys are present
        required_keys = {
            "metadata": ["analysis_time", "complexity"],
            "issues": ["syntax_errors", "logical_errors", "security_issues"],
            "improvements": ["corrected_code", "optimizations", "security_fixes"]
        }

        for category, keys in required_keys.items():
            if not all(key in response_data.get(category, {}) for key in keys):
                raise ValueError(f"Invalid {category} structure")

        return response_data

    except Exception as e:
        return {"error": f"Validation failed: {str(e)}"}

# ======================
# Streamlit Interface
# ======================
def main():
    st.set_page_config(page_title="AI Code Debugger Pro", page_icon="🐞", layout="wide")
    st.title("🐞 AI Code Debugger Pro")
    st.write("Analyze and debug your code using Gemini AI.")

    # Input fields
    code = st.text_area("📜 Paste your code here:", height=300)
    language = st.selectbox("🌐 Select Programming Language:", ["python", "javascript", "java"])

    # Analyze button
    if st.button("🚀 Analyze Code"):
        if not code.strip():
            st.warning("⚠️ Please input some code to analyze.")
            return

        with st.spinner("🔍 Analyzing..."):
            start = time.time()
            result = debug_code(code, language.lower())
            elapsed = time.time() - start

            if "error" in result:
                st.error(f"❌ Error: {result['error']}")
            else:
                display_results(result, language.lower(), elapsed)


    
    # Detailed Issues
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

    # Corrected Code
    st.subheader("✅ Corrected Code")
    st.code(data['improvements']['corrected_code'], language=lang)

    # Optimizations
    if data['improvements']['optimizations']:
        st.subheader("🚀 Optimizations")
        for opt in data['improvements']['optimizations']:
            st.markdown(f"- {opt}")

    # Security Fixes
    if data['improvements']['security_fixes']:
        st.subheader("🔐 Security Fixes")
        for fix in data['improvements']['security_fixes']:
            st.markdown(f"- {fix}")

if __name__ == "__main__":
    main()
