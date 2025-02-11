import streamlit as st
import json
import os
import google.generativeai as genai
from google.cloud import vision
from google.oauth2 import service_account

# ✅ Set up Google Vision API credentials
def set_google_credentials():
    service_account_info = json.loads(st.secrets["GOOGLE_APPLICATION_CREDENTIALS"])
    credentials = service_account.Credentials.from_service_account_info(service_account_info)
    return credentials

# ✅ Configure Gemini API
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

# ✅ Analyze image for code extraction
def analyze_image(image_file, credentials):
    vision_client = vision.ImageAnnotatorClient(credentials=credentials)
    content = image_file.read()
    image = vision.Image(content=content)
    response = vision_client.text_detection(image=image)
    extracted_text = response.text_annotations
    
    if extracted_text:
        return extracted_text[0].description  # Extracted text from image
    return None

# ✅ Analyze and debug code using Gemini API
def analyze_code(code_snippet):
    if not code_snippet.strip():
        return {"error": "⚠️ No code provided"}
    
    prompt = f"""Analyze and correct this Python code:
    ```python
    {code_snippet}
    ```
    Provide structured response with:
    - Corrected code with line comments
    - Error explanations
    - Analysis findings
    - Optimization recommendations
    """
    try:
        response = MODEL.generate_content(prompt)
        return response.text if response else "⚠️ No response from Gemini API"
    except Exception as e:
        return {"error": f"⚠️ Analysis failed: {str(e)}"}

# ✅ Set up credentials
credentials = set_google_credentials()

# 📌 Streamlit App UI
st.title("AI Code Debugger with Google Vision & Gemini API")
st.write("Upload an image of handwritten or printed code, or a Python file, and it will be analyzed for errors and optimization.")

# ✅ Upload Image File
uploaded_image = st.file_uploader("Upload a code image (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"])
if uploaded_image is not None:
    extracted_code = analyze_image(uploaded_image, credentials)
    if extracted_code:
        st.subheader("Extracted Code from Image:")
        st.code(extracted_code, language="python")  
        
        # ✅ Debug extracted code using Gemini API
        analysis_result = analyze_code(extracted_code)
        st.subheader("🔍 AI Debugging Analysis:")
        st.write(analysis_result)
    else:
        st.warning("No text found in the image.")

# ✅ Upload Code File (Optional)
uploaded_code_file = st.file_uploader("Upload a Python file for debugging", type=["py"])
if uploaded_code_file is not None:
    code_text = uploaded_code_file.read().decode("utf-8")
    st.subheader("Uploaded Code:")
    st.code(code_text, language="python")
    
    # ✅ Debug uploaded code using Gemini API
    analysis_result = analyze_code(code_text)
    st.subheader("🔍 AI Debugging Analysis:")
    st.write(analysis_result)
