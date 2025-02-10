import google.generativeai as genai
import streamlit as st
import re

# Initialize Gemini API
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

@st.cache_data(show_spinner=True)
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

# Streamlit UI
st.set_page_config(page_title="AI Code Debugger Pro", layout="wide")
st.title("🚀 AI Code Debugger Pro")

uploaded_file = st.file_uploader("📤 Upload Code", type=["py", "js", "java", "cpp", "cs", "go"])
code = st.text_area("📝 Code Editor", height=400, value=uploaded_file.read().decode("utf-8") if uploaded_file else "", key="code_editor")

lang = st.selectbox("🌐 Language", ["Auto-Detect", "Python", "JavaScript", "Java", "C++", "C#", "Go", "Rust"])
analysis_type = st.radio("🔍 Analysis Mode", ["Full Audit", "Quick Fix", "Security Review"])

def display_analysis():
    if not code.strip():
        st.error("⚠️ Input code first.")
    else:
        with st.spinner("🔬 Analyzing Code..."):
            response = correct_code(code, lang, analysis_type)
            
            tab1, tab2, tab3 = st.tabs(["Corrected Code", "Explanation", "Optimizations"])
            
            match_corrected = re.search(r"### CORRECTED CODE\n```.*?\n(.*?)```", response, re.DOTALL)
            match_explanation = re.search(r"### ERROR EXPLANATION\n(.*?)\n###", response, re.DOTALL)
            match_optimization = re.search(r"### OPTIMIZATION RECOMMENDATIONS\n(.*?)\n###", response, re.DOTALL)
            
            with tab1:
                st.code(match_corrected.group(1) if match_corrected else "No corrected code found.", language=lang.lower())
            with tab2:
                st.markdown(match_explanation.group(1) if match_explanation else "No explanation found.")
            with tab3:
                st.markdown(match_optimization.group(1) if match_optimization else "No optimization recommendations found.")

if st.button("🚀 Analyze Code"):
    display_analysis()

# Sample Buggy Code
buggy_code = """
def divide_numbers(a, b):
    if b == 0:
        return "Error: Division by zero"
    return a / b  # Fixed division by zero check

def reverse_string(s):
    return s[::-1]  # Fixed syntax error (added missing bracket)

print("Result:", divide_numbers(10, 0))  # Now handles division by zero gracefully
print(reverse_string("hello"))  # Now correctly reverses string
"""
st.markdown("### 🐞 Test with Buggy Code")
st.code(buggy_code, language="python")

# Footer
st.markdown("""
---
👩‍💻 **Developed by Robina Mallah**  
📧 [Email](mailto:mallah.robina@gmail.com) | 🔗 [LinkedIn](https://linkedin.com/in/robinamirbahar)
""")
