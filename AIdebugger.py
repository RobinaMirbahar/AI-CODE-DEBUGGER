import google.generativeai as genai
import streamlit as st
import re
from datetime import datetime

# Initialize Gemini API
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

@st.cache_data(show_spinner=False)
def analyze_code(code_snippet, language, analysis_type="Full Audit"):
    """Advanced code analysis with structured training prompts"""
    if not code_snippet.strip():
        return {"error": "⚠️ No code provided."}

    lang = language.lower() if language != "Auto-Detect" else "python"
    
    expert_prompt = f"""Act as a senior software architect analyzing {lang} code. Provide:
    1. **Corrected Code**: Line-numbered implementation with safety checks
    2. **Critical Errors**: List with CWE/CVE references where applicable
    3. **Quality Analysis**: OWASP compliance, code smells, tech debt
    4. **Optimization Plan**: Performance metrics, memory management
    5. **Security Review**: Vulnerability assessment with CVSS scores
    
    Format strictly as:
    ### CORRECTED CODE
    ```{lang}
    [Safe implementation]
    ```
    
    ### CRITICAL ERRORS
    - [CWE-xxx] Error description (Severity: High)
    
    ### QUALITY ANALYSIS
    - [SMLLxxx] Code smell description
    
    ### OPTIMIZATION PLAN
    - [PERF] Performance improvement strategy
    
    ### SECURITY REVIEW
    - [CVE-xxx] Vulnerability details (CVSS: x.x)
    
    Analyze this code:
    ```{lang}
    {code_snippet}
    ```
    """

    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(expert_prompt)
        return parse_ai_response(response.text)
    except Exception as e:
        return {"error": f"⚠️ Analysis failed: {str(e)}"}

def parse_ai_response(response_text):
    """Parse structured AI response into categorized components"""
    sections = re.split(r'### ', response_text)
    parsed = {
        'corrected_code': '',
        'errors': [],
        'quality_issues': [],
        'optimizations': [],
        'security_findings': []
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
                elif current_section == 'critical_errors' and cleaned_line:
                    parsed['errors'].append(cleaned_line)
                elif current_section == 'quality_analysis' and cleaned_line:
                    parsed['quality_issues'].append(cleaned_line)
                elif current_section == 'optimization_plan' and cleaned_line:
                    parsed['optimizations'].append(cleaned_line)
                elif current_section == 'security_review' and cleaned_line:
                    parsed['security_findings'].append(cleaned_line)

    return parsed

# Streamlit UI with Original Tab Structure
st.title("🧠 AI Code Architect Pro")

uploaded_file = st.file_uploader("📤 Upload Code", type=["py", "js", "java", "cpp", "cs", "go"])
code = st.text_area("📝 Code Editor", height=300, value=uploaded_file.read().decode("utf-8") if uploaded_file else "")

gen_prompt = st.text_area("💡 Code Generation Prompt", height=100, placeholder="Describe functionality to generate...")

lang = st.selectbox("🌐 Language", ["Auto-Detect", "Python", "JavaScript", "Java", "C++", "C#", "Go", "Rust"])
analysis_type = st.radio("🔍 Analysis Mode", ["Full Audit", "Quick Fix", "Security Review"])
template = st.selectbox("📁 Code Template", ["None", "Web API", "CLI", "GUI", "Microservice"])

if st.button("🚀 Analyze Code"):
    if not code.strip():
        st.error("⚠️ Input code first.")
    else:
        with st.spinner("🔬 Analyzing Code..."):
            results = analyze_code(code, lang, analysis_type)
            
            if 'error' in results:
                st.error(results['error'])
            else:
                col1, col2 = st.columns([2, 3])
                
                with col1:
                    with st.expander("🚨 Critical Errors", expanded=True):
                        for error in results['errors']:
                            st.error(f"```\n{error}\n```")
                    
                    with st.expander("🔍 Quality Analysis"):
                        for issue in results['quality_issues']:
                            st.markdown(f"- 🧹 {issue}")

                with col2:
                    st.subheader("✅ Corrected Code")
                    if results['corrected_code']:
                        st.code(results['corrected_code'], language=lang.lower())
                    else:
                        st.info("No corrections needed")
                    
                    with st.expander("⚡ Optimization Plan"):
                        for opt in results['optimizations']:
                            st.markdown(f"- 🚀 {opt}")
                    
                    with st.expander("🔒 Security Findings"):
                        for finding in results['security_findings']:
                            st.warning(finding)

if st.button("✨ Generate Code"):
    if not gen_prompt.strip():
        st.error("⚠️ Enter a prompt.")
    else:
        with st.spinner("🛠 Generating Code..."):
            generated_code = generate_code_from_text(gen_prompt, lang, template)
            st.code(generated_code, language=lang.lower())

if st.button("📄 Generate Documentation"):
    if not code.strip():
        st.error("⚠️ Provide code first.")
    else:
        with st.spinner("📖 Generating Documentation..."):
            documentation = generate_api_documentation(code, lang)
            st.markdown(documentation)

# Sample Buggy Code (Keep original sample)
buggy_code = """
def divide_numbers(a, b):
    return a / b  # No check for division by zero

def reverse_string(s):
    return s[::-1  # Syntax error, missing bracket

print("Result:", divide_numbers(10, 0))  # Division by zero
print(reverse_string("hello"))  # Syntax error
"""
st.markdown("### 🐞 Test with Buggy Code")
st.code(buggy_code, language="python")
