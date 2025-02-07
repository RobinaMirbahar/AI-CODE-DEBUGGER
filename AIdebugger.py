import streamlit as st
import google.generativeai as genai

# Configure Gemini API
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

def correct_code(code_snippet, language="python"):
    prompt = f"""
    You are an AI-powered code correction assistant. 
    Analyze the following {language} code, detect errors, correct them, and suggest improvements:

    ```{language}
    {code_snippet}
    ```

    Provide:
    1. Corrected code
    2. Explanation of changes
    3. Any additional improvements
    """
    
    model = genai.GenerativeModel('gemini-2.0-pro-exp')
    response = model.generate_content(prompt)
    return response.text

st.title("AI Code Corrector with Gemini 2.0")
code = st.text_area("Paste your code here:")
language = st.selectbox("Select Language:", ["python", "javascript", "java", "c++"])

if st.button("Correct Code"):
    if code:
        corrected_code = correct_code(code, language)
        st.text_area("Suggested Corrections:", corrected_code, height=200)
    else:
        st.warning("Please enter some code.")
