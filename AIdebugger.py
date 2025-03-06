import streamlit as st
from openai import OpenAI  # Using OpenAI client format
import base64
import json
import re
import time

# ======================
# Configuration
# ======================
CLIENT_CONFIG = {
    "api_key": st.secrets.GEMINI.api_key,
    "base_url": "https://generativelanguage.googleapis.com/v1beta/models/"
}

ANALYSIS_PROMPT = """Analyze this {language} code and provide detailed feedback:
1. Syntax errors with line numbers
2. Logical errors with explanations
3. Performance optimizations
4. Security vulnerabilities

Return structured JSON response."""

# ======================
# Client Initialization
# ======================
def initialize_client():
    """Create configured client instance"""
    try:
        return OpenAI(**CLIENT_CONFIG)
    except Exception as e:
        st.error(f"Client initialization failed: {str(e)}")
        st.stop()

client = initialize_client()

# ======================
# Analysis Functions
# ======================
def analyze_code(code, language):
    """Analyze code using OpenAI client format"""
    try:
        response = client.chat.completions.create(
            model="gemini-1.5-pro-latest",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": ANALYSIS_PROMPT.format(language=language)},
                        {"type": "text", "text": f"Code:\n```{language}\n{code}\n```"}
                    ]
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=4000
        )
        
        return parse_response(response.choices[0].message.content)
        
    except Exception as e:
        return {"error": f"Analysis failed: {str(e)}"}

def parse_response(response_text):
    """Parse and validate JSON response"""
    try:
        response_data = json.loads(response_text)
        
        # Validate response structure
        required_keys = {
            'issues': ['syntax_errors', 'logical_errors', 'security_issues'],
            'improvements': ['corrected_code', 'optimizations', 'security_fixes']
        }
        
        for category, keys in required_keys.items():
            if not all(key in response_data.get(category, {}) for key in keys):
                raise ValueError("Invalid response structure")
                
        return response_data
        
    except Exception as e:
        return {"error": f"Response parsing failed: {str(e)}"}

# ======================
# Streamlit UI
# ======================
def main():
    st.set_page_config(page_title="AI Code Analyzer", layout="wide")
    st.title("🧠 AI Code Analyzer (Gemini)")
    
    code_input = st.text_area("Paste your code:", height=300)
    language = st.selectbox("Select language:", ["python", "javascript", "java"])
    
    if st.button("Analyze Code"):
        with st.spinner("Analyzing..."):
            start_time = time.time()
            result = analyze_code(code_input, language)
            analysis_time = time.time() - start_time
            
            if "error" in result:
                st.error(result["error"])
            else:
                display_results(result, analysis_time)

def display_results(result, time_taken):
    """Render analysis results"""
    st.subheader("Analysis Results")
    st.write(f"Analysis completed in {time_taken:.2f} seconds")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.header("🚨 Issues")
        with st.expander("Syntax Errors"):
            st.json(result["issues"]["syntax_errors"])
            
        with st.expander("Logical Errors"):
            st.json(result["issues"]["logical_errors"])
            
    with col2:
        st.header("✨ Improvements")
        with st.expander("Corrected Code"):
            st.code(result["improvements"]["corrected_code"])
            
        with st.expander("Optimizations"):
            st.json(result["improvements"]["optimizations"])

if __name__ == "__main__":
    main()
