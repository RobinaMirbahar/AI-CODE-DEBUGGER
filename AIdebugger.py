import streamlit as st
import google.generativeai as genai
import json
import re
import time

# ======================
# Configuration
# ======================
DEBUG_PROMPT = """Analyze and debug this {language} code with:
1. Line-specific error identification
2. Runtime behavior analysis
3. Security vulnerability detection
4. Performance optimization
5. Corrected implementation

Return strict JSON format:
{{
  "metadata": {{
    "analysis_time": float,
    "complexity": string
  }},
  "errors": [
    {{
      "line": int,
      "type": string,
      "description": string,
      "fix": string
    }}
  ],
  "corrected_code": string,
  "warnings": [string]
}}"""

# ======================
# Gemini Initialization
# ======================
def initialize_debugger():
    """Configure Gemini debugger engine"""
    try:
        if "GEMINI_API_KEY" not in st.secrets:
            raise ValueError("Missing GEMINI_API_KEY in secrets")
            
        genai.configure(
            api_key=st.secrets["GEMINI_API_KEY"],
            transport='rest',
            client_options={
                'api_endpoint': 'https://generativelanguage.googleapis.com/v1beta'
            }
        )
        return genai.GenerativeModel('gemini-1.0-pro')
    except Exception as e:
        st.error(f"🔧 Debugger Initialization Failed: {str(e)}")
        st.stop()

model = initialize_debugger()

# ======================
# Core Debugging Logic
# ======================
def debug_code(code: str, language: str) -> dict:
    """Execute AI-powered debugging"""
    try:
        response = model.generate_content(
            DEBUG_PROMPT.format(language=language, code=code),
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,
                max_output_tokens=4000,
                response_mime_type="application/json"
            )
        )
        return parse_debug_response(response.text)
    except Exception as e:
        return {"error": f"Debugging failed: {str(e)}"}

def parse_debug_response(response: str) -> dict:
    """Process and validate debug output"""
    try:
        json_str = re.search(r'```json\n(.*?)\n```', response, re.DOTALL)
        if not json_str:
            raise ValueError("No JSON found in response")
            
        debug_data = json.loads(json_str.group(1))
        
        # Validate response structure
        required_keys = {
            "metadata": ["analysis_time", "complexity"],
            "errors": ["line", "type", "description", "fix"],
            "corrected_code": str,
            "warnings": list
        }
        
        for category, keys in required_keys.items():
            if not all(key in debug_data.get(category, {}) for key in keys):
                raise ValueError(f"Missing {category} data")
                
        return debug_data
    except Exception as e:
        return {"error": f"Response parsing failed: {str(e)}"}

# ======================
# Streamlit Interface
# ======================
def main():
    st.set_page_config(page_title="AI Code Debugger", layout="wide")
    st.title("🤖 Google Gemini Code Debugger")
    
    code = st.text_area("Input Code:", height=300)
    language = st.selectbox("Language:", ["python", "javascript", "java", "c++"])
    
    if st.button("Debug Code"):
        if not code.strip():
            st.warning("Please enter code to debug")
            return
            
        with st.spinner("🔍 Analyzing code..."):
            start = time.time()
            result = debug_code(code, language.lower())
            elapsed = time.time() - start
            
            if "error" in result:
                st.error(f"🚨 {result['error']}")
            else:
                display_results(result, elapsed, language.lower())

def display_results(data: dict, time_taken: float, language: str):
    """Visualize debugging results"""
    st.subheader("📊 Debug Report")
    
    # Metadata columns
    col1, col2, col3 = st.columns(3)
    col1.metric("Analysis Time", f"{time_taken:.2f}s")
    col2.metric("Code Complexity", data['metadata']['complexity'].upper())
    col3.metric("Issues Found", len(data['errors']))
    
    # Errors section
    st.subheader("🚨 Code Issues")
    for error in data['errors']:
        with st.expander(f"Line {error['line']}: {error['type']}", expanded=True):
            st.markdown(f"""
            **Description**: {error['description']}
            ```diff
            - Problem: {error['description'].split('.')[0]} 
            + Fix: {error['fix']}
            """)
    
    # Corrected code
    st.subheader("✅ Optimized Code")
    st.code(data['corrected_code'], language=language)
    
    # Warnings
    if data['warnings']:
        st.subheader("⚠️ Important Notes")
        for warning in data['warnings']:
            st.warning(warning)

if __name__ == "__main__":
    main()
