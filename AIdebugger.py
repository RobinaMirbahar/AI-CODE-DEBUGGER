import google.generativeai as genai
import streamlit as st
import re

# Configure Gemini API
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

@st.cache_data(show_spinner=False)
def correct_code(code_snippet, language, analysis_type="Full Audit"):
    """Performs detailed AI-powered code analysis with structured output."""
    try:
        if not code_snippet.strip():
            return "⚠️ No code provided for analysis."
        
        lang = language.lower() if language != "Auto-Detect" else "python"
        code_block = f"```{lang}\n{code_snippet}\n```"

        # Improved AI prompt
        base_prompt = f"""
        You are an expert {lang} developer. Perform deep analysis and return:
        
        1. **Corrected Code** (with clear comments on changes)
        2. **Error Explanation** (categorized errors and fixes)
        3. **{analysis_type.upper()} Analysis** (detailed insights)
        4. **Optimization Recommendations** (security, performance, best practices)
        
        **Strictly format response as follows:**
        
        ### CORRECTED CODE
        ```{lang}
        [Your corrected code here]
        ```

        ### ERROR EXPLANATION
        - **Syntax Errors**: [Explain issues & fixes]
        - **Security Issues**: [Highlight risks like injections, leaks]
        - **Logical Errors**: [Incorrect logic, faulty conditions]

        ### {analysis_type.upper()} FINDINGS
        - [Insight 1: e.g., Missing exception handling]
        - [Insight 2: e.g., Inefficient algorithm usage]

        ### OPTIMIZATION RECOMMENDATIONS
        - **Performance**: [Optimize O(n²) to O(n), parallelize loops, caching]
        - **Security**: [Validate user inputs, avoid hardcoded secrets]
        - **Best Practices**: [Use f-strings, modularize code, docstrings]
        - **Refactoring**: [Split large functions, remove redundant logic]
        - **Tests**: [Include edge case tests, increase code coverage]
        
        Analyze this code:\n```{lang}\n{code_snippet}\n```
        """

        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(base_prompt)

        return response.text if response and response.text else "⚠️ No response from AI."
    except Exception as e:
        return f"**API Error**: {str(e)}"

def parse_response(response_text):
    """Parses AI response into structured sections."""
    sections = {"code": "", "explanation": "", "improvements": ""}

    corrected_code_match = re.search(r'### CORRECTED CODE\n```[a-zA-Z0-9]+\n(.*?)```', response_text, re.DOTALL)
    explanation_match = re.search(r'### ERROR EXPLANATION\n(.*?)\n\n', response_text, re.DOTALL)
    improvements_match = re.search(r'### OPTIMIZATION RECOMMENDATIONS\n(.*?)$', response_text, re.DOTALL)

    if corrected_code_match:
        sections['code'] = corrected_code_match.group(1).strip()
    if explanation_match:
        sections['explanation'] = explanation_match.group(1).strip()
    if improvements_match:
        sections['improvements'] = improvements_match.group(1).strip()

    return sections


# Streamlit UI
st.title("🚀 AI Code Debugger Pro")
col1, col2 = st.columns([3, 1])

if 'code' not in st.session_state:
    st.session_state.code = ""
if 'history' not in st.session_state:
    st.session_state.history = []

with col1:
    uploaded_file = st.file_uploader("📤 Upload Code", type=["py", "js", "java", "cpp", "cs", "go"])
    if uploaded_file:
        try:
            st.session_state.code = uploaded_file.read().decode("utf-8")
        except UnicodeDecodeError:
            st.error("⚠️ Invalid file format - please upload text-based source files")
    code = st.text_area("📝 Code Editor", height=300, value=st.session_state.code)

with col2:
    lang = st.selectbox("🌐 Language", ["Auto-Detect", "Python", "JavaScript", "Java", "C++", "C#", "Go", "Rust"])
    analysis_type = st.radio("🔍 Analysis Mode", ["Full Audit", "Quick Fix", "Security Review"])

if st.button("🚀 Analyze Code"):
    if not code.strip():
        st.error("⚠️ Please input code or upload a file")
    else:
        with st.spinner("🔬 Deep code analysis in progress..."):
            response = correct_code(code, lang.lower(), analysis_type)
            sections = parse_response(response)

            tab1, tab2, tab3 = st.tabs(["🛠 Corrected Code", "📖 Explanation", "💎 Optimizations"])
            with tab1:
                st.code(sections['code'], language=lang.lower())
            with tab2:
                st.markdown(f"### Error Breakdown\n{sections['explanation']}")
            with tab3:
                st.markdown(f"### Optimization Recommendations\n{sections['improvements']}")
