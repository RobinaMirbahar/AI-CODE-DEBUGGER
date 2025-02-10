The provided code is well-structured and functional. Here's the breakdown with recommendations kept within the original structure:

**### ERROR EXPLANATION**  
*(No critical errors found in the implementation. These are observations:)*  
- **Language Detection:** Auto-detect defaults to Python; consider adding basic syntax checks for more accurate language detection.  
- **Response Formatting:** Gemini's output might occasionally deviate from the markdown structure. Adding validation would make it more robust.  

**### ANALYSIS FINDINGS**  
- **Streamlit Caching:** `@st.cache_data` usage is appropriate for performance.  
- **Security:** API key management via `st.secrets` follows best practices.  
- **Error Handling:** Gracefully handles empty inputs but could benefit from Gemini response validation.  

**### OPTIMIZATION RECOMMENDATIONS**  
- **User Feedback:** Add success toasts (e.g., "Analysis completed!") after operations.  
- **Template Handling:** Skip "None" template in generation queries for cleaner prompts.  
- **UI/UX:** Add expandable sections for long outputs to improve readability.  

**Corrected Code** *(No changes made - original code is correct as per requirements):**

```python
import google.generativeai as genai
import streamlit as st
import re

# Initialize Gemini API
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

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

# Streamlit UI
st.title("🚀 AI Code Debugger Pro")

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
            response = correct_code(code, lang, analysis_type)
            st.markdown(response)

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

# Sample Buggy Code
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
