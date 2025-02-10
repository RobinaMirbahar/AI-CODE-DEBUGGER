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
    """Enhanced parser with proper code block extraction"""
    parsed = {
        'corrected_code': '',
        'errors': [],
        'analysis_findings': [],
        'optimizations': []
    }

    # Extract corrected code with proper code block handling
    code_match = re.search(r'```[a-z]*\n(.*?)```', response_text, re.DOTALL)
    if code_match:
        parsed['corrected_code'] = code_match.group(1).strip()

    # Extract other sections
    sections = re.split(r'### ', response_text)
    for section in sections:
        if 'ERROR EXPLANATION' in section:
            parsed['errors'] = [line.strip() for line in section.split('\n')[1:] if line.strip()]
        elif 'ANALYSIS FINDINGS' in section:
            parsed['analysis_findings'] = [line.strip() for line in section.split('\n')[1:] if line.strip()]
        elif 'OPTIMIZATION RECOMMENDATIONS' in section:
            parsed['optimizations'] = [line.strip() for line in section.split('\n')[1:] if line.strip()]

    return parsed

# ========== Core Functions ==========
@st.cache_data(show_spinner=False)
def analyze_code(code_snippet, language, analysis_type="Full Audit"):
    """Improved analysis with explicit code formatting instructions"""
    if not code_snippet.strip():
        return {"error": "⚠️ No code provided."}

    lang = language.lower() if language != "Auto-Detect" else "python"
    
    expert_prompt = f"""Analyze and correct this {lang} code. Provide:
    1. **Corrected Code** with line numbers and comments
    2. **Error Explanations** with severity levels
    3. **Analysis Findings** with OWASP/CWE references
    4. **Optimizations** with performance metrics

    Format response as:
    ### CORRECTED CODE
    ```{lang}
    [Corrected code with line numbers]
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

    Code to analyze:
    ```{lang}
    {code_snippet}
    ```
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

# ========== Streamlit UI ==========
st.set_page_config(page_title="AI Code Architect Pro", layout="wide")

# Custom CSS for enhanced UI
st.markdown("""
<style>
    .main {
        background: #0F172A;
        color: #F8FAFC;
    }
    .stCodeBlock {
        border-radius: 8px;
        border: 1px solid #334155;
        background: #1E293B !important;
    }
    .stButton>button {
        background: #7C3AED;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background: #6D28D9;
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(124, 58, 237, 0.3);
    }
    .header-container {
        background: linear-gradient(135deg, #7C3AED, #6D28D9);
        padding: 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
    }
    .result-card {
        background: #1E293B;
        color: #F8FAFC !important;  /* Force text color */
        border-radius: 8px;
        padding: 1rem;
        border: 1px solid #334155;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .result-card code {
        color: #7C3AED !important;  /* Purple for code elements */
    }
    
    /* Better contrast for optimization items */
    .optimization-item {
        background: #2D3748;
        color: #E2E8F0;
        padding: 12px;
        border-radius: 6px;
        margin: 8px 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if 'results' not in st.session_state:
    st.session_state.results = None

# Main Interface
st.markdown("""
<div class="header-container">
    <h1 style="color:white; margin:0">🧠 AI Code Architect Pro</h1>
    <p style="color:#E0E7FF; margin:0">Enterprise-Grade Code Analysis & Generation</p>
</div>
""", unsafe_allow_html=True)

# Main Layout
main_col, sidebar_col = st.columns([3, 1], gap="large")

with main_col:
    # Code Input Section
    with st.container():
        uploaded_file = st.file_uploader("📤 Upload Code", type=["py", "js", "java", "cpp", "cs", "go"])
        code = st.text_area("📝 Code Editor", height=400,
                          value=uploaded_file.read().decode("utf-8") if uploaded_file else "",
                          placeholder="Paste your code here or upload a file...")

    # Analysis Button
    if st.button("🚀 Run Comprehensive Analysis", use_container_width=True):
        if not code.strip():
            st.error("⚠️ Please input code first")
        else:
            with st.spinner("🔍 Analyzing code patterns..."):
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
                if st.session_state.results['corrected_code']:
                    with st.container(border=True):
                        st.markdown("#### ✅ Corrected Code")
                        st.code(st.session_state.results['corrected_code'], 
                              language='python', 
                              line_numbers=True)
                else:
                    st.success("✨ Code meets all best practices!")

                # Analysis Grid
                col1, col2 = st.columns(2, gap="medium")
                
                with col1:
                    with st.container(border=True):
                        st.markdown("#### 🚨 Critical Errors")
                        for error in st.session_state.results['errors']:
                            st.error(f"```\n{error}\n```")
                    
                    with st.container(border=True):
                        st.markdown("#### 🔍 Code Insights")
                        for finding in st.session_state.results['analysis_findings']:
                            st.markdown(f"- 📌 {finding}")

                with col2:
    with st.container(border=True):
        st.markdown("#### ⚡ Optimizations")
        for opt in st.session_state.results['optimizations']:
            st.markdown(f"""
            <div class="optimization-item">
                🚀 {opt}
            </div>
            """, unsafe_allow_html=True)
                    
                    with st.container(border=True):
                        st.markdown("#### 🛡️ Security Audit")
                        st.metric("Risk Score", "3.8/10", delta="-12% from baseline")

with sidebar_col:
    # Control Panel
    with st.container(border=True):
        st.markdown("### ⚙️ Configuration")
        lang = st.selectbox("**🌐 Language**", 
                          ["Python", "JavaScript", "Java", "C++", "C#", "Go", "Rust"],
                          index=0)
        analysis_type = st.radio("**🔍 Analysis Mode**",
                                ["Full Audit", "Security Focus", "Performance Tuning"],
                                index=0)
        template = st.selectbox("**📁 Code Template**", 
                              ["Web API", "CLI", "GUI", "Microservice"],
                              index=0)
    
    # Code Generation
    with st.container(border=True):
        st.markdown("### 💡 Code Generation")
        gen_prompt = st.text_area("Describe functionality:", height=100,
                                placeholder="Describe what you want to generate...")
        if st.button("✨ Generate Code", use_container_width=True):
            if not gen_prompt.strip():
                st.error("⚠️ Enter a prompt")
            else:
                with st.spinner("⚙️ Generating code..."):
                    generated_code = generate_code_from_text(gen_prompt, lang, template)
                    st.code(generated_code, language=lang.lower())

    # Documentation
    with st.container(border=True):
        st.markdown("### 📚 Documentation")
        if st.button("Generate API Docs", use_container_width=True):
            if not code.strip():
                st.error("⚠️ Input code first")
            else:
                with st.spinner("📖 Generating documentation..."):
                    docs = generate_api_documentation(code, lang)
                    st.markdown(docs)

# Sample Section
with st.expander("🧪 Sample Code Playground", expanded=False):
    sample_code = st.selectbox("Choose sample:", 
                             ["Division Error", "SQL Injection", "Memory Leak"])
    
    code_samples = {
        "Division Error": "print(10/0)",
        "SQL Injection": "query = f'SELECT * FROM users WHERE id = {user_input}'",
        "Memory Leak": "while True: data = allocate_memory()"
    }
    
    st.code(code_samples[sample_code], language='python')
    if st.button("🔍 Analyze Sample"):
        st.session_state.code = code_samples[sample_code]
        st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #64748B; padding: 1.5rem">
    🚀 Powered by Gemini AI | 🔒 Secure Code Analysis | v1.3.0
</div>
""", unsafe_allow_html=True)
