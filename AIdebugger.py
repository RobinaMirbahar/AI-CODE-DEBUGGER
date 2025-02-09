import google.generativeai as genai
import streamlit as st
import re
from datetime import datetime

# Configure Gemini API
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

@st.cache_data(show_spinner=False)
def correct_code(code_snippet, language, analysis_type="Full Audit"):
    """Enhanced code analysis with multiple modes"""
    try:
        lang = language.lower() if language != "Auto-Detect" else "python"
        code_block = f"```{lang}\n{code_snippet}\n```"
        
        base_prompt = f"""
        Analyze this {lang} code and provide:
        
        1. CORRECTED CODE with line numbers and change comments
        2. ERROR EXPLANATION with categorized errors and fixes
        3. {analysis_type.upper()} ANALYSIS with relevant suggestions
        4. OPTIMIZATION RECOMMENDATIONS for best performance
        
        Format your response EXACTLY like this:
        
        ### CORRECTED CODE
        ```{lang}
        [Your corrected code here]
        ```
        
        ### ERROR EXPLANATION
        - [Error 1]
        - [Error 2]
        
        ### ANALYSIS FINDINGS
        - [Finding 1]
        - [Finding 2]
        
        ### OPTIMIZATION RECOMMENDATIONS
        - [Optimization 1]
        - [Optimization 2]
        """
        
        model = genai.GenerativeModel('gemini-pro')
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
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"**Generation Error**: {str(e)}"


def generate_api_documentation(code_snippet, language):
    """Enhanced API documentation generator"""
    try:
        prompt = f"""
        Create API and function documentation for this {language} code:
        ```{language}
        {code_snippet}
        ```
        
        Include:
        - API Endpoints and Methods (if applicable)
        - Request and Response examples
        - Function and class descriptions
        - Security best practices
        - Optimization recommendations for performance
        """
        model = genai.GenerativeModel('gemini-pro')
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
    """Robust response parser with fallbacks"""
    sections = {'code': '', 'explanation': '', 'improvements': '', 'optimizations': ''}
    
    try:
        code_match = re.search(r'### CORRECTED CODE\s*```.*?\n(.*?)```', response_text, re.DOTALL | re.IGNORECASE)
        explanation_match = re.search(r'### ERROR EXPLANATION(.*?)(?:###|\Z)', response_text, re.DOTALL | re.IGNORECASE)
        improvements_match = re.search(r'### ANALYSIS FINDINGS(.*?)(?:###|\Z)', response_text, re.DOTALL | re.IGNORECASE)
        optimizations_match = re.search(r'### OPTIMIZATION RECOMMENDATIONS(.*?)(?:###|\Z)', response_text, re.DOTALL | re.IGNORECASE)
        
        sections['code'] = code_match.group(1).strip() if code_match else "No code corrections suggested"
        sections['explanation'] = explanation_match.group(1).strip() if explanation_match else "No errors detected"
        sections['improvements'] = improvements_match.group(1).strip() if improvements_match else "No additional findings"
        sections['optimizations'] = optimizations_match.group(1).strip() if optimizations_match else "No optimization recommendations"
        
    except Exception as e:
        st.error(f"Parsing error: {str(e)}")
    
    return sections

st.set_page_config(page_title="AI Code Suite Pro", page_icon="🚀", layout="wide")

if 'history' not in st.session_state:
    st.session_state.history = []
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'code' not in st.session_state:
    st.session_state.code = ""

st.title("🚀 AI Code Suite Pro")

code = st.text_area("📝 Code Editor", height=300, value=st.session_state.code, help="Write or paste your code here")

if st.button("📚 Generate Docs"):
    if code.strip():
        with st.spinner("📝 Generating documentation..."):
            docs = generate_api_documentation(code, "python")
            st.markdown(docs)
            st.download_button("📥 Download Spec", docs, file_name="api_spec.yaml", mime="text/yaml")
    else:
        st.error("⚠️ Please input code to document")

st.markdown("---")
st.markdown("🔒 *Code processed securely via Google's AI APIs*")
