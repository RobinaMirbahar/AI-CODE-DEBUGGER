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

# ✅ AI Assistant to help users
def ai_assistant():
    st.sidebar.title("AI Assistant")
    st.sidebar.write("Ask me anything about debugging and coding!")
    user_query = st.sidebar.text_input("Your question:")
    if user_query:
        response = MODEL.generate_content(f"Provide guidance for: {user_query}")
        st.sidebar.write(response.text if response else "⚠️ No response from AI")

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

# ✅ Analyze and debug code using Gemini API with benchmark evaluation
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
    - Analysis findings
    - Optimization recommendations
    Also, score the debugging effectiveness on a scale of 1-10 for:
    1. **Accuracy** (Does the fix match expected results?)
    2. **Completeness** (Are all errors addressed?)
    3. **Clarity** (Are explanations understandable?)
    Provide a final benchmark score out of 30.
    If the score is below 20, retry analysis with a refined approach emphasizing missing areas."""
    
    try:
        response = MODEL.generate_content(prompt)
        if response and "benchmark score" in response.text.lower():
            score = int(response.text.split("benchmark score:")[-1].strip().split("/30")[0])
            if score < 20:
                st.warning("🔄 Reanalyzing the code for improvements...")
                response = MODEL.generate_content(prompt + "\n\nPlease improve the accuracy, completeness, and clarity further.")
        return response.text if response else "⚠️ No response from Gemini API"
    except Exception as e:
        return {"error": f"⚠️ Analysis failed: {str(e)}"}

# ✅ Set up credentials
credentials = set_google_credentials()

# 📌 Streamlit App UI
st.title("AI Code Debugger with Google Vision & Gemini API")
st.write("Upload an image of handwritten or printed code, or a code file, and it will be analyzed for errors and optimization.")

# ✅ AI Assistant
ai_assistant()

# ✅ Upload Image File
uploaded_image = st.file_uploader("Upload a code image (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"])
if uploaded_image is not None:
    extracted_code = analyze_image(uploaded_image, credentials)
    if extracted_code:
        st.subheader("Extracted Code from Image:")
        st.code(extracted_code, language="python")  
        
        # ✅ Select programming language
        language = st.selectbox("Select Code Language", ["python", "java", "javascript", "c", "cpp", "go", "ruby", "php"])
        
        # ✅ Debug extracted code using Gemini API
        analysis_result = analyze_code(extracted_code, language)
        st.subheader("🔍 AI Debugging Analysis:")
        st.write(analysis_result)
        
        # ✅ Add paste code functionality
        if st.button("Paste Code for Editing"):
            st.text_area("Edit Code:", value=extracted_code, height=200)
    else:
        st.warning("No text found in the image.")

# ✅ Upload Code File (Optional)
uploaded_code_file = st.file_uploader("Upload a code file for debugging", type=["py", "java", "js", "c", "cpp", "go", "rb", "php"])
if uploaded_code_file is not None:
    code_text = uploaded_code_file.read().decode("utf-8")
    st.subheader("Uploaded Code:")
    
    # ✅ Detect language based on file extension
    extension = uploaded_code_file.name.split(".")[-1]
    language_map = {"py": "python", "java": "java", "js": "javascript", "c": "c", "cpp": "cpp", "go": "go", "rb": "ruby", "php": "php"}
    language = language_map.get(extension, "python")
    
    st.code(code_text, language=language)
    
    # ✅ Debug uploaded code using Gemini API
    analysis_result = analyze_code(code_text, language)
    st.subheader("🔍 AI Debugging Analysis:")
    st.write(analysis_result)
    
    # ✅ Add paste code functionality
    if st.button("Paste Code for Editing"):
        st.text_area("Edit Code:", value=code_text, height=200)
