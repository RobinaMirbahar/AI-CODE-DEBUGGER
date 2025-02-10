import google.generativeai as genai
import streamlit as st
import re

# Initialize Gemini API
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# Common safety settings for all Gemini interactions
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

# Streamlit UI
st.title("🚀 AI Code Debugger Pro")

# File Upload & Code Input
uploaded_file = st.file_uploader("📤 Upload Code", type=["py", "js", "java", "cpp", "cs", "go"])
code = st.text_area("📝 Code Editor", height=300, 
                  value=uploaded_file.read().decode("utf-8") if uploaded_file else "")

# Sidebar Controls
with st.sidebar:
    st.subheader("⚙️ Settings")
    lang = st.selectbox("🌐 Language", ["Auto-Detect", "Python", "JavaScript", "Java", "C++", "C#", "Go", "Rust"])
    analysis_type = st.radio("🔍 Analysis Mode", ["Full Audit", "Quick Fix", "Security Review"])
    template = st.selectbox("📁 Code Template", ["None", "Web API", "CLI", "GUI", "Microservice"])
    gen_prompt = st.text_area("💡 Code Generation Prompt", height=100, 
                            placeholder="Describe functionality to generate...")

# Main Interaction Buttons
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("🚀 Analyze Code", use_container_width=True):
        if not code.strip():
            st.error("⚠️ Input code first.")
        else:
            with st.spinner("🔬 Analyzing Code..."):
                results = analyze_code(code, lang, analysis_type)
                if 'error' in results:
                    st.error(results['error'])
                    if "DANGEROUS_CONTENT" in results['error']:
                        st.warning("""**Security Warning** 🔒
                        Detected potential security risks in:
                        - Memory operations
                        - System-level calls
                        - Input validation
                        Review carefully before deployment""")
                else:
                    # Results Display
                    main_col1, main_col2 = st.columns([2, 3])
                    
                    with main_col1:
                        with st.expander("🚨 Errors Found", expanded=True):
                            for error in results['errors']:
                                st.error(f"```\n{error}\n```")
                        
                        with st.expander("🔍 Analysis Findings"):
                            for finding in results['analysis_findings']:
                                st.markdown(f"- {finding}")

                    with main_col2:
                        st.subheader("✅ Corrected Code")
                        if results['corrected_code']:
                            st.code(results['corrected_code'], language=lang.lower())
                        else:
                            st.info("No corrections needed")
                        
                        with st.expander("⚡ Optimizations"):
                            for opt in results['optimizations']:
                                st.markdown(f"- 🚀 {opt}")

with col2:
    if st.button("✨ Generate Code", use_container_width=True):
        if not gen_prompt.strip():
            st.error("⚠️ Enter a prompt.")
        else:
            with st.spinner("🛠 Generating Code..."):
                generated_code = generate_code_from_text(gen_prompt, lang, template)
                if generated_code.startswith("⚠️"):
                    st.error(generated_code)
                else:
                    st.code(generated_code, language=lang.lower())

with col3:
    if st.button("📄 Generate Docs", use_container_width=True):
        if not code.strip():
            st.error("⚠️ Provide code first.")
        else:
            with st.spinner("📖 Generating Documentation..."):
                documentation = generate_api_documentation(code, lang)
                if documentation.startswith("⚠️"):
                    st.error(documentation)
                else:
                    st.markdown(documentation)

# Sample Buggy Code Section
st.markdown("---")
with st.expander("🐞 Sample Buggy Code Test"):
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
        with st.spinner("🔍 Analyzing Sample Code..."):
            sample_results = analyze_code(buggy_code, "Python")
            if 'error' in sample_results:
                st.error(sample_results['error'])
            else:
                st.success("✅ Sample Analysis Completed")
                st.json(sample_results)
