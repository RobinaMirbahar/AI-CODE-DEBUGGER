import google.generativeai as genai
import streamlit as st
import re

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

        # Use a well-structured prompt to get better responses
        base_prompt = f"""
        Act as an expert {lang} developer. Perform deep code analysis and return structured results:
        
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
        
        Analyze this code:
        ```{lang}
        {code_snippet}
        ```
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

def generate_code_from_text(prompt, language, template):
    """Generates code based on user-provided description."""
    if not prompt.strip():
        return "⚠️ Please enter a prompt to generate code."

    gen_prompt = f"Generate a {language} {template} based on this description: {prompt}"
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(gen_prompt)

    return response.text if response and response.text else "⚠️ No response from AI."

def generate_api_documentation(code_snippet, language):
    """Generates documentation for provided code."""
    if not code_snippet.strip():
        return "⚠️ Please provide code for documentation."

    doc_prompt = f"Generate API documentation for this {language} code:\n```{language}\n{code_snippet}\n```"
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(doc_prompt)

    return response.text if response and response.text else "⚠️ No response from AI."

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
            sections = parse_response(response)

            tab1, tab2, tab3 = st.tabs(["🛠 Corrected Code", "📖 Explanation", "💎 Optimizations"])
            with tab1:
                st.code(sections['code'], language=lang.lower())
            with tab2:
                st.markdown(f"### Error Breakdown\n{sections['explanation']}")
            with tab3:
                st.markdown(f"### Optimization Recommendations\n{sections['improvements']}")

if st.button("✨ Generate Code"):
    if not gen_prompt.strip():
        st.error("⚠️ Please enter a prompt")
    else:
        with st.spinner("🛠 Generating AI-powered code..."):
            generated_code = generate_code_from_text(gen_prompt, lang, template)
            st.code(generated_code, language=lang.lower())

if st.button("📄 Generate Documentation"):
    if not code.strip():
        st.error("⚠️ Please input code to document")
    else:
        with st.spinner("📖 Generating API documentation..."):
            documentation = generate_api_documentation(code, lang.lower())
            st.markdown(documentation)
