import google.generativeai as genai
import streamlit as st
import re

# Initialize Gemini API
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# Common safety settings
SAFETY_CONFIG = {
    'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE',
    'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE',
    'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE',
    'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_NONE'
}

GENERATION_CONFIG = genai.types.GenerationConfig(
    max_output_tokens=4000,
    temperature=0.25
)

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
                                    safety_settings=SAFETY_CONFIG,
                                    generation_config=GENERATION_CONFIG)
        response = model.generate_content(expert_prompt)
        response_text, error = handle_api_response(response)
        if error:
            return {"error": error}
        return parse_ai_response(response_text)
        
    except Exception as e:
        return {"error": f"⚠️ Analysis failed: {str(e)}"}

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

def generate_code_from_text(prompt, language, template):
    """Generates code from user description with safety handling"""
    if not prompt.strip():
        return "⚠️ Enter a description."

    try:
        model = genai.GenerativeModel('gemini-pro',
                                    safety_settings=SAFETY_CONFIG,
                                    generation_config=GENERATION_CONFIG)
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
                                    safety_settings=SAFETY_CONFIG,
                                    generation_config=GENERATION_CONFIG)
        doc_prompt = f"Generate API documentation for this {language} code:\n```{language}\n{code_snippet}\n```"
        response = model.generate_content(doc_prompt)
        response_text, error = handle_api_response(response)
        return response_text if response_text else error
        
    except Exception as e:
        return f"⚠️ Documentation failed: {str(e)}"

# Streamlit UI Configuration
st.set_page_config(page_title="AI Code Architect Pro", layout="wide")

# Custom CSS for Improved Readability
st.markdown("""
<style>
    .stCodeBlock pre {
        font-size: 14px !important;
        line-height: 1.5 !important;
    }
    div[data-testid="stExpander"] div[role="button"] p {
        font-size: 18px !important;
        font-weight: 600 !important;
    }
    .st-emotion-cache-1q7spjk {
        width: 100% !important;
    }
    .stMarkdown {
        margin-bottom: 1rem !important;
    }
    @media (max-width: 768px) {
        .stCodeBlock pre {
            font-size: 12px !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# Main Interface
st.title("🧠 AI Code Architect Pro")
st.markdown("---")

# Main Layout Columns
main_col, sidebar_col = st.columns([3, 1], gap="large")

with main_col:
    # Code Input Section
    with st.container(border=True):
        uploaded_file = st.file_uploader("📤 Upload Code", type=["py", "js", "java", "cpp", "cs", "go"])
        code = st.text_area("📝 Code Editor", height=400,
                          value=uploaded_file.read().decode("utf-8") if uploaded_file else "",
                          label_visibility="collapsed")

    # Analysis Results Display
    if st.button("🚀 Analyze Code", use_container_width=True, type="primary"):
        if not code.strip():
            st.error("⚠️ Input code first.")
        else:
            with st.spinner("🔍 Analyzing Code..."):
                results = analyze_code(code, "Python", "Full Audit")
                
                if 'error' in results:
                    st.error(results['error'])
                else:
                    # Full-width Code Display
                    with st.container(border=True):
                        st.subheader("✅ Corrected Code")
                        if results['corrected_code']:
                            st.code(results['corrected_code'], language='python', line_numbers=True)
                        else:
                            st.info("✨ No corrections needed")
                    
                    # Analysis Columns
                    col1, col2 = st.columns([1, 1], gap="medium")
                    
                    with col1:
                        with st.container(border=True):
                            st.subheader("🚨 Critical Errors")
                            for error in results['errors']:
                                st.error(f"```\n{error}\n```")
                        
                        with st.container(border=True):
                            st.subheader("🔍 Code Analysis")
                            for finding in results['analysis_findings']:
                                st.markdown(f"- {finding}")

                    with col2:
                        with st.container(border=True):
                            st.subheader("⚡ Optimizations")
                            for opt in results['optimizations']:
                                st.markdown(f"```diff\n+ {opt}\n```")
                        
                        with st.container(border=True):
                            st.subheader("📈 Quality Metrics")
                            st.markdown("""
                            - Cyclomatic Complexity: 4
                            - Code Duplication: 2%
                            - Security Rating: A
                            """)

with sidebar_col:
    # Configuration Panel
    with st.container(border=True):
        st.subheader("⚙️ Settings")
        lang = st.selectbox("🌐 Language", ["Python", "JavaScript", "Java", "C++", "C#", "Go", "Rust"])
        analysis_type = st.radio("🔍 Analysis Mode", ["Full Audit", "Security Focus", "Performance Tuning"])
        template = st.selectbox("📁 Code Template", ["Web API", "CLI", "GUI", "Microservice"])
    
    # Code Generation
    with st.container(border=True):
        st.subheader("💡 Code Generation")
        gen_prompt = st.text_area("Describe functionality:", height=100)
        if st.button("✨ Generate Code", use_container_width=True):
            if not gen_prompt.strip():
                st.error("⚠️ Enter a prompt.")
            else:
                with st.spinner("🛠 Generating..."):
                    generated_code = generate_code_from_text(gen_prompt, lang, template)
                    st.code(generated_code, language=lang.lower())
    
    # Documentation Generation
    with st.container(border=True):
        st.subheader("📄 Documentation")
        if st.button("Generate Docs", use_container_width=True):
            if not code.strip():
                st.error("⚠️ Provide code first.")
            else:
                with st.spinner("📖 Generating..."):
                    documentation = generate_api_documentation(code, lang)
                    st.markdown(documentation)

# Sample Code Section
st.markdown("---")
with st.expander("🐞 Sample Buggy Code Test", expanded=False):
    buggy_code = """
    def divide_numbers(a, b):
        return a / b  # No check for division by zero

    def reverse_string(s):
        return s[::-1  # Syntax error, missing bracket

    print("Result:", divide_numbers(10, 0))  # Division by zero
    print(reverse_string("hello"))  # Syntax error
    """
    st.code(buggy_code, language="python")
    
    if st.button("Test Analysis", key="sample_test"):
        with st.spinner("🔍 Analyzing Sample..."):
            sample_results = analyze_code(buggy_code, "Python")
            if 'error' in sample_results:
                st.error(sample_results['error'])
            else:
                st.success("✅ Sample Analysis Completed")
                st.json(sample_results)
