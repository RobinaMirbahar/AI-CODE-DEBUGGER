import google.generativeai as genai
import streamlit as st
import re
from datetime import datetime

# Configure Gemini API
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# --- Core Functions ---
@st.cache_data(show_spinner=False)
def generate_code(prompt_text, language):
    """AI-powered code generation"""
    try:
        full_prompt = f"""
        Generate {language} code that:
        {prompt_text}
        
        Requirements:
        1. Production-ready quality
        2. Proper error handling
        3. Clear documentation
        4. Modular structure
        """
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        return f"**Generation Error**: {str(e)}"

@st.cache_data(show_spinner=False)
def analyze_code(code_snippet, language, analysis_type):
    """Comprehensive code analysis"""
    try:
        prompt = f"""
        Analyze this {language} code:
        ```{language}
        {code_snippet}
        ```
        Provide:
        1. Corrected code with line numbers
        2. Error categorization
        3. Optimization recommendations
        4. Security suggestions
        """
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"**Analysis Error**: {str(e)}"

@st.cache_data(show_spinner=False)
def generate_docs(code_snippet, language):
    """API documentation generator"""
    try:
        prompt = f"""
        Create professional documentation for:
        ```{language}
        {code_snippet}
        ```
        Include:
        - Function descriptions
        - Parameter details
        - Return values
        - Usage examples
        - Error references
        """
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"**Docs Error**: {str(e)}"

# --- UI Setup ---
st.set_page_config(page_title="AI Code Master", page_icon="🤖", layout="wide")

# Session State
if 'history' not in st.session_state:
    st.session_state.history = []
if 'code' not in st.session_state:
    st.session_state.code = ""

# Main Interface
st.title("🤖 AI Code Master Pro")
col1, col2 = st.columns([3, 1])

with col1:
    uploaded_file = st.file_uploader("📤 Upload Code", type=["py","js","java","cpp","cs","go"])
    code = st.text_area("📝 Code Editor", height=300, value=st.session_state.code)
    gen_prompt = st.text_area("💡 Code Generation Prompt", height=100)

with col2:
    lang = st.selectbox("🌐 Language", ["Python", "JavaScript", "Java", "C++", "C#", "Go"])
    analysis_type = st.radio("🔍 Analysis Mode", ["Full Audit", "Security Focus", "Performance Tune"])

# Control Buttons
col3, col4, col5 = st.columns(3)
with col3:
    analyze_btn = st.button("🔍 Analyze Code", use_container_width=True)
with col4:
    gen_btn = st.button("✨ Generate Code", use_container_width=True)
with col5:
    doc_btn = st.button("📚 Generate Docs", use_container_width=True)

# --- Feature Handlers ---
# Code Analysis
if analyze_btn:
    if code.strip():
        with st.spinner("🔬 Analyzing code..."):
            response = analyze_code(code, lang, analysis_type)
            st.session_state.history.append({
                'code': code,
                'response': response,
                'timestamp': datetime.now()
            })
            
            st.subheader("Analysis Results")
            tab1, tab2, tab3 = st.tabs(["🛠 Corrections", "📈 Recommendations", "🔒 Security"])
            
            with tab1:
                st.code(response, language=lang.lower())
            
            with tab2:
                optimizations = re.search(r'Optimization recommendations:(.*?)Security suggestions:', response, re.DOTALL)
                if optimizations:
                    st.markdown(f"```\n{optimizations.group(1).strip()}\n```")
            
            with tab3:
                security = re.search(r'Security suggestions:(.*?)$', response, re.DOTALL)
                if security:
                    st.markdown(f"```\n{security.group(1).strip()}\n```")
    else:
        st.error("⚠️ Please input code to analyze")

# Code Generation
if gen_btn:
    if gen_prompt.strip():
        with st.spinner("🚀 Generating code..."):
            generated = generate_code(gen_prompt, lang)
            st.subheader("Generated Code")
            st.code(generated, language=lang.lower())
            
            if st.button("💾 Insert into Editor"):
                st.session_state.code = generated
                st.rerun()
    else:
        st.error("⚠️ Please describe functionality to generate")

# Documentation Generation
if doc_btn:
    if code.strip():
        with st.spinner("📝 Creating docs..."):
            docs = generate_docs(code, lang)
            st.subheader("Technical Documentation")
            st.markdown(docs)
            st.download_button("📥 Download Docs", docs, "documentation.md")
    else:
        st.error("⚠️ Please input code to document")

# History Sidebar
with st.sidebar:
    st.subheader("🕰 History")
    for idx, entry in enumerate(st.session_state.history[-3:]):
        with st.expander(f"Analysis {idx+1}"):
            st.code(entry['code'][:150] + "...")

st.markdown("---")
st.caption("🔒 Secure AI processing | 🚀 Production-ready code | 🤖 AI-powered analysis")
