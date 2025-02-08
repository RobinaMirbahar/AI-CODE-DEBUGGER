import google.generativeai as genai
import streamlit as st
import difflib
import re
from datetime import datetime

# Configure Gemini API
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

@st.cache_data(show_spinner=False)
def correct_code(code_snippet, language):
    """Analyze and correct code using Gemini AI with enhanced error handling."""
    try:
        lang = language.lower() if language != "auto-detect" else ""
        code_block = f"```{lang}\n{code_snippet}\n```" if lang else f"```\n{code_snippet}\n```"
        
        prompt = f"""
        You are an expert code correction assistant. Analyze, debug, and improve this code:

        {code_block}

        Provide markdown-formatted response with these exact sections:
        ### Corrected Code
        - Include line numbers in code blocks
        - Highlight key changes with comments
        
        ### Error Explanation
        - Categorize errors (syntax, logic, performance)
        - Explain each fix in bullet points
        
        ### Optimization Suggestions
        - Suggest efficiency improvements
        - Recommend best practices
        - Propose security enhancements
        """
        
        model = genai.GenerativeModel('gemini-2.0-pro-exp')
        response = model.generate_content(prompt)
        return response.text
    
    except Exception as e:
        return f"**API Error**: {str(e)}"

def generate_code_from_text(prompt_text, language):
    """Generate code from a text prompt using Gemini AI."""
    try:
        prompt = f"""
        You are an AI software developer. Generate code based on this description:

        {prompt_text}

        Provide the output in markdown code blocks with syntax highlighting for {language}.
        """
        
        model = genai.GenerativeModel('gemini-2.0-pro-exp')
        response = model.generate_content(prompt)
        return response.text
    
    except Exception as e:
        return f"**API Error**: {str(e)}"

def recommend_improvements(code_snippet, language):
    """Generate recommendations for code improvements."""
    try:
        prompt = f"""
        You are a senior software engineer. Review the following {language} code and provide improvement suggestions:
        ```{language}
        {code_snippet}
        ```
        
        Provide markdown-formatted output with:
        ### Code Quality Improvements
        - Readability enhancements
        - Performance optimizations
        - Security best practices
        """
        
        model = genai.GenerativeModel('gemini-2.0-pro-exp')
        response = model.generate_content(prompt)
        return response.text
    
    except Exception as e:
        return f"**API Error**: {str(e)}"

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
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(prompt)
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

st.title("🤖 AI Code Debugger Pro")
st.write("Advanced code analysis powered by Google Gemini")

code = st.text_area("📝 Paste code here:", height=300, help="Supports 10+ programming languages")
prompt_text = st.text_area("💡 Describe the functionality you want:", height=150, help="AI will generate code based on your description")
lang = st.selectbox("🌐 Language:", ["Auto-Detect", "Python", "JavaScript", "Java", "C++", "C#", "Go", "Rust", "TypeScript"])

if st.button("🚀 Analyze Code"):
    with st.spinner("🔬 Deep code analysis in progress..."):
        response = correct_code(code, lang.lower() if lang != "Auto-Detect" else "auto-detect")
    
    if response.startswith("**API Error**"):
        st.error(response)
    else:
        sections = parse_response(response)
        st.code(sections['code'], language=lang.lower())
        st.markdown(f"### Error Breakdown\n{sections['explanation']}")
        st.markdown(f"### Optimization Recommendations\n{sections['improvements']}")

if st.button("✨ Auto-Format Code"):
    formatted_code = format_code(code, lang)
    st.code(formatted_code, language=lang.lower())

if st.button("🛠 Generate Code"):
    generated_code = generate_code_from_text(prompt_text, lang)
    st.code(generated_code, language=lang.lower())

if st.button("🔍 Recommend Improvements"):
    recommendations = recommend_improvements(code, lang)
    st.markdown(recommendations)

st.markdown("---")
st.caption("🔒 Secure AI processing | 🚀 Production-ready code | 🤖 AI-powered analysis")
