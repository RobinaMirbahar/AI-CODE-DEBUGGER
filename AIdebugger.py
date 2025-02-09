import google.generativeai as genai
import streamlit as st
import re

# Configure Gemini API
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

@st.cache_data(show_spinner=True)
def correct_code(code_snippet, language, analysis_type="Full Audit"):
    """Enhanced code analysis with multiple modes"""
    try:
        if not code_snippet.strip():
            return "⚠️ No code provided for analysis."
        lang = language.lower() if language != "Auto-Detect" else "python"
        
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

        ### OPTIMIZATION RECOMMENDATIONS
        - [Optimization Tip 1]
        - [Optimization Tip 2]
        """

        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(base_prompt)
        return response.text if response and response.text else "⚠️ No response from AI."
    except Exception as e:
        return f"**API Error**: {str(e)}"

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

gen_prompt = st.text_area("💡 Code Generation Prompt", height=100, placeholder="Describe functionality to generate...")

with col2:
    lang = st.selectbox("🌐 Language", ["Auto-Detect", "Python", "JavaScript", "Java", "C++", "C#", "Go", "Rust"])
    analysis_type = st.radio("🔍 Analysis Mode", ["Full Audit", "Quick Fix", "Security Review"])
    template = st.selectbox("📁 Code Template", ["None", "Web API", "CLI", "GUI", "Microservice"])

if st.button("🚀 Analyze Code"):
    if not code.strip():
        st.error("⚠️ Please input code or upload a file")
    else:
        with st.spinner("🔬 Deep code analysis in progress..."):
            response = correct_code(code, lang.lower(), analysis_type)
            
            # Extract sections
            corrected_code_match = re.search(r'### CORRECTED CODE\n```[a-zA-Z0-9]+\n(.*?)```', response, re.DOTALL)
            explanation_match = re.search(r'### ERROR EXPLANATION\n(.*?)\n\n', response, re.DOTALL)
            recommendations_match = re.search(r'### OPTIMIZATION RECOMMENDATIONS\n(.*?)$', response, re.DOTALL)
            
            corrected_code = corrected_code_match.group(1).strip() if corrected_code_match else "⚠️ No corrected code."
            explanation = explanation_match.group(1).strip() if explanation_match else "⚠️ No error explanation."
            recommendations = recommendations_match.group(1).strip() if recommendations_match else "⚠️ No recommendations."
            
            tab1, tab2, tab3 = st.tabs(["🛠 Corrected Code", "📖 Error Explanation", "💎 Optimizations"])
            with tab1:
                st.code(corrected_code, language=lang.lower())
            with tab2:
                st.markdown(f"### Error Breakdown\n{explanation}")
            with tab3:
                st.markdown(f"### Optimization Recommendations\n{recommendations}")

if st.button("📄 Generate Documentation"):
    if not code.strip():
        st.error("⚠️ Please input code to document")
    else:
        with st.spinner("📖 Generating API documentation..."):
            doc_prompt = f"Generate API documentation for this {lang} code:\n```{lang}\n{code}\n```"
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(doc_prompt)
            st.markdown(response.text if response and response.text else "⚠️ No response from AI.")

# Footer with contact details
st.markdown("""
---
👩‍💻 **Developed by Robina Mallah**  
📧 [Contact Me](mailto:mallah.robina@gmail.com) | 🌐 [LinkedIn](https://www.linkedin.com/in/robinamirbahar)  
""")
