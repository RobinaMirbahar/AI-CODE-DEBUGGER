import os
import google.generativeai as genai
import streamlit as st
import difflib
import json

# Configure Gemini API
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Session State Initialization
if 'code' not in st.session_state:
    st.session_state.code = ""
if 'lang' not in st.session_state:
    st.session_state.lang = "Auto-Detect"
if 'corrected_code' not in st.session_state:
    st.session_state.corrected_code = ""

@st.cache_data(show_spinner=False)
def correct_code(code_snippet, language, analysis_type="Full Audit"):
    """Enhanced code analysis with multiple modes"""
    try:
        if not code_snippet.strip():
            return {"error": "⚠️ No code provided for analysis."}
        
        lang = language.lower() if language != "Auto-Detect" else auto_detect_language(code_snippet)
        
        base_prompt = f"""Act as an expert {lang} developer. Perform deep code analysis and return JSON with:
        {{
            "corrected_code": "Improved code with fixes",
            "error_explanation": {{
                "errors": [{{"line": "X", "description": "..."}}],
                "security_issues": [{{"type": "CWE-XX", "description": "..."}}],
                "warnings": ["Possible race condition..."]
            }},
            "optimization_recommendations": {{
                "performance": ["Replace O(n²) with hashmap..."],
                "best_practices": ["Add input validation..."],
                "refactoring": ["Extract into helper function..."],
                "tests": ["Add edge case test for..."]
            }}
        }}
        Analyze this code:\n```{lang}\n{code_snippet}\n```
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

def auto_detect_language(code):
    """Basic language detection based on file structure"""
    if "import " in code or "def " in code:
        return "python"
    elif "function " in code or "const " in code or "let " in code:
        return "javascript"
    elif "class " in code and "public static void main" in code:
        return "java"
    elif "#include" in code and "using namespace" in code:
        return "cpp"
    return "plaintext"

def display_analysis_results(response):
    """Display enhanced analysis results in expandable sections"""
    with st.expander("🛠️ Corrected Code", expanded=True):
        st.code(response.get("corrected_code", ""), language=st.session_state.lang.lower())
    
    with st.expander("❌ Errors & Warnings"):
        if response["error_explanation"]["errors"]:
            st.subheader("Critical Errors")
            for error in response["error_explanation"]["errors"]:
                st.markdown(f"- **Line {error['line']}**: {error['description']}")
        
        if response["error_explanation"]["security_issues"]:
            st.subheader("🔒 Security Issues")
            for issue in response["error_explanation"]["security_issues"]:
                st.markdown(f"- **{issue['type']}**: {issue['description']}")
        
        if response["error_explanation"]["warnings"]:
            st.subheader("⚠️ Warnings")
            for warning in response["error_explanation"]["warnings"]:
                st.markdown(f"- {warning}")

# UI Configuration
st.set_page_config(page_title="AI Code Debugger Pro", layout="wide")
st.title("🚀 AI-Powered Code Debugger Pro")

# Main Layout
col1, col2 = st.columns([3, 1])

with col2:
    # Language selection with session state
    st.session_state.lang = st.selectbox(
        "🌐 Language",
        ["Auto-Detect", "Python", "JavaScript", "Java", "C++", "C#", "Go", "Rust"],
        index=["Auto-Detect", "Python", "JavaScript", "Java", "C++", "C#", "Go", "Rust"].index(st.session_state.lang)
    )
    
    analysis_type = st.radio("🔍 Analysis Mode", ["Full Audit", "Quick Fix", "Security Review"])
    
    # Generate Code Button in sidebar
    gen_prompt = st.text_area("💡 Code Generation Prompt", height=100, placeholder="Describe functionality to generate...")
    if st.button("✨ Generate Code"):
        if not gen_prompt.strip():
            st.error("⚠️ Please enter a prompt to generate code")
        else:
            with st.spinner("✨ Generating code..."):
                generated_code = generate_code_from_text(gen_prompt, st.session_state.lang)
                st.session_state.code = generated_code
                st.rerun()

with col1:
    uploaded_file = st.file_uploader("📤 Upload Code", type=["py","js","java","cpp","cs","go","rs"])
    if uploaded_file:
        try:
            st.session_state.code = uploaded_file.read().decode("utf-8")
        except UnicodeDecodeError:
            st.error("⚠️ Invalid file format - please upload text-based source files")
    
    code = st.text_area("📝 Code Editor", height=300, value=st.session_state.code)
    
    if st.button("🛠 Analyze Code"):
        if not code.strip():
            st.error("⚠️ Please provide code for analysis")
        else:
            with st.spinner("🔍 Analyzing code..."):
                analysis_result = correct_code(code, st.session_state.lang, analysis_type)
                if "error" in analysis_result:
                    st.error(analysis_result["error"])
                    if "raw_response" in analysis_result:
                        st.text(analysis_result["raw_response"])
                else:
                    st.session_state.corrected_code = analysis_result["corrected_code"]
                    display_analysis_results(analysis_result)

# Display corrected code section
if st.session_state.corrected_code:
    st.markdown("---")
    st.subheader("🔀 Corrected Code")
    st.code(st.session_state.corrected_code, language=st.session_state.lang.lower())
    st.download_button(
        label="📥 Download Corrected Code",
        data=st.session_state.corrected_code,
        file_name=f"corrected_code.{st.session_state.lang.lower() if st.session_state.lang != 'Auto-Detect' else 'txt'}",
        mime="text/plain"
    )

# Footer
st.markdown("---")
st.markdown("© 2024 AI Code Debugger Pro - All Rights Reserved")
