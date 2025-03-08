import os
import streamlit as st
import google.generativeai as genai
import json
import re
import time

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

# Initialize the model
model = initialize_debugger()
if model is None:
    st.error("❌ Failed to initialize the model. Check your API key and configuration.")
    st.stop()

# ======================
# Debugging Core
# ======================
def debug_code(code: str, language: str) -> dict:
    """Execute code analysis with proper API calls"""
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
        return {"error": f"API Error: {str(e)}"}

def validate_response(response_text: str) -> dict:
    """Validate and parse API response JSON"""
    try:
        # Extract JSON from the response
        json_str = re.search(r'\{.*\}', response_text, re.DOTALL)
        if not json_str:
            print("⚠️ No JSON found in response. Full Response:", response_text)
            return {"error": "API response is not in JSON format"}

        # Parse JSON
        response_data = json.loads(json_str.group())

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

    except Exception as e:
        return {"error": f"Validation failed: {str(e)}"}

# ======================
# AI Agent for Further Questions
# ======================
def initialize_ai_agent():
    """Initialize the AI agent for follow-up questions"""
    try:
        generation_config = {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
            "response_mime_type": "text/plain",
        }

        system_instruction = (
            "You are an experienced software engineer specializing in debugging and optimizing code. "
            "Your role is to analyze errors, identify root causes, and provide correct solutions based on the given environment.\n\n"
            "Guidelines:\n"
            "1️⃣ Accurate Diagnosis: Analyze error messages carefully and identify root causes.\n"
            "2️⃣ System-Specific Solutions: Consider the user's OS (Windows/Linux/macOS), Python version, and dependencies.\n"
            "3️⃣ Corrected Code Output: Provide the corrected version of the faulty code.\n"
            "4️⃣ Step-by-Step Fixes: Explain each fix clearly, ensuring the user understands why it works.\n"
            "5️⃣ Commands & Logs: If CLI commands are needed (e.g., pip install, kill -9 PID), format them correctly.\n"
            "6️⃣ Verify Fix: Suggest a method to test and confirm the issue is resolved."
        )

        return genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            generation_config=generation_config,
            system_instruction=system_instruction,
        )
    except Exception as e:
        st.error(f"❌ Failed to initialize AI agent: {str(e)}")
        st.stop()

# Initialize the AI agent
ai_agent = initialize_ai_agent()
chat_session = ai_agent.start_chat(history=[])

# ======================
# Streamlit Interface
# ======================
def main():
    st.set_page_config(page_title="AI Code Debugger Pro", page_icon="🐞", layout="wide")
    st.title("🐞 AI Code Debugger Pro")
    st.write("Analyze and debug your code using Gemini AI.")

    # Input fields
    code = st.text_area("📜 Paste your code here:", height=300)
    language = st.selectbox("🌐 Select Programming Language:", ["python", "javascript", "java"])

    # Analyze button
    if st.button("🚀 Analyze Code"):
        if not code.strip():
            st.warning("⚠️ Please input some code to analyze.")
            return

        with st.spinner("🔍 Analyzing..."):
            start = time.time()
            result = debug_code(code, language.lower())
            elapsed = time.time() - start

            if "error" in result:
                st.error(f"❌ Error: {result['error']}")
            else:
                display_results(result, language.lower(), elapsed)

    # AI Agent for Follow-Up Questions
    st.markdown("---")
    st.subheader("🤖 AI Agent: Ask Follow-Up Questions")
    user_question = st.text_input("Ask a question about your code:")
    if user_question and user_question.strip():  # Ensure the input is not empty
        with st.spinner("🤖 Thinking..."):
            try:
                response = chat_session.send_message(user_question)
                st.write("**AI Response:**")
                st.write(response.text)
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    else:
        st.warning("⚠️ Please enter a valid question.")

def display_results(data: dict, lang: str, elapsed_time: float):
    """Display analysis results"""
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
