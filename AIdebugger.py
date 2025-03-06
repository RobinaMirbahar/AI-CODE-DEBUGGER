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
# Corrected Initialization
# ======================
def initialize_debugger():
    """Proper API configuration to fix 404 errors"""
    try:
        if "GEMINI_API_KEY" not in st.secrets:
            raise ValueError("Missing GEMINI_API_KEY in secrets")

        # Correct API endpoint configuration
        genai.configure(
            api_key=st.secrets["GEMINI_API_KEY"],
            transport='rest',
            client_options={
                'api_endpoint': 'https://generativelanguage.googleapis.com/'  # Base URL
            }
        )
        
        # Use latest model name
        return genai.GenerativeModel('gemini-1.0-pro')
        
    except Exception as e:
        st.error(f"🔧 Initialization Failed: {str(e)}")
        st.stop()

model = initialize_debugger()

# ======================
# Core Debugging Logic
# ======================
def debug_code(code: str, language: str) -> dict:
    """Execute debugging with error handling"""
    try:
        response = model.generate_content(
            DEBUG_PROMPT.format(language=language, code=code),
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,
                max_output_tokens=4000,
                response_mime_type="application/json"
            )
        )
        
        if not response.text:
            raise ValueError("Empty API response")
            
        return parse_debug_response(response.text)
        
    except Exception as e:
        return {"error": f"API Error: {str(e)}"}

def parse_debug_response(response: str) -> dict:
    """Validate and parse response"""
    try:
        json_str = re.search(r'\{.*\}', response, re.DOTALL)
        if not json_str:
            raise ValueError("No JSON found in response")
            
        debug_data = json.loads(json_str.group())
        
        # Structure validation
        required = {
            "metadata": ["analysis_time", "complexity"],
            "errors": ["line", "type", "description", "fix"],
            "corrected_code": str,
            "warnings": list
        }
        
        for category, keys in required.items():
            if not all(key in debug_data.get(category, {}) for key in keys):
                raise ValueError(f"Invalid {category} structure")
                
        return debug_data
        
    except Exception as e:
        return {"error": f"Parsing failed: {str(e)}"}

# ======================
# Streamlit Interface
# ======================
def main():
    st.set_page_config(page_title="AI Code Debugger", layout="wide")
    st.title("🤖 Code Debugger Pro")
    
    code = st.text_area("Input Code:", height=300)
    language = st.selectbox("Language:", ["python", "javascript", "java"])
    
    if st.button("Debug Code"):
        if not code.strip():
            st.warning("Please enter code to debug")
            return
            
        with st.spinner("Analyzing..."):
            try:
                start = time.time()
                result = debug_code(code, language)
                elapsed = time.time() - start
                
                if "error" in result:
                    st.error(f"Error: {result['error']}")
                else:
                    display_results(result, language)
                    
            except Exception as e:
                st.error(f"Unexpected error: {str(e)}")

def display_results(data: dict, language: str):
    """Show debugging results"""
    st.subheader("🔍 Analysis Report")
    
    # Metadata
    with st.expander("📊 Metrics"):
        cols = st.columns(3)
        cols[0].metric("Complexity", data['metadata']['complexity'].upper())
        cols[1].metric("Issues Found", len(data['errors']))
        cols[2].metric("Warnings", len(data['warnings']))
    
    # Errors
    st.subheader("🚨 Identified Issues")
    for error in data['errors']:
        st.markdown(f"""
        **Line {error['line']}** ({error['type']}):
        ```diff
        - Problem: {error['description']}
        + Fix: {error['fix']}
        """)
    
    # Corrected Code
    st.subheader("✅ Corrected Implementation")
    st.code(data['corrected_code'], language=language.lower())
    
    # Warnings
    if data['warnings']:
        st.subheader("⚠️ Important Notes")
        for warning in data['warnings']:
            st.warning(warning)

if __name__ == "__main__":
    main()
