import google.generativeai as genai
import streamlit as st
import difflib
import re
from datetime import datetime

# Configure Gemini API
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

@st.cache_data(show_spinner=False)
def correct_code(code_snippet, language, analysis_type="Full Audit"):
    """Enhanced code analysis with multiple modes"""
    try:
        lang = language.lower() if language != "auto-detect" else ""
        code_block = f"```{lang}\n{code_snippet}\n```" if lang else f"```\n{code_snippet}\n```"
        
        base_prompt = f"""
        You are an expert code assistant. Analyze this code:

        {code_block}

        Provide markdown response with these sections:
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
        
        model = genai.GenerativeModel('gemini-2.0-pro-exp')
        response = model.generate_content(base_prompt)
        return response.text
    except Exception as e:
        return f"**API Error**: {str(e)}"

def generate_code_from_text(prompt_text, language, template=None):
    """AI-powered code generation"""
    try:
        template_prompt = f" using {template} template" if template else ""
        prompt = f"""
        Generate {language} code{template_prompt} for:
        {prompt_text}
        
        Include:
        1. Production-ready code
        2. Error handling
        3. Documentation
        4. Test hooks
        """
        model = genai.GenerativeModel('gemini-2.0-pro-exp')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"**Generation Error**: {str(e)}"

def generate_test_cases(code_snippet, language):
    """Test case generation"""
    try:
        prompt = f"""
        Create pytest tests for this {language} code:
        ```{language}
        {code_snippet}
        ```
        Include:
        - Edge cases
        - Mocking
        - Parameterized tests
        """
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"**Test Error**: {str(e)}"

def generate_api_documentation(code_snippet, language):
    """API documentation generator"""
    try:
        prompt = f"""
        Create OpenAPI documentation for this {language} code:
        ```{language}
        {code_snippet}
        ```
        Include:
        - Endpoints
        - Schemas
        - Examples
        - Security schemes
        """
        model = genai.GenerativeModel('gemini-2.0-pro-exp')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"**Docs Error**: {str(e)}"

def code_chat_assistant(code_snippet, question):
    """Code-focused chat AI"""
    try:
        prompt = f"""
        As code tutor, explain:
        ```python
        {code_snippet}
        ```
        Question: {question}
        - Simplify concepts
        - Give examples
        - Highlight best practices
        """
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"**Chat Error**: {str(e)}"

def parse_response(response_text):
    """Parse analysis response"""
    sections = {'code': '', 'explanation': '', 'improvements': ''}
    code_match = re.search(r'```[\w+]*\n(.*?)```', response_text, re.DOTALL)
    if code_match:
        sections['code'] = code_match.group(1)
    explanation_match = re.search(r'### Error Explanation(.*?)###', response_text, re.DOTALL)
    if explanation_match:
        sections['explanation'] = explanation_match.group(1).strip()
    improvements_match = re.search(r'### (Optimization Suggestions|Security Findings)(.*?)$', response_text, re.DOTALL)
    if improvements_match:
        sections['improvements'] = improvements_match.group(2).strip()
    return sections

# Streamlit UI Configuration
st.set_page_config(page_title="AI Code Suite Pro", page_icon="🚀", layout="wide")

# Custom Styling
st.markdown("""
    <style>
        .stMarkdown pre {border-radius: 10px; padding: 15px!important;}
        .stTextArea textarea {font-family: monospace !important;}
        .highlight {border-left: 3px solid #4CAF50; padding-left: 10px;}
        .stButton>button {transition: all 0.3s ease;}
        .stButton>button:hover {transform: scale(1.05);}
    </style>
""", unsafe_allow_html=True)

# Session State
if 'history' not in st.session_state:
    st.session_state.history = []
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Main Interface
st.title("🚀 AI Code Suite Pro")
col1, col2 = st.columns([3, 1])

with col1:
    uploaded_file = st.file_uploader("📤 Upload Code", type=["py","js","java","cpp","cs","go"])
    code = st.text_area("📝 Code Editor", height=300, 
                      value=st.session_state.get('code', ''),
                      help="Write or paste your code here")
    
    gen_prompt = st.text_area("💡 Code Generation Prompt", height=100,
                            placeholder="Describe functionality to generate...")

with col2:
    lang = st.selectbox("🌐 Language", ["Auto-Detect", "Python", "JavaScript", 
                                      "Java", "C++", "C#", "Go", "Rust"])
    analysis_type = st.radio("🔍 Analysis Mode", ["Full Audit", "Quick Fix", "Security Review"])
    template = st.selectbox("📁 Code Template", ["None", "Web API", "CLI", "GUI", "Microservice"])

# Control Panel
col3, col4, col5 = st.columns(3)
with col3:
    analyze_btn = st.button("🔍 Analyze Code", use_container_width=True)
with col4:
    gen_btn = st.button("✨ Generate Code", use_container_width=True)
with col5:
    doc_btn = st.button("📚 Generate Docs", use_container_width=True)

# Analysis Results
if analyze_btn:
    if code.strip():
        with st.spinner("🧠 Analyzing code..."):
            response = correct_code(code, lang, analysis_type)
            sections = parse_response(response)
            
            tab1, tab2, tab3 = st.tabs(["🛠 Code", "📖 Explanation", "🔍 Findings"])
            with tab1:
                st.code(sections['code'], language=lang.lower())
                if st.button("🧪 Generate Tests"):
                    tests = generate_test_cases(code, lang)
                    st.code(tests, language='python')
            with tab2:
                st.markdown(f"```\n{sections['explanation']}\n```")
            with tab3:
                st.markdown(f"```\n{sections['improvements']}\n```")
    else:
        st.error("⚠️ Please input code to analyze")

# Code Generation
if gen_btn:
    if gen_prompt.strip():
        with st.spinner("🚀 Generating code..."):
            generated = generate_code_from_text(gen_prompt, lang, template)
            st.code(generated, language=lang.lower())
            if st.button("💾 Save to Editor"):
                st.session_state.code = generated
                st.rerun()
    else:
        st.error("⚠️ Please describe the functionality")

# API Documentation
if doc_btn:
    if code.strip():
        with st.spinner("📝 Generating documentation..."):
            docs = generate_api_documentation(code, lang)
            st.markdown(docs)
            st.download_button("📥 Download Spec", docs, 
                             file_name="api_spec.yaml",
                             mime="text/yaml")
    else:
        st.error("⚠️ Please input code to document")

# Chat Assistant
with st.sidebar:
    st.subheader("💬 Code Chat")
    user_question = st.text_input("Ask about the code:")
    if user_question and code.strip():
        response = code_chat_assistant(code, user_question)
        st.markdown(f"**AI:**\n{response}")
    
    st.subheader("📚 History")
    for idx, item in enumerate(st.session_state.history[-3:]):
        with st.expander(f"Analysis {idx+1}"):
            st.code(item['code'][:200] + "...")

# Footer
st.markdown("---")
st.markdown("🔒 *Code processed securely via Google's AI APIs*")
