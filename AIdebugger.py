import google.generativeai as genai
import streamlit as st

# Configure Gemini API
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# Cache results to optimize performance
@st.cache_data(show_spinner=False)
def correct_code(code_snippet, language, analysis_type="Full Audit"):
    """Analyzes and corrects code using Gemini AI"""
    if not code_snippet.strip():
        return "⚠️ No code provided."

    lang = language.lower() if language != "Auto-Detect" else "python"

    prompt = f"""
    Analyze the following {lang} code and provide:

    1. **Corrected Code** (with line numbers and comments)
    2. **Error Explanation** (categorized errors and fixes)
    3. **{analysis_type.upper()} Analysis** (relevant insights)
    4. **Optimization Recommendations** (performance & security)

    Format the response strictly as:
    ```
    ### CORRECTED CODE
    ```{lang}
    [Corrected Code]
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
    ```
    """

    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(prompt)
    return response.text if response else "⚠️ No AI response."

def generate_code_from_text(prompt, language, template):
    """Generates code from user description"""
    if not prompt.strip():
        return "⚠️ Enter a description."

    query = f"Generate a {language} {template} based on: {prompt}"
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(query)

    return response.text if response else "⚠️ No AI response."

def generate_api_documentation(code_snippet, language):
    """Generates API documentation for given code"""
    if not code_snippet.strip():
        return "⚠️ Provide code for documentation."

    doc_prompt = f"Generate API documentation for this {language} code:\n```{language}\n{code_snippet}\n```"
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(doc_prompt)

    return response.text if response else "⚠️ No AI response."

# Streamlit UI with Tab Layout
st.set_page_config(page_title="AI Code Debugger", layout="wide")
st.title("🚀 AI Code Debugger Pro")

# Layout: Columns
col1, col2 = st.columns(2)

with col1:
    uploaded_file = st.file_uploader("📤 Upload Code", type=["py", "js", "java", "cpp", "cs", "go"])
    code = st.text_area("📝 Code Editor", height=300, value=uploaded_file.read().decode("utf-8") if uploaded_file else "")

with col2:
    gen_prompt = st.text_area("💡 Code Generation Prompt", height=100, placeholder="Describe functionality to generate...")

# Tabs for Different Actions
tab1, tab2, tab3 = st.tabs(["🔍 Analyze Code", "✨ Generate Code", "📄 Generate Documentation"])

with tab1:
    lang = st.selectbox("🌐 Language", ["Auto-Detect", "Python", "JavaScript", "Java", "C++", "C#", "Go", "Rust"])
    analysis_type = st.radio("🔍 Analysis Mode", ["Full Audit", "Quick Fix", "Security Review"])
    
    if st.button("🚀 Analyze Code"):
        if not code.strip():
            st.error("⚠️ Input code first.")
        else:
            with st.spinner("🔬 Analyzing Code..."):
                response = correct_code(code, lang, analysis_type)
                st.markdown(response)

with tab2:
    template = st.selectbox("📁 Code Template", ["None", "Web API", "CLI", "GUI", "Microservice"])
    
    if st.button("✨ Generate Code"):
        if not gen_prompt.strip():
            st.error("⚠️ Enter a prompt.")
        else:
            with st.spinner("🛠 Generating Code..."):
                generated_code = generate_code_from_text(gen_prompt, lang, template)
                st.code(generated_code, language=lang.lower())

with tab3:
    if st.button("📄 Generate Documentation"):
        if not code.strip():
            st.error("⚠️ Provide code first.")
        else:
            with st.spinner("📖 Generating Documentation..."):
                documentation = generate_api_documentation(code, lang)
                st.markdown(documentation)

# Sample Buggy Code for Testing
st.markdown("### 🐞 Test with Buggy Code")
buggy_code = """
def divide_numbers(a, b):
    return a / b  # No check for division by zero

def reverse_string(s):
    return s[::-1  # Syntax error, missing bracket

print("Result:", divide_numbers(10, 0))  # Division by zero
print(reverse_string("hello"))  # Syntax error
"""
st.code(buggy_code, language="python")

# FOOTER
st.markdown("---")
st.markdown(
    """
    🔹 **AI Code Debugger Pro** - Built with [Streamlit](https://streamlit.io/) & [Gemini AI](https://ai.google.dev/)  
    💡 Developed by **Robina - Google Cloud Innovator Champion**  
    📧 Contact: [Your Email] | 🌍 Follow: [Your LinkedIn/GitHub]  
    """
)
