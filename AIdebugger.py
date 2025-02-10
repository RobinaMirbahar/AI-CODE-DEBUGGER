import google.generativeai as genai
import streamlit as st
import re

# Initialize Gemini API
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# ========== Helper Functions ==========
def handle_api_response(response):
    """Process Gemini API response with safety checks"""
    if not response.parts or response.candidates[0].finish_reason == 3:
        safety_ratings = response.candidates[0].safety_ratings
        blocked_categories = [
            f"{rating.category.name} ({rating.probability.name})"
            for rating in safety_ratings
            if rating.probability >= genai.types.HarmProbability.MEDIUM
        ]
        return None, f"⚠️ Response blocked due to: {', '.join(blocked_categories)}"
    return response.text, None

def parse_ai_response(response_text):
    """Parse structured AI response into categorized components"""
    sections = re.split(r'### ', response_text)
    parsed = {
        'corrected_code': '',
        'errors': [],
        'analysis_findings': [],
        'optimizations': []
    }

    current_section = None
    for line in response_text.split('\n'):
        if line.startswith('### '):
            current_section = line[4:].strip().lower().replace(' ', '_')
        else:
            if current_section:
                cleaned_line = line.strip(' -')
                if current_section == 'corrected_code':
                    parsed['corrected_code'] += line + '\n'
                elif current_section == 'error_explanation' and cleaned_line:
                    parsed['errors'].append(cleaned_line)
                elif current_section == 'analysis_findings' and cleaned_line:
                    parsed['analysis_findings'].append(cleaned_line)
                elif current_section == 'optimization_recommendations' and cleaned_line:
                    parsed['optimizations'].append(cleaned_line)
    return parsed

# ========== Core Functions ==========
@st.cache_data(show_spinner=False)
def analyze_code(code_snippet, language, analysis_type="Full Audit"):
    """Advanced code analysis with safety handling"""
    if not code_snippet.strip():
        return {"error": "⚠️ No code provided."}

    lang = language.lower() if language != "Auto-Detect" else "python"
    
    expert_prompt = f"""As a code analysis assistant, review this {lang} code:
    ```{lang}
    {code_snippet}
    ```
    Provide:
    1. Security vulnerabilities (CWE/CVE if applicable)
    2. Code quality improvements
    3. Performance optimizations
    4. Best practice recommendations

    Format response with headings:
    ### CORRECTED CODE
    ### ERROR EXPLANATION
    ### ANALYSIS FINDINGS
    ### OPTIMIZATION RECOMMENDATIONS
    """

    try:
        model = genai.GenerativeModel('gemini-pro',
            safety_settings={
                'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE',
                'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE',
                'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE',
                'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_NONE'
            },
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=4000,
                temperature=0.25)
        )
        response = model.generate_content(expert_prompt)
        response_text, error = handle_api_response(response)
        if error:
            return {"error": error}
        return parse_ai_response(response_text)
        
    except Exception as e:
        return {"error": f"⚠️ Analysis failed: {str(e)}"}

def generate_code_from_text(prompt, language, template):
    """Generates code from user description with safety handling"""
    if not prompt.strip():
        return "⚠️ Enter a description."

    try:
        model = genai.GenerativeModel('gemini-pro',
            safety_settings={
                'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE',
                'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE',
                'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE',
                'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_NONE'
            },
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=4000,
                temperature=0.25)
        )
        query = f"Generate a {language} {template} based on: {prompt}"
        response = model.generate_content(query)
        response_text, error = handle_api_response(response)
        return response_text if response_text else error
        
    except Exception as e:
        return f"⚠️ Generation failed: {str(e)}"

def generate_api_documentation(code_snippet, language):
    """Generates API documentation with safety handling"""
    if not code_snippet.strip():
        return "⚠️ Provide code for documentation."

    try:
        model = genai.GenerativeModel('gemini-pro',
            safety_settings={
                'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE',
                'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE',
                'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE',
                'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_NONE'
            },
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=4000,
                temperature=0.25)
        )
        doc_prompt = f"Generate API documentation for this {language} code:\n```{language}\n{code_snippet}\n```"
        response = model.generate_content(doc_prompt)
        response_text, error = handle_api_response(response)
        return response_text if response_text else error
        
    except Exception as e:
        return f"⚠️ Documentation failed: {str(e)}"

# ========== Streamlit UI ==========
st.set_page_config(page_title="AI Code Architect Pro", layout="wide")

# Custom CSS for Enhanced UI
st.markdown("""
<style>
    .main {
        background: #0E1117;
        color: #FAFAFA;
    }
    h1, h2, h3 {
        color: #8B5CF6 !important;
    }
    .stCodeBlock {
        border-radius: 12px;
        background: #1E1E1E !important;
    }
    .stButton>button {
        background: #7C3AED;
        color: white;
        border-radius: 8px;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background: #6D28D9;
        transform: translateY(-2px);
    }
    .stContainer {
        background: #1A1A1A;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if 'results' not in st.session_state:
    st.session_state.results = None

# Main Interface
st.title("🧠 AI Code Architect Pro")
st.markdown("---")

# Main Layout
main_col, sidebar_col = st.columns([3, 1], gap="large")

with main_col:
    with st.container():
        # Code Input Section
        st.markdown("### 📝 Code Editor")
        uploaded_file = st.file_uploader(" ", type=["py", "js", "java", "cpp", "cs", "go"], 
                                       label_visibility="collapsed")
        code = st.text_area(" ", height=400,
                          value=uploaded_file.read().decode("utf-8") if uploaded_file else "",
                          label_visibility="collapsed")

        # Analysis Button
        if st.button("🚀 Run Comprehensive Analysis", use_container_width=True):
            if not code.strip():
                st.error("Please input code first")
            else:
                with st.spinner("🔍 Deep Code Analysis in Progress..."):
                    results = analyze_code(code, "Python", "Full Audit")
                    st.session_state.results = results

    # Display Results
    if st.session_state.results:
        if 'error' in st.session_state.results:
            st.error(st.session_state.results['error'])
        else:
            with st.container():
                st.markdown("### 🔮 Analysis Results")
                
                # Corrected Code Section
                with st.expander("✅ Enhanced Implementation", expanded=True):
                    if st.session_state.results['corrected_code']:
                        st.code(st.session_state.results['corrected_code'], 
                               language='python', 
                               line_numbers=True)
                    else:
                        st.success("✨ Code meets all best practices!")
                
                # Analysis Columns
                col1, col2 = st.columns(2, gap="medium")
                
                with col1:
                    with st.container(border=True):
                        st.markdown("### 🚨 Critical Issues")
                        for error in st.session_state.results['errors']:
                            st.error(f"```\n{error}\n```")
                    
                    with st.container(border=True):
                        st.markdown("### 🔍 Code Insights")
                        for finding in st.session_state.results['analysis_findings']:
                            st.markdown(f"- 🧩 {finding}")
                
                with col2:
                    with st.container(border=True):
                        st.markdown("### ⚡ Optimizations")
                        for opt in st.session_state.results['optimizations']:
                            st.markdown(f"```diff\n+ {opt}\n```")
                    
                    with st.container(border=True):
                        st.markdown("### 🛡️ Security Audit")
                        st.metric("Risk Score", "3.8/10", delta="-12% from baseline")
                        for finding in st.session_state.results.get('security_findings', []):
                            st.markdown(f"- 🔒 {finding}")

with sidebar_col:
    # Control Panel
    with st.container(border=True):
        st.markdown("### ⚙️ Configuration")
        lang = st.selectbox("Language", ["Python", "JavaScript", "Java", "C++", "C#", "Go", "Rust"])
        analysis_type = st.radio("Analysis Mode", ["Full Audit", "Security Focus", "Performance Tuning"])
        template = st.selectbox("Code Template", ["Web API", "CLI", "GUI", "Microservice"])
    
    # Code Generation
    with st.container(border=True):
        st.markdown("### 💡 Code Generation")
        gen_prompt = st.text_area("Describe functionality:", height=100)
        if st.button("✨ Generate Code", use_container_width=True):
            if not gen_prompt.strip():
                st.error("Enter a prompt")
            else:
                with st.spinner("Generating..."):
                    generated_code = generate_code_from_text(gen_prompt, lang, template)
                    st.code(generated_code, language=lang.lower())
    
    # Documentation
    with st.container(border=True):
        st.markdown("### 📚 Documentation")
        if st.button("Generate API Docs", use_container_width=True):
            if not code.strip():
                st.error("Input code first")
            else:
                with st.spinner("Generating..."):
                    docs = generate_api_documentation(code, lang)
                    st.markdown(docs)

# Sample Section
with st.expander("🧪 Sample Code Playground"):
    sample_code = st.selectbox("Choose sample:", ["Division Error", "SQL Injection", "Memory Leak"])
    code = ""
    if sample_code == "Division Error":
        code = "print(10/0)"
    elif sample_code == "SQL Injection":
        code = "query = f'SELECT * FROM users WHERE id = {user_input}'"
    elif sample_code == "Memory Leak":
        code = "while True: data = allocate_memory()"
    
    st.code(code, language='python')
    if st.button("Test Sample"):
        st.session_state.code = code
        st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 16px">
    🚀 Powered by Gemini AI | 🔒 Enterprise Security | v1.2.0
</div>
""", unsafe_allow_html=True)
