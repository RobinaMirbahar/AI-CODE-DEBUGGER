import google.generativeai as genai
import streamlit as st

# Configure Gemini API
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])  # Ensure API key is set in Streamlit secrets

st.title("AI Code Corrector & Optimizer")
st.write("Analyze, correct, and optimize code using Gemini AI.")

# User input: Code snippet & Language
language = st.selectbox("Select Programming Language", ["python", "javascript", "java", "c++"])
code_snippet = st.text_area("Enter your code snippet")

# Additional features
enhancement = st.selectbox("Select Enhancement", ["Code Correction", "Performance Optimization", "Security Analysis"])

def process_code(code_snippet, language, enhancement):
    """
    Analyzes and enhances code based on user selection.
    """
    prompt = f"""
    You are an AI-powered code assistant.
    Analyze the following {language} code and perform the selected enhancement: {enhancement}.

    ```{language}
    {code_snippet}
    ```

    Provide:
    1. Corrected or optimized code
    2. Explanation of changes
    3. Additional improvements if applicable
    """
    
    try:
        model = genai.GenerativeModel("gemini-2.0-pro-exp")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: {e}"

if st.button("Run AI Analysis"):
    if code_snippet:
        result = process_code(code_snippet, language, enhancement)
        st.subheader("AI Suggested Code:")
        st.code(result, language)
    else:
        st.warning("Please enter a code snippet before running analysis.")
