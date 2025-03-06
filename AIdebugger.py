import streamlit as st
import google.generativeai as genai
import json
import re
import time

# ======================
# Configuration
# ======================
DEBUG_PROMPT = """Act as a senior software engineer. Debug this {language} code:

**Required Output Format:**
{{
  "metadata": {{
    "execution_time": float,
    "code_complexity": "low/medium/high"
  }},
  "issues": {{
    "runtime_errors": [{{"line": int, "message": str, "fix": str}}],
    "logical_errors": [{{"line": int, "message": str, "fix": str}}],
    "potential_bugs": [{{"line": int, "message": str, "fix": str}}]
  }},
  "corrected_code": str
}}

**Code to Debug:**
```{language}
{code}
```"""

def initialize_debugger():
    """Configure AI model for debugging"""
    try:
        genai.configure(api_key=st.secrets.GEMINI_API_KEY)
        return genai.GenerativeModel('gemini-pro')
    except Exception as e:
        st.error(f"Debugger Initialization Failed: {str(e)}")
        st.stop()

model = initialize_debugger()

# ======================
# Core Debugging Logic
# ======================
def debug_code(code: str, language: str) -> dict:
    """Perform AI-powered code debugging"""
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
    """Parse and validate debug response"""
    try:
        # Extract JSON from markdown
        json_str = re.search(r'```json\n(.*?)\n```', response, re.DOTALL).group(1)
        debug_data = json.loads(json_str)
        
        # Validate structure
        required = {
            "metadata": ["execution_time", "code_complexity"],
            "issues": ["runtime_errors", "logical_errors", "potential_bugs"],
            "corrected_code": str
        }
        
        for category, keys in required.items():
            if not all(key in debug_data.get(category, {}) for key in keys):
                raise ValueError("Invalid debug response structure")
                
        return debug_data
    except Exception as e:
        return {"error": f"Response parsing failed: {str(e)}"}

# ======================
# Streamlit Interface
# ======================
def main():
    st.set_page_config(page_title="AI Code Debugger", page_icon="🐞", layout="wide")
    st.title("🐞 AI Code Debugger Pro")
    
    # Code Input
    code = st.text_area("Input Code:", height=300, placeholder="Paste your code here...")
    language = st.selectbox("Select Language:", ["Python", "JavaScript", "Java", "C++"])
    
    if st.button("Debug Code"):
        if not code.strip():
            st.warning("Please input some code to debug")
            return
            
        with st.spinner("🔍 Debugging your code..."):
            start_time = time.time()
            result = debug_code(code, language.lower())
            elapsed = time.time() - start_time
            
            if "error" in result:
                st.error(f"Debugging Error: {result['error']}")
            else:
                display_debug_results(result, elapsed)

def display_debug_results(data: dict, time_taken: float):
    """Display debugging results"""
    st.subheader("🔧 Debugging Report")
    
    # Metadata
    with st.expander("📊 Performance Metrics"):
        cols = st.columns(3)
        cols[0].metric("Analysis Time", f"{time_taken:.2f}s")
        cols[1].metric("Code Complexity", data['metadata']['code_complexity'].upper())
        cols[2].metric("Execution Estimate", f"{data['metadata']['execution_time']}ms")
    
    # Issues Panel
    st.subheader("🚨 Identified Issues")
    for issue_type in ['runtime_errors', 'logical_errors', 'potential_bugs']:
        if data['issues'][issue_type]:
            with st.expander(f"{issue_type.replace('_', ' ').title()} ({len(data['issues'][issue_type])})"):
                for error in data['issues'][issue_type]:
                    st.markdown(f"""
                    **Line {error['line']}**: {error['message']}
                    ```diff
                    + Fix: {error['fix']}
                    """)
    
    # Corrected Code
    st.subheader("✅ Corrected Code")
    st.code(data['corrected_code'], language=language)

if __name__ == "__main__":
    main()
