import streamlit as st
import json
import os
import google.generativeai as genai
from google.cloud import vision
from google.oauth2 import service_account
import subprocess

# Set Google Cloud Credentials
def set_google_credentials():
    service_account_info = json.loads(st.secrets["GOOGLE_APPLICATION_CREDENTIALS"])
    credentials = service_account.Credentials.from_service_account_info(service_account_info)
    return credentials

# Configure Gemini AI API
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
SAFETY_SETTINGS = {
    'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE',
    'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE',
    'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE',
    'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_NONE'
}
GENERATION_CONFIG = genai.types.GenerationConfig(
    max_output_tokens=4000,
    temperature=0.25
)
MODEL = genai.GenerativeModel('gemini-pro',
    safety_settings=SAFETY_SETTINGS,
    generation_config=GENERATION_CONFIG
)

# AI Assistant Sidebar with Tooltips
def ai_assistant():
    st.sidebar.title("🧠 AI Assistant")
    st.sidebar.write("Ask me anything about debugging and coding!")
    user_query = st.sidebar.text_input("🔍 Your question:", help="Type your query here and get AI-generated insights.")
    if user_query:
        response = MODEL.generate_content(f"Provide guidance for: {user_query}")
        st.sidebar.write(response.text if response else "⚠️ No response from AI")

# Code Execution Function
def execute_code(code, language):
    try:
        if language == "python":
            result = subprocess.run(["python3", "-c", code], capture_output=True, text=True, timeout=5)
        elif language == "javascript":
            result = subprocess.run(["node", "-e", code], capture_output=True, text=True, timeout=5)
        elif language == "java":
            with open("Temp.java", "w") as f:
                f.write(code)
            result = subprocess.run(["javac", "Temp.java"], capture_output=True, text=True)
            if result.returncode == 0:
                result = subprocess.run(["java", "Temp"], capture_output=True, text=True, timeout=5)
        else:
            return "⚠️ Execution not supported for this language."
        return result.stdout if result.stdout else result.stderr
    except Exception as e:
        return f"Execution Error: {str(e)}"

# AI Code Analysis Function
def analyze_code(code_snippet, language="python"):
    if not code_snippet.strip():
        return {"error": "⚠️ No code provided"}
    
    prompt = f"""Analyze and correct this {language} code:
    ```{language}
    {code_snippet}
    ```
    Provide structured response with:
    - Corrected code with line comments
    - Error explanations
    - Execution results (if applicable)
    - Optimization recommendations
    """
    try:
        response = MODEL.generate_content(prompt)
        corrected_code = response.text if response else "⚠️ No response from AI"
        execution_result = execute_code(corrected_code, language)
        return {
            "corrected_code": corrected_code,
            "execution_result": execution_result,
        }
    except Exception as e:
        return {"error": f"⚠️ Analysis failed: {str(e)}"}

# Extract Code from Image
def extract_code_from_image(image):
    credentials = set_google_credentials()
    client = vision.ImageAnnotatorClient(credentials=credentials)
    content = image.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations
    if texts:
        return texts[0].description
    return "⚠️ No text detected in image."

# Initialize Credentials
credentials = set_google_credentials()

# Streamlit UI
st.title("🛠️ AI Code Debugger with Google Vision & Gemini API")
st.write("Upload an image of handwritten or printed code, upload a code file, or paste code manually for debugging and optimization.")

# Initialize AI Assistant
ai_assistant()

# Image Upload Debugging Feature
st.subheader("🖼️ Upload Image with Code")
st.write("Upload an image containing code, and AI will extract and debug it.")
uploaded_image = st.file_uploader("📂 Choose an image file", type=["png", "jpg", "jpeg"], help="Supported formats: PNG, JPG, JPEG")
if uploaded_image is not None:
    st.image(uploaded_image, caption="Uploaded Image", use_container_width=True)
    extracted_code = extract_code_from_image(uploaded_image)
    st.subheader("📜 Extracted Code:")
    st.code(extracted_code, language="python")
    analysis_result = analyze_code(extracted_code)
    st.subheader("🔍 AI Debugging Analysis:")
    st.write(analysis_result)

# File Upload Debugging Feature
st.subheader("📂 Upload Code File for Debugging")
st.write("Upload a code file for AI analysis and debugging.")
uploaded_code_file = st.file_uploader("Choose a code file", type=["py", "java", "js"], help="Supported formats: Python (.py), Java (.java), JavaScript (.js)")
if uploaded_code_file is not None:
    code_text = uploaded_code_file.read().decode("utf-8")
    
    extension = uploaded_code_file.name.split(".")[-1]
    language_map = {"py": "python", "java": "java", "js": "javascript"}
    language = language_map.get(extension, "python")
    
    st.subheader("📜 Uploaded Code:")
    st.code(code_text, language=language)
    
    analysis_result = analyze_code(code_text, language)
    st.subheader("🔍 AI Debugging Analysis:")
    st.write(analysis_result)

# Manual Code Debugging Feature
st.subheader("✏️ Manually Paste Code for Debugging")
st.write("Paste your code below and let AI analyze and fix it.")
pasted_code_manual = st.text_area("Paste Your Code Here:", height=200)
if st.button("Analyze Manual Code"):
    manual_analysis = analyze_code(pasted_code_manual)
    st.subheader("🔍 AI Debugging Analysis for Manual Code:")
    st.write(manual_analysis)

# Workflow Guide
st.sidebar.subheader("📌 How to Use This Tool")
st.sidebar.write("1️⃣ **Upload an image** with handwritten/printed code.")
st.sidebar.write("2️⃣ **Upload a code file** in Python, Java, or JavaScript.")
st.sidebar.write("3️⃣ **Paste code manually** for instant AI analysis.")
st.sidebar.write("4️⃣ **View AI debugging insights** and execution results.")
