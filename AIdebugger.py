import os
import json
import time
import re
import streamlit as st
import google.generativeai as genai
from google.cloud import vision
from google.oauth2 import service_account
from google.api_core.exceptions import GoogleAPICallError, RetryError
from concurrent.futures import TimeoutError as FutureTimeoutError

# Load API Key Securely
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    st.error("GEMINI_API_KEY is missing. Set it in environment variables.")
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)

# Load Google Cloud Credentials Securely
credentials = None
if cred_json := os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON"):
    try:
        credentials_dict = json.loads(cred_json)
        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict,
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
    except Exception as e:
        st.error(f"Credential parsing error: {str(e)}")
        st.stop()

# Check available models
try:
    available_models = [model.name for model in genai.list_models()]
    if "gemini-1.5-pro-latest" in available_models:
        model_name = "gemini-1.5-pro-latest"
    else:
        model_name = available_models[0] if available_models else "gemini-pro"
except Exception as e:
    st.error(f"Failed to list available models: {str(e)}")
    st.stop()

# Initialize Gemini Model
try:
    MODEL = genai.GenerativeModel(
        model_name,
        safety_settings={
            'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE',
            'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE',
            'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE',
            'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_NONE'
        },
        generation_config=genai.types.GenerationConfig(
            max_output_tokens=4000,
            temperature=0.25
        )
    )
except Exception as e:
    st.error(f"Model initialization error: {str(e)}")
    st.stop()

st.set_page_config(page_title="AI Code Debugger", layout="wide")
st.title("🛠️ AI-Powered Code Debugger")

# Function to analyze code
def analyze_code(code: str, language: str) -> dict:
    try:
        prompt = f"""
        Analyze the following {language} code for bugs, fixes, and optimizations.
        Return JSON with keys: 'bugs', 'fixes', 'corrected_code', and 'explanation'.
        
        CODE:
        {code}
        """
        response = MODEL.generate_content(prompt)

        # Ensure response is valid and extract JSON
        if not response.text:
            return {"error": "No response received from AI model."}

        # Extract JSON from text response
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        else:
            return {"error": "AI response does not contain valid JSON."}

    except json.JSONDecodeError:
        return {"error": "Failed to parse AI response: Invalid JSON format."}
    except Exception as e:
        return {"error": f"Analysis failed: {str(e)}"}

# UI Components
input_code = st.text_area("Paste Code Here", height=300)
if st.button("Analyze Code"):
    if input_code.strip():
        with st.spinner("Analyzing..."):
            results = analyze_code(input_code, "python")
            if "error" in results:
                st.error(results["error"])
            else:
                st.subheader("🔍 Analysis Results")
                st.write(results)
    else:
        st.warning("Please enter some code to analyze.")
