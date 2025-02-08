import google.generativeai as genai
import streamlit as st
import re
from datetime import datetime

# Configure Gemini API
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# --- Core Functions ---
def analyze_code(code, language):
    """Full code analysis with proper parsing"""
    try:
        prompt = f"""
        Analyze this {language} code:
        ```{language}
        {code}
        ```
        Return MARKDOWN with these EXACT sections:
        ## Corrected Code
        ## Error Analysis
        ## Optimizations
        ## Security Check
        """
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"**Analysis Error**: {str(e)}"

def code_chat(code, question):
    """Chat assistant for code Q&A"""
    try:
        prompt = f"""
        Code being discussed:
        ```python
        {code}
        ```
        Question: {question}
        Answer with:
        - Clear explanation
        - Code examples
        - Best practices
        """
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"**Chat Error**: {str(e)}"

def parse_analysis(response):
    """Reliable response parser"""
    sections = {
        'corrected': '',
        'errors': '',
        'optimizations': '',
        'security': ''
    }
    
    # Updated parsing logic
    corrected_match = re.search(r'## Corrected Code\s*(.*?)## Error Analysis', response, re.DOTALL)
    if corrected_match:
        sections['corrected'] = corrected_match.group(1).strip()
    
    errors_match = re.search(r'## Error Analysis\s*(.*?)## Optimizations', response, re.DOTALL)
    if errors_match:
        sections['errors'] = errors_match.group(1).strip()
    
    optimizations_match = re.search(r'## Optimizations\s*(.*?)## Security Check', response, re.DOTALL)
    if optimizations_match:
        sections['optimizations'] = optimizations_match.group(1).strip()
    
    security_match = re.search(r'## Security Check\s*(.*?)$', response, re.DOTALL)
    if security_match:
        sections['security'] = security_match.group(1).strip()
    
    return sections

# --- UI Setup ---
st.set_page_config(page_title="Ultimate Code Assistant", page_icon="🤖", layout="wide")

# Session State
if 'history' not in st.session_state:
    st.session_state.history = []
if 'code' not in st.session_state:
    st.session_state.code = ""
if 'chat' not in st.session_state:
    st.session_state.chat = []

# Main Interface
st.title("🤖 Ultimate Code Assistant")
col1, col2 = st.columns([3, 1])

# Code Input Area
with col1:
    uploaded_file = st.file_uploader("📤 Upload Code", type=["py","js","java","cpp","cs","go"])
    code = st.text_area("📝 Code Editor", height=300, value=st.session_state.code)
    
    # Analysis Controls
    col1a, col1b = st.columns(2)
    with col1a:
        analyze_btn = st.button("🔍 Analyze Code", use_container_width=True)
    with col1b:
        gen_btn = st.button("✨ Generate Docs", use_container_width=True)

# Right Sidebar
with col2:
    lang = st.selectbox("🌐 Language", ["Python", "JavaScript", "Java", "C++", "C#", "Go"])
    
    # Chat Interface
    st.subheader("💬 Code Chat")
    user_question = st.text_input("Ask about the code:")
    if user_question and code:
        response = code_chat(code, user_question)
        st.session_state.chat.append((user_question, response))
    
    for q, a in st.session_state.chat[-3:]:
        with st.expander(f"Q: {q}"):
            st.markdown(a)

# --- Handlers ---
# Code Analysis
if analyze_btn:
    if code.strip():
        with st.spinner("🔬 Deep analysis..."):
            response = analyze_code(code, lang)
            parsed = parse_analysis(response)
            
            st.subheader("Analysis Results")
            tab1, tab2, tab3, tab4 = st.tabs(["🛠 Fixed Code", "📜 Errors", "⚡ Optimize", "🔒 Security"])
            
            with tab1:
                st.code(parsed['corrected'], language=lang.lower())
            
            with tab2:
                st.markdown(f"```\n{parsed['errors']}\n```")
            
            with tab3:
                st.markdown(f"```\n{parsed['optimizations']}\n```")
            
            with tab4:
                st.markdown(f"```\n{parsed['security']}\n```")
            
            st.session_state.history.append({
                'code': code,
                'analysis': parsed,
                'timestamp': datetime.now()
            })
    else:
        st.error("⚠️ Please input code to analyze")

# Documentation Generation
if gen_btn:
    if code.strip():
        with st.spinner("📝 Generating docs..."):
            # Add documentation generation logic
            pass
    else:
        st.error("⚠️ Please input code to document")

# History
with st.sidebar:
    st.subheader("📅 History")
    for idx, entry in enumerate(st.session_state.history[-5:]):
        with st.expander(f"Analysis {idx+1}"):
            st.code(entry['code'][:100] + "...")

st.markdown("---")
st.caption("🔐 Secure AI Processing | 🛠 Full Feature Set | 💬 Interactive Chat")
