%%writefile AIdebugger.py
import streamlit as st
import google.generativeai as genai

# Configure Gemini API
genai.configure(api_key="GOOGLE_API_KEY")  # Replace with your actual Gemini API key

# Function to correct code
def correct_code(code_snippet, language="python"):
    prompt = f"""
    You are an AI-powered code correction assistant.
    Analyze the following {language} code, detect errors, correct them, and suggest improvements.

    Code:
    ```{language}
    {code_snippet}
    ```

    Please provide the following:
    1. **Corrected Code**: Provide the fully corrected code.
    2. **Explanation of Changes**: Describe what was fixed and why.
    3. **Additional Improvements**: Suggest improvements in readability, performance, or best practices.
    """

    try:
        model = genai.GenerativeModel('gemini-2.0-pro-exp')  
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: {e}"

# Streamlit UI
st.title("🛠️ AI Code Corrector")
st.write("An AI-powered tool to analyze and correct programming code in multiple languages.")

# Language selection
language = st.selectbox("Select Programming Language:", ["python", "javascript", "java", "c++", "html", "css"])

# Code input
user_code = st.text_area("Paste your code here:", height=200)

# Submit button
if st.button("Correct Code"):
    if user_code.strip():
        with st.spinner("Analyzing code... Please wait!"):
            correction = correct_code(user_code, language)
        st.subheader("✅ Suggested Corrections")
        st.text_area("Corrected Code and Explanation:", correction, height=400)
    else:
        st.warning("⚠️ Please enter some code before submitting.")

st.markdown("---")
st.caption("🚀 Built with Streamlit & Gemini AI | Developed by Robina")
