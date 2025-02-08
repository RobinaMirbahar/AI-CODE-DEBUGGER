import google.generativeai as genai
import streamlit as st

# Configure Gemini API
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])  # Replace with your Gemini API key

def correct_code(code_snippet, language):
    """
    Analyzes and corrects errors in the provided code snippet using Gemini AI.
    
    Args:
        code_snippet (str): The code snippet to analyze.
        language (str): The programming language of the snippet.

    Returns:
        str: The corrected code and explanations.
    """
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
    
    try:
        model = genai.GenerativeModel('gemini-2.0-pro-exp')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: {e}"

# Streamlit UI
st.title("AI Code Debugger & Improver")

code_snippet = st.text_area("Enter your code:")
language = st.selectbox("Select Language", ["Python", "JavaScript", "Java", "C++", "C#", "Go"], index=0)

if st.button("Correct Code"):
    if not code_snippet.strip():
        st.error("Please enter some code to analyze.")
    else:
        correction = correct_code(code_snippet, language.lower())
        st.text_area("Suggested Corrections:", correction, height=300)
