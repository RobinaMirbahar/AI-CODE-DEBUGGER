import os
import google.generativeai as genai
import streamlit as st
import difflib
import re
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API securely
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    st.error("❌ GEMINI_API_KEY is missing. Set it as an environment variable.")
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)

@st.cache_data(show_spinner=False)
def correct_code(code_snippet, language):
    """Analyze and correct code using Gemini AI with enhanced error handling."""
    try:
        lang = language.lower() if language != "Auto-Detect" else ""
        code_block = f"```{lang}\n{code_snippet}\n```" if lang else f"```\n{code_snippet}\n```"

        prompt = f"""
        You are an expert AI code reviewer. Analyze, debug, and improve the following {language} code:

        {code_block}

        Return output with:
        - **Corrected Code** (highlight key changes)
        - **Error Explanation** (syntax, logic, security issues)
        - **Optimization Suggestions** (efficiency, best practices, security)
        """
        
        model = genai.GenerativeModel("gemini-1.5-pro-latest")
        response = model.generate_content(prompt)
        
        if not response.text:
            return "**Error:** AI did not return any response."

        return response.text
    
    except Exception as e:
        return f"**API Error:** {str(e)}"

def generate_code_from_text(prompt_text, language):
    """Generate code from a text prompt using Gemini AI."""
    try:
        prompt = f"""
        You are an AI developer. Generate {language} code for the following requirement:

        {prompt_text}

        Provide the output in markdown code blocks with syntax highlighting.
        """
        
        model = genai.GenerativeModel("gemini-1.5-pro-latest")
        response = model.generate_content(prompt)

        if not response.text:
            return "**Error:** AI did not generate any response."

        return response.text
    
    except Exception as e:
        return f"**API Error:** {str(e)}"

def format_code(code_snippet, language): 
    """AI-powered code formatting"""
    prompt = f"""
    Reformat this {language} code according to best practices:
    ```{language}
    {code_snippet}
    ```
    Apply:
    1. Standard style guide
    2. Proper indentation
    3. Consistent naming
    4. PEP8/ESLint equivalent
    """
    model = genai.GenerativeModel("gemini-1.5-pro-latest")
    response = model.generate_content(prompt)
    
    if not response.text:
        return "**Error:** AI did not return formatted code."
    
    return response.text

def parse_response(response_text):
    """Parse the AI response into structured sections"""
    sections = {'code': '', 'explanation': '', 'improvements': ''}

    code_match = re.search(r'```[\w+]*\n(.*?)```', response_text, re.DOTALL)
    if code_match:
        sections['code'] = code_match.group(1)
    
    explanation_match = re.search(r'### Error Explanation(.*?)### Optimization Suggestions', response_text, re.DOTALL)
    if explanation_match:
        sections['explanation'] = explanation_match.group(1).strip()
    
    improvements_match = re.search(r'### Optimization Suggestions(.*?)$', response_text, re.DOTALL)
    if improvements_match:
        sections['improvements'] = improvements_match.group(1).strip()
    
    return sections

st.set_page_config(page_title="AI Code Debugger Pro", page_icon="🤖", layout="wide")

st.markdown("""
    <style>
        .stMarkdown pre {border-radius: 10px; padding: 15px!important;}
        .st-emotion-cache-1y4p8pa {padding: 2rem 1rem;}
        .reportview-container {background: #f5f5f5;}
        .diff-added {background: #e6ffe6;}
        .diff-removed {background: #ffe6e6;}
        .diff-container {padding: 10px; border-radius: 5px;}
    </style>
""", unsafe_allow_html=True)

if 'history' not in st.session_state:
    st.session_state.history = []

st.title("🤖 AI Code Debugger Pro")
st.write("Advanced code analysis powered by Google Gemini")

col1, col2 = st.columns([3, 1])
with col1:
    uploaded_file = st.file_uploader("📤 Upload code file", type=["py", "js", "java", "cpp", "cs", "go", "rs", "ts"])
    
    if uploaded_file is not None:
        file_contents = uploaded_file.read().decode("utf-8")
        st.session_state['code'] = file_contents  # Store uploaded content
    
    code = st.text_area("📝 Paste code here:", height=300, value=st.session_state.get('code', ''), help="Supports multiple programming languages")
    prompt_text = st.text_area("💡 Describe the functionality you want:", height=150, help="AI will generate code based on your description")

with col2:
    lang = st.selectbox("🌐 Language:", ["Auto-Detect", "Python", "JavaScript", "Java", "C++", "C#", "Go", "Rust", "TypeScript"])
    analysis_type = st.radio("🔍 Analysis Type:", ["Full Audit", "Quick Fix", "Security Review"])
    st.info("💡 Tip: Use 'Full Audit' for a complete review")

if st.button("🚀 Analyze Code", use_container_width=True):
    if not code.strip():
        st.error("⚠️ Please input code or upload a file")
    else:
        with st.spinner("🔬 Analyzing code..."):
            start_time = datetime.now()
            response = correct_code(code, lang.lower() if lang != "Auto-Detect" else "auto-detect")
            process_time = (datetime.now() - start_time).total_seconds()
            
            st.session_state.history.append({'code': code, 'response': response, 'timestamp': start_time})
        
        if response.startswith("**API Error**"):
            st.error(response)
        else:
            sections = parse_response(response)
            st.success(f"✅ Analysis completed in {process_time:.2f}s")
            tab1, tab2, tab3 = st.tabs(["🛠 Corrected Code", "📖 Explanation", "💎 Optimizations"])
            
            with tab1:
                st.subheader("Improved Code")
                st.code(sections['code'], language=lang.lower())
            
            with tab2:
                st.markdown(f"### Error Breakdown\n{sections['explanation']}")
            
            with tab3:
                st.markdown(f"### Optimization Recommendations\n{sections['improvements']}")

if st.button("✨ Auto-Format Code"):
    formatted_code = format_code(code, lang)
    st.code(formatted_code, language=lang.lower())

if st.button("🛠 Generate Code"):
    generated_code = generate_code_from_text(prompt_text, lang)
    st.code(generated_code, language=lang.lower())

st.markdown("---")
st.markdown("🔒 **Security Note:** Code is processed securely through Google's API and not stored.")
