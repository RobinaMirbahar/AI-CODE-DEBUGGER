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
  "metadata": {{
    "analysis_time": float,
    "complexity": "low/medium/high"
  }},
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
# Corrected API Setup
# ======================
def initialize_debugger():
    """Proper API configuration with valid endpoints"""
    try:
        if "GEMINI_API_KEY" not in st.secrets:
            raise ValueError("Missing GEMINI_API_KEY in secrets")

        # Correct API configuration
        genai.configure(
            api_key=st.secrets["GEMINI_API_KEY"],
            transport='rest',
            client_options={
                'api_endpoint': 'https://generativelanguage.googleapis.com/v1'  # Single API version
            }
        )
        
        # Use latest validated model
        return genai.GenerativeModel('gemini-1.0-pro')
        
    except Exception as e:
        st.error(f"🔌 Connection Failed: {str(e)}")
        st.stop()

model = initialize_debugger()

# ======================
# Debugging Core (Updated)
# ======================
def debug_code(code: str, language: str) -> dict:
    """Execute code analysis with proper endpoint"""
    try:
        response = model.generate_content(
            DEBUG_PROMPT.format(language=language, code=code),
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,
                max_output_tokens=4000,
                response_mime_type="application/json"
            )
        )
        
        # Debug: Print raw API response
        st.write("API Response:", response.text)  # For troubleshooting
        
        return validate_response(response.text)
        
    except Exception as e:
        return {"error": f"API Error: {str(e)}"}

def validate_response(response_text: str) -> dict:
    """Validate API response structure"""
    try:
        # Handle different JSON formats
        json_str = re.search(r'\{.*\}', response_text, re.DOTALL)
        if not json_str:
            raise ValueError("No JSON found in response")
            
        response_data = json.loads(json_str.group())
        
        # Required structure validation
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
    st.set_page_config(
        page_title="AI Code Debugger Pro",
        page_icon="🐞",
        layout="wide"
    )
    
    st.title("🐞 AI Code Debugger Pro")
    code = st.text_area("Input Code:", height=300)
    language = st.selectbox("Language:", ["python", "javascript", "java"])
    
    if st.button("Analyze Code"):
        if not code.strip():
            st.warning("Please input code to analyze")
            return
            
        with st.spinner("Analyzing..."):
            start = time.time()
            result = debug_code(code, language.lower())
            elapsed = time.time() - start
            
            if "error" in result:
                st.error(f"Error: {result['error']}")
            else:
                display_results(result, language.lower())

def display_results(data: dict, lang: str):
    """Display analysis results"""
    st.subheader("📊 Analysis Report")
    
    # Metadata
    cols = st.columns(3)
    cols[0].metric("Complexity", data['metadata']['complexity'].upper())
    cols[1].metric("Analysis Time", f"{data['metadata']['analysis_time']:.2f}s")
    cols[2].metric("Total Issues", 
                  len(data['issues']['syntax_errors']) + 
                  len(data['issues']['logical_errors']) + 
                  len(data['issues']['security_issues']))
    
    # Issues
    with st.expander("🚨 Detailed Issues"):
        st.subheader("Syntax Errors")
        for err in data['issues']['syntax_errors']:
            st.markdown(f"**Line {err['line']}:** {err['message']}")
            st.code(f"Fix: {err['fix']}", language=lang)
            
        st.subheader("Logical Errors")
        for err in data['issues']['logical_errors']:
            st.markdown(f"**Line {err['line']}:** {err['message']}")
            st.code(f"Fix: {err['fix']}", language=lang)
            
        st.subheader("Security Issues")
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
        st.subheader("🔒 Security Fixes")
        for fix in data['improvements']['security_fixes']:
            st.markdown(f"- {fix}")

if __name__ == "__main__":
    main()
