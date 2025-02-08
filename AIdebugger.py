import google.generativeai as genai
import streamlit as st
import difflib
import re
from datetime import datetime

# Configure Gemini API
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# --- Fixed Functions ---
@st.cache_data(show_spinner=False)
def correct_code(code_snippet, language, analysis_type="Full Audit"):
    """Enhanced error handling and model selection"""
    try:
        lang = language.lower() if language != "Auto-Detect" else ""
        code_block = f"```{lang}\n{code_snippet}\n```" if lang else f"```\n{code_snippet}\n```"
        
        base_prompt = f"""
        You are an expert code assistant. Analyze this code:

        {code_block}

        Provide markdown response with these EXACT sections:
        ### Corrected Code
        - Line numbers
        - Change comments
        
        ### Error Explanation
        - Categorize errors
        - Bullet-point fixes
        """
        
        if analysis_type == "Security Review":
            base_prompt += """
            ### Security Findings
            - OWASP Top 10 vulnerabilities
            - Severity ratings
            - Remediation steps
            """
        else:
            base_prompt += """
            ### Optimization Suggestions
            - Performance improvements
            - Best practices
            - Security enhancements
            """
        
        model = genai.GenerativeModel('gemini-pro')  # Fixed model name
        response = model.generate_content(base_prompt)
        return response.text
    except Exception as e:
        return f"**API Error**: {str(e)}"

def parse_response(response_text):
    """More robust response parsing"""
    sections = {'code': '', 'explanation': '', 'improvements': ''}
    
    # Improved regex patterns
    code_match = re.search(r'```[^\n]*\n(.*?)```', response_text, re.DOTALL)
    if code_match:
        sections['code'] = code_match.group(1).strip()
    
    explanation_match = re.search(
        r'### Error Explanation\s*(.*?)(?:###|\Z)', 
        response_text, 
        re.DOTALL | re.IGNORECASE
    )
    if explanation_match:
        sections['explanation'] = explanation_match.group(1).strip()
    
    improvements_match = re.search(
        r'### (Optimization Suggestions|Security Findings)\s*(.*?)(?:###|\Z)', 
        response_text, 
        re.DOTALL | re.IGNORECASE
    )
    if improvements_match:
        sections['improvements'] = improvements_match.group(2).strip()
    
    return sections

def get_extension(language):
    """Missing helper function added"""
    extensions = {
        "Python": "py",
        "JavaScript": "js",
        "Java": "java",
        "C++": "cpp",
        "C#": "cs",
        "Go": "go",
        "Rust": "rs",
        "TypeScript": "ts"
    }
    return extensions.get(language, "txt")

# --- Fixed UI Components ---
st.set_page_config(page_title="AI Code Suite Pro", page_icon="🚀", layout="wide")

# Session State Management
if 'history' not in st.session_state:
    st.session_state.history = []
if 'code' not in st.session_state:
    st.session_state.code = ""

# Main Interface
st.title("🚀 AI Code Suite Pro")
col1, col2 = st.columns([3, 1])

with col1:
    uploaded_file = st.file_uploader("📤 Upload Code", type=["py","js","java","cpp","cs","go"])
    if uploaded_file:
        try:
            st.session_state.code = uploaded_file.read().decode("utf-8")
        except UnicodeDecodeError:
            st.error("⚠️ Invalid file format - please upload text-based source files")
    
    code = st.text_area(
        "📝 Code Editor", 
        height=300, 
        value=st.session_state.code,
        help="Write or paste your code here"
    )
    
    gen_prompt = st.text_area(
        "💡 Code Generation Prompt", 
        height=100,
        placeholder="Describe functionality to generate..."
    )

with col2:
    lang = st.selectbox(
        "🌐 Language", 
        ["Auto-Detect", "Python", "JavaScript", "Java", "C++", "C#", "Go", "Rust"]
    )
    analysis_type = st.radio(
        "🔍 Analysis Mode", 
        ["Full Audit", "Quick Fix", "Security Review"]
    )
    template = st.selectbox(
        "📁 Code Template", 
        ["None", "Web API", "CLI", "GUI", "Microservice"]
    )

# Control Panel
col3, col4, col5 = st.columns(3)
with col3:
    analyze_btn = st.button("🔍 Analyze Code", use_container_width=True)
with col4:
    gen_btn = st.button("✨ Generate Code", use_container_width=True)
with col5:
    doc_btn = st.button("📚 Generate Docs", use_container_width=True)

# --- Fixed Analysis Results ---
if analyze_btn:
    if code.strip():
        with st.spinner("🧠 Analyzing code..."):
            response = correct_code(code, lang, analysis_type)
            
            if response.startswith("**API Error**"):
                st.error(response)
            else:
                sections = parse_response(response)
                
                tab1, tab2, tab3 = st.tabs(["🛠 Code", "📖 Explanation", "🔍 Findings"])
                with tab1:
                    st.code(sections['code'], language=lang.lower() if lang != "Auto-Detect" else "")
                    if st.button("🧪 Generate Tests"):
                        tests = generate_test_cases(code, lang)
                        st.code(tests, language='python')
                
                with tab2:
                    st.markdown(f"```\n{sections['explanation']}\n```")
                
                with tab3:
                    st.markdown(f"```\n{sections['improvements']}\n```")
                
                st.session_state.history.append({
                    'code': code,
                    'response': response,
                    'timestamp': datetime.now()
                })
    else:
        st.error("⚠️ Please input code to analyze")

# ... (rest of the code remains similar with proper error handling)

# Fixed Chat Assistant
with st.sidebar:
    st.subheader("💬 Code Chat")
    user_question = st.text_input("Ask about the code:")
    if user_question and code.strip():
        response = code_chat_assistant(code, user_question)
        st.markdown(f"**AI:**\n{response}")
    
    st.subheader("📚 History")
    for idx, item in enumerate(st.session_state.history[-3:]):
        with st.expander(f"Analysis {idx+1} - {item['timestamp'].strftime('%H:%M')}"):
            st.code(item['code'][:200] + "...")

st.markdown("---")
st.markdown("🔒 *Code processed securely via Google's AI APIs*")
