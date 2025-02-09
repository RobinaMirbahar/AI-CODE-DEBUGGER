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
        if not code_snippet.strip():
            return "⚠️ No code provided for analysis."
        
        lang = language.lower() if language != "Auto-Detect" else "python"
        code_block = f"```{lang}\n{code_snippet}\n```"
        
        base_prompt = f"""
        Analyze this {lang} code and provide:
        
        1. CORRECTED CODE with line numbers and change comments
        2. ERROR EXPLANATION with categorized errors and fixes
        3. {analysis_type.upper()} ANALYSIS with relevant suggestions
        4. OPTIMIZATION RECOMMENDATIONS for better performance and security
        
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
        - [Optimization Tip 1]
        - [Optimization Tip 2]
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

st.title("🚀 AI Code Debugger Pro")
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

with col2:
    lang = st.selectbox("🌐 Language", ["Auto-Detect", "Python", "JavaScript", "Java", "C++", "C#", "Go", "Rust"])
    analysis_type = st.radio("🔍 Analysis Mode", ["Full Audit", "Quick Fix", "Security Review"])
    template = st.selectbox("📁 Code Template", ["None", "Web API", "CLI", "GUI", "Microservice"])

if st.button("🚀 Analyze Code", use_container_width=True):
    if not code.strip():
        st.error("⚠️ Please input code or upload a file")
    else:
        with st.spinner("🔬 Deep code analysis in progress..."):
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

col3, col4, col5 = st.columns(3)
with col4:
    if st.button("✨ Generate Code"):
        generated_code = generate_code_from_text(gen_prompt, lang, template)
        st.write(generated_code)
with col5:
    if st.button("📚 Generate Docs"):
        docs = generate_api_documentation(code, lang)
        st.write(docs)

st.markdown("---")
st.markdown("© 2025 AI Code Suite Pro - All Rights Reserved")
