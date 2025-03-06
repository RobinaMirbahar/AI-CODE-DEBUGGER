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

Return strict JSON format:
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
# API Initialization
# ======================
def initialize_gemini():
    """Properly configured Gemini client with error handling"""
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
        
        # Verify model availability
        model = genai.GenerativeModel('gemini-pro')
        return model
        
    except Exception as e:
        st.error(f"🔌 Connection Failed: {str(e)}")
        st.stop()

model = initialize_gemini()

# ======================
# Debugging Core
# ======================
def debug_code(code: str, language: str) -> dict:
    """Execute code analysis with retry logic"""
    for attempt in range(3):
        try:
            response = model.generate_content(
                DEBUG_PROMPT.format(language=language, code=code),
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=4000,
                    response_mime_type="application/json"
                )
            )
            return validate_response(response.text)
            
        except genai.types.StopCandidateException as e:
            return {"error": f"Content blocked: {str(e)}"}
        except Exception as e:
            if attempt == 2:
                return {"error": f"Failed after 3 attempts: {str(e)}"}
            time.sleep(1.5 ** (attempt + 1))
            
    return {"error": "Unexpected error"}

def validate_response(response_text: str) -> dict:
    """Validate and sanitize API response"""
    try:
        # Extract JSON from potential markdown
        json_match = re.search(r'```json\n(.*?)\n```', response_text, re.DOTALL)
        if not json_match:
            raise ValueError("No JSON found in response")
            
        response_data = json.loads(json_match.group(1))
        
        # Validate response structure
        required_structure = {
            "metadata": ["analysis_time", "complexity"],
            "issues": ["syntax_errors", "logical_errors", "security_issues"],
            "improvements": ["corrected_code", "optimizations", "security_fixes"]
        }
        
        for category, keys in required_structure.items():
            if not all(key in response_data.get(category, {}) for key in keys):
                raise ValueError(f"Invalid {category} structure")
                
        return response_data
        
    except Exception as e:
        return {"error": f"Response validation failed: {str(e)}"}

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
    st.markdown("---")
    
    # Code Input Section
    code = st.text_area("Paste your code:", height=300, 
                       placeholder="// Your code here...")
    language = st.selectbox("Select Language:", 
                           ["python", "javascript", "java", "c++"])
    
    if st.button("Analyze Code", type="primary"):
        if not code.strip():
            st.warning("Please input some code to analyze")
            return
            
        with st.spinner("🔍 Deep analysis in progress..."):
            start_time = time.time()
            result = debug_code(code, language)
            analysis_time = time.time() - start_time
            
            if "error" in result:
                st.error(f"Analysis Failed: {result['error']}")
            else:
                display_results(result, language, analysis_time)

def display_results(data: dict, lang: str, time_taken: float):
    """Interactive results display"""
    st.markdown("---")
    st.subheader("📊 Analysis Report")
    
    # Metadata Columns
    col1, col2, col3 = st.columns(3)
    col1.metric("Analysis Time", f"{time_taken:.2f}s")
    col2.metric("Code Complexity", data['metadata']['complexity'].upper())
    col3.metric("Total Issues", 
               len(data['issues']['syntax_errors']) + 
               len(data['issues']['logical_errors']) + 
               len(data['issues']['security_issues']))
    
    # Issues Panel
    with st.expander("🚨 Detailed Issues", expanded=True):
        tab1, tab2, tab3 = st.tabs(["Syntax Errors", "Logical Errors", "Security Issues"])
        
        with tab1:
            if data['issues']['syntax_errors']:
                for err in data['issues']['syntax_errors']:
                    st.markdown(f"""
                    **Line {err['line']}**:
                    ```diff
                    - {err['message']}
                    + Fix: {err['fix']}
                    """)
            else:
                st.success("No syntax errors found!")
                
        with tab2:
            if data['issues']['logical_errors']:
                for err in data['issues']['logical_errors']:
                    st.markdown(f"""
                    **Line {err['line']}**:
                    ```diff
                    - {err['message']}
                    + Fix: {err['fix']}
                    """)
            else:
                st.info("No logical errors detected")
                
        with tab3:
            if data['issues']['security_issues']:
                for err in data['issues']['security_issues']:
                    st.markdown(f"""
                    **Line {err['line']}**:
                    ```diff
                    - {err['message']}
                    + Fix: {err['fix']}
                    """)
            else:
                st.success("No security vulnerabilities found!")

    # Improvements Panel
    with st.expander("✨ Optimization Suggestions", expanded=True):
        st.subheader("Improved Code")
        st.code(data['improvements']['corrected_code'], language=lang)
        
        if data['improvements']['optimizations']:
            st.subheader("Performance Optimizations")
            for opt in data['improvements']['optimizations']:
                st.markdown(f"✅ {opt}")
                
        if data['improvements']['security_fixes']:
            st.subheader("Security Enhancements")
            for fix in data['improvements']['security_fixes']:
                st.markdown(f"🔒 {fix}")

if __name__ == "__main__":
    main()
