import streamlit as st
import json
import os
from google.cloud import vision
from google.cloud.vision_v1 import types
import google.auth

def set_google_credentials():
    # ✅ Load service account credentials from Streamlit Secrets
    service_account_info = json.loads(st.secrets["GOOGLE_APPLICATION_CREDENTIALS"])
    
    # ✅ Save to a temporary file
    with open("service_account.json", "w") as f:
        json.dump(service_account_info, f)
    
    # ✅ Set environment variable for Google API authentication
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service_account.json"

def analyze_image(image_file):
    """Extracts text from an uploaded image using Google Vision API."""
    vision_client = vision.ImageAnnotatorClient()
    content = image_file.read()
    image = vision.Image(content=content)
    response = vision_client.text_detection(image=image)
    extracted_text = response.text_annotations
    
    if extracted_text:
        return extracted_text[0].description  # Extracted text from image
    return None

# ✅ Set up Google credentials
set_google_credentials()

# 📌 Streamlit App UI
st.title("AI Code Debugger with Google Vision API")
st.write("Upload an image of handwritten or printed code, and it will be converted into text for debugging.")

# ✅ Upload Image File
uploaded_image = st.file_uploader("Upload a code image (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"])

if uploaded_image is not None:
    extracted_code = analyze_image(uploaded_image)
    if extracted_code:
        st.subheader("Extracted Code from Image:")
        st.code(extracted_code, language="python")  # Display extracted code
        
        # ✅ Perform basic debugging (Example: Checking for syntax errors)
        try:
            exec(extracted_code)  # 🚨 WARNING: This executes the code! Remove for security.
            st.success("✅ No syntax errors found!")
        except Exception as e:
            st.error(f"❌ Syntax Error: {e}")
    else:
        st.warning("No text found in the image.")

# ✅ Upload Code File (Optional)
uploaded_code_file = st.file_uploader("Upload a Python file for debugging", type=["py"])

if uploaded_code_file is not None:
    code_text = uploaded_code_file.read().decode("utf-8")
    
    st.subheader("Uploaded Code:")
    st.code(code_text, language="python")

    # ✅ Perform Debugging
    try:
        exec(code_text)  # 🚨 WARNING: This executes the code! Remove for security.
        st.success("✅ No syntax errors found in the uploaded file!")
    except Exception as e:
        st.error(f"❌ Syntax Error: {e}")
import os
import google.generativeai as genai
import google.cloud.vision as vision
import streamlit as st
import re
from io import BytesIO

# ===== Initialize APIs =====
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "path/to/your/service-account.json"
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
vision_client = vision.ImageAnnotatorClient()

# ===== Constants & Configs =====
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

# ===== Helper Functions =====
def handle_api_response(response):
    """Process API response with error handling"""
    if not response.parts:
        ratings = response.candidates[0].safety_ratings
        blocked = [
            f"{r.category.name} ({r.probability.name})" 
            for r in ratings if r.probability >= genai.types.HarmProbability.MEDIUM
        ]
        return None, f"⚠️ Blocked: {', '.join(blocked)}" if blocked else "⚠️ Empty response"
    return response.text, None

def parse_code_blocks(response_text):
    """Extracts code blocks from AI response"""
    return re.findall(r'```[a-z]*\n(.*?)```', response_text, re.DOTALL)

def analyze_code(code_snippet, language="python"):
    """Analyze and correct uploaded code."""
    if not code_snippet.strip():
        return {"error": "⚠️ No code provided"}
    
    prompt = f"""Analyze and correct this {language} code:
    ```{language}
    {code_snippet}
    ```
    Provide structured response with:
    - Corrected code with comments
    - Error explanations
    - Optimization recommendations
    """

    try:
        response = MODEL.generate_content(prompt)
        return handle_response(response)
    except Exception as e:
        return {"error": f"⚠️ Analysis failed: {str(e)}"}

def handle_response(response):
    """Handles AI-generated response."""
    response_text, error = handle_api_response(response)
    return {"error": error} if error else parse_response(response_text)

def parse_response(response_text):
    """Extracts structured results from AI response."""
    code_blocks = parse_code_blocks(response_text)
    return {
        'corrected_code': code_blocks[0].strip() if code_blocks else '',
        'errors': extract_items(response_text, 'ERROR EXPLANATION'),
        'optimizations': extract_items(response_text, 'OPTIMIZATION RECOMMENDATIONS')
    }

def extract_items(text, header):
    """Extracts list items under specific headers."""
    sections = re.split(r'### \w+', text)
    for section in sections:
        if header in section:
            return [line.strip() for line in section.split('\n') if line.strip()]
    return []

def extract_text_from_image(image_bytes):
    """Uses Vision API to extract text from an uploaded image."""
    image = vision.Image(content=image_bytes)
    response = vision_client.text_detection(image=image)
    texts = response.text_annotations
    return texts[0].description if texts else ""

# ===== UI Components =====
def main_content():
    """Main UI content"""
    with st.container():
        uploaded_file = st.file_uploader("📤 Upload Code File or Image", type=["py", "js", "java", "cpp", "cs", "go", "png", "jpg", "jpeg"])
        code = ""
        
        if uploaded_file:
            file_type = uploaded_file.type
            file_bytes = uploaded_file.read()
            
            if "image" in file_type:
                st.info("Extracting text from image...")
                code = extract_text_from_image(file_bytes)
            else:
                code = file_bytes.decode("utf-8")
        
        code_snippet = st.text_area("📝 Editor", value=code, height=400, placeholder="Paste code here...")
        if st.button("🚀 Analyze", use_container_width=True) and code_snippet.strip():
            with st.spinner("Analyzing..."):
                st.session_state.results = analyze_code(code_snippet, "Python")

def sidebar_content():
    """Sidebar settings"""
    with st.container(border=True):
        st.markdown("### ⚙️ Settings")
        st.selectbox("Language", ["Auto-Detect", "Python", "JavaScript", "Java", "C++", "C#", "Go", "Rust"])

# ===== Initialize App =====
def init_app():
    """Initialize Streamlit App"""
    st.set_page_config("AI Code Debugger Pro", layout="wide")
    st.markdown(APP_CSS, unsafe_allow_html=True)
    
    if 'results' not in st.session_state:
        st.session_state.results = None
    
    st.markdown(HEADER_HTML, unsafe_allow_html=True)
    main_col, sidebar_col = st.columns([3, 1])
    with main_col:
        main_content()
    with sidebar_col:
        sidebar_content()

# ===== Styling =====
APP_CSS = """<style>
    .main { background: #0F172A; color: #F8FAFC; }
    .stCodeBlock { border-radius: 8px; background: #1E293B !important; }
</style>"""

HEADER_HTML = """<div style="background:linear-gradient(135deg,#7C3AED,#6D28D9);padding:2rem;border-radius:16px">
    <h1 style="color:white;margin:0">🧠 AI Code Debugger Pro</h1>
</div>"""

if __name__ == "__main__":
    init_app()
