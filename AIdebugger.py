import os
import streamlit as st
import google.generativeai as genai
import json
import re
import time
from pygments.lexers import guess_lexer, PythonLexer

# ======================
# Configuration
# ======================
DEBUG_PROMPT = """Analyze and debug this {language} code:
{code}

Return JSON format:
{{
  "metadata": {{"analysis_time": float, "complexity": "low/medium/high"}},
  "issues": {{
    "syntax_errors": [{{"line": int, "message": str, "fix": str}}],
    "logical_errors": [{{"line": int, "message": str, "fix": str}}],
    "security_issues": [{{"line": int, "message": str, "fix": str}}]
  }},
  "improvements": {{
    "corrected_code": str,
    "optimizations": [str],
    "security_fixes": [str]
  }}
}}"""

# ======================
# API Setup
# ======================
def initialize_debugger():
    """Proper API configuration with valid endpoints"""
    try:
        # Fetch API key from Streamlit secrets or environment variables
        if "GEMINI" in st.secrets:
            api_key = st.secrets["GEMINI"]["api_key"]
        else:
            api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            st.error("❌ Missing API Key! Check your `.streamlit/secrets.toml` or environment variables.")
            st.stop()

        # Configure Generative AI API
        genai.configure(api_key=api_key)

        # Use the correct model version
        return genai.GenerativeModel('gemini-1.5-pro')

    except Exception as e:
        st.error(f"🔌 Connection Failed: {str(e)}")
        st.stop()

# ======================
# Debugging Core
# ======================
def debug_code(code: str, language: str, model) -> dict:
    """Execute code analysis with proper API calls"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Generate the prompt for debugging
            prompt = DEBUG_PROMPT.format(language=language, code=code)
            
            # Send the prompt to the model
            response = model.generate_content(prompt)
            
            # Print raw response for debugging
            print("Raw API Response:", response.text)

            # Validate and parse the response
            return validate_response(response.text)

        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt == max_retries - 1:
                return {"error": f"API Error: {str(e)}"}
            time.sleep(2)  # Wait before retrying

def validate_response(response_text: str) -> dict:
    """Validate and parse API response JSON"""
    try:
        # Extract JSON from the response using regex
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if not json_match:
            print("⚠️ No JSON found in response. Full Response:", response_text)
            return {"error": "API response is not in JSON format"}

        json_str = json_match.group()

        # Replace single quotes with double quotes
        json_str = json_str.replace("'", '"')

        # Fix missing commas (example: add a comma before a closing brace)
        json_str = re.sub(r'(\s*"\s*:\s*[^,]+)\s*(?=\})', r'\1,', json_str)

        # Parse JSON
        response_data = json.loads(json_str)

        # Ensure expected keys are present
        required_keys = {
            "metadata": ["analysis_time", "complexity"],
            "issues": ["syntax_errors", "logical_errors", "security_issues"],
            "improvements": ["corrected_code", "optimizations", "security_fixes"]
        }

        for category, keys in required_keys.items():
            if not all(key in response_data.get(category, {}) for key in keys):
                raise ValueError(f"Invalid {category} structure")

        return response_data

    except json.JSONDecodeError as e:
        print("⚠️ Invalid JSON format. Error:", e)
        return {"error": f"Invalid JSON format: {str(e)}"}
    except Exception as e:
        return {"error": f"Validation failed: {str(e)}"}

# ======================
# AI Code Generation
# ======================
def generate_code(prompt: str, language: str, model) -> str:
    """Generate code based on a natural language prompt using the AI model."""
    try:
        # Create the prompt for code generation
        gen_prompt = f"""Generate {language} code based on the following description:
{prompt}

IMPORTANT: Return ONLY the code. Do not include any explanations or additional text."""
        
        # Send the prompt to the model
        response = model.generate_content(gen_prompt)
        
        # Return the generated code
        return response.text

    except Exception as e:
        return f"Error: {str(e)}"

# ======================
# AI Chatbot
# ======================
def ask_question(question: str, model) -> str:
    """Ask a general programming question to the AI chatbot."""
    try:
        # Send the question to the model
        response = model.generate_content(question)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

# ======================
# Streamlit Interface
# ======================
def main():
    st.set_page_config(page_title="AI Code Debugger Pro", page_icon="🐞", layout="wide")
    st.title("🐞 AI Code Debugger Pro")
    st.write("Analyze and debug your code using Gemini AI.")

    # Initialize the model inside the main function
    model = initialize_debugger()
    if model is None:
        st.error("❌ Failed to initialize the model. Check your API key and configuration.")
        st.stop()

    # File uploader
    uploaded_file = st.file_uploader("📤 Upload a code file", type=["py", "js", "java", "cpp", "cs", "go"])
    if uploaded_file:
        try:
            code = uploaded_file.read().decode("utf-8")
        except UnicodeDecodeError:
            st.error("⚠️ Invalid file format - please upload text-based source files")
            return
    else:
        code = st.text_area("📜 Paste your code here:", height=300)

    # Language selection
    language = st.selectbox("🌐 Select Programming Language:", ["Auto-Detect", "python", "javascript", "java", "cpp", "cs", "go"])

    # Auto-detect language if selected
    if language == "Auto-Detect":
        detected_language = detect_language(code, language)
        st.write(f"🔍 Detected Language: **{detected_language.capitalize()}**")
        language = detected_language

    # Analyze button
    if st.button("🚀 Analyze Code"):
        if not code.strip():
            st.warning("⚠️ Please input some code to analyze.")
            return

        with st.spinner("🔍 Analyzing..."):
            start = time.time()
            result = debug_code(code, language.lower(), model)  # Pass the model to debug_code
            elapsed = time.time() - start

            if "error" in result:
                st.error(f"❌ Error: {result['error']}")
            else:
                display_results(result, language.lower(), elapsed)

                # Store the result in session state for follow-up questions
                st.session_state["analysis_result"] = result
                st.session_state["code_context"] = code

    # AI Code Generation section
    st.divider()
    st.subheader("💡 AI Code Generation")

    # Input for natural language prompt
    code_prompt = st.text_area("📝 Enter a description of the code you want to generate:")

    # Language selection for code generation
    gen_language = st.selectbox("🌐 Select Language for Code Generation:", ["python", "javascript", "java", "cpp", "cs", "go"])

    # Button to generate code
    if st.button("🚀 Generate Code"):
        if not code_prompt.strip():
            st.warning("⚠️ Please enter a description to generate code.")
        else:
            with st.spinner("🤖 Generating code..."):
                generated_code = generate_code(code_prompt, gen_language, model)  # Pass the model to generate_code
                st.subheader("✅ Generated Code")
                st.code(generated_code, language=gen_language)

    # AI Chatbot section
    st.divider()
    st.subheader("🤖 AI Chatbot")

    # Input for chatbot question
    chatbot_question = st.text_input("❓ Ask a general programming question:")
    if chatbot_question:
        with st.spinner("🤖 Thinking..."):
            answer = ask_question(chatbot_question, model)  # Pass the model to ask_question
            st.write(f"**Answer:** {answer}")

# ======================
# Display Results
# ======================
def display_results(data: dict, lang: str, elapsed_time: float):
    """Display analysis results"""
    # Metadata
    st.subheader("📊 Metadata")
    st.write(f"**Analysis Time:** {data['metadata']['analysis_time']:.2f} seconds")
    st.write(f"**Code Complexity:** {data['metadata']['complexity'].capitalize()}")

    # Detailed Issues
    with st.expander("🚨 Detailed Issues"):
        st.subheader("🔴 Syntax Errors")
        for err in data['issues']['syntax_errors']:
            st.markdown(f"**Line {err['line']}:** {err['message']}")
            st.code(f"Fix: {err['fix']}", language=lang)

        st.subheader("🟠 Logical Errors")
        for err in data['issues']['logical_errors']:
            st.markdown(f"**Line {err['line']}:** {err['message']}")
            st.code(f"Fix: {err['fix']}", language=lang)

        st.subheader("🔒 Security Issues")
        for err in data['issues']['security_issues']:
            st.markdown(f"**Line {err['line']}:** {err['message']}")
            st.code(f"Fix: {err['fix']}", language=lang)

    # Corrected Code
    st.subheader("✅ Corrected Code")
    st.code(data['improvements']['corrected_code'], language=lang)

    # Optimizations
    if data['improvements']['optimizations']:
        st.subheader("🚀 Optimizations")
        for opt in data['improvements']['optimizations']:
            st.markdown(f"- {opt}")

    # Security Fixes
    if data['improvements']['security_fixes']:
        st.subheader("🔐 Security Fixes")
        for fix in data['improvements']['security_fixes']:
            st.markdown(f"- {fix}")

if __name__ == "__main__":
    main()
