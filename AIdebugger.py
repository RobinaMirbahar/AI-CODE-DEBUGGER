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
        - Corrected code
        - Error explanations
        - Optimization recommendations
        """
        
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(base_prompt)
        
        if not response or not hasattr(response, "text") or not response.text:
            return {"error": "⚠️ Empty response from Gemini API."}
        
        try:
            return json.loads(response.text)
        except json.JSONDecodeError:
            return {"error": "⚠️ Gemini API returned an invalid JSON response."}
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

st.title("🚀 AI Code Debugger Pro")
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
    
with col2:
    lang = st.selectbox("🌐 Language", ["Auto-Detect", "Python", "JavaScript", "Java", "C++", "C#", "Go", "Rust"])
    analysis_type = st.radio("🔍 Analysis Mode", ["Full Audit", "Quick Fix", "Security Review"])

if st.button("🚀 Analyze Code"):
    if not code.strip():
        st.error("⚠️ Please input code or upload a file")
    else:
        with st.spinner("🔬 Deep code analysis in progress..."):
            start_time = datetime.now()
            response = correct_code(code, lang.lower() if lang != "Auto-Detect" else "auto-detect")
            process_time = (datetime.now() - start_time).total_seconds()
            
            st.session_state.history.append({'code': code, 'response': response, 'timestamp': start_time})
        
        if "error" in response:
            st.error(response["error"])
        else:
            corrected_code = response["corrected_code"]
            explanation = response["error_explanation"]
            improvements = response["optimization_recommendations"]
            
            st.success(f"✅ Analysis completed in {process_time:.2f}s")
            tab1, tab2, tab3 = st.tabs(["🛠 Corrected Code", "📖 Explanation", "💎 Optimizations"])
            
            with tab1:
                st.subheader("Improved Code")
                st.code(corrected_code, language=lang.lower())
                display_download_button(corrected_code, lang.lower())
                st.text_area("🔍 Code Comparison", compare_code(code, corrected_code), height=200)
            
            with tab2:
                st.markdown(f"### Error Breakdown\n{explanation}")
            
            with tab3:
                st.markdown(f"### Optimization Recommendations\n{improvements}")

st.markdown("---")
st.markdown("© 2025 AI Code Debugger Pro - All Rights Reserved - Robina Mirbahar")
