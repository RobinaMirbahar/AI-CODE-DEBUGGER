import streamlit as st
import json
import os
import re
import imghdr
import time
import google.generativeai as genai
from google.cloud import vision
from google.oauth2 import service_account

# Constants
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_IMAGE_TYPES = ["jpeg", "png", "jpg"]
ALLOWED_CODE_EXTENSIONS = ["py", "java", "js", "cpp", "html", "css", "php"]
MAX_CODE_LENGTH = 5000

# Initialize Streamlit app
st.set_page_config(page_title="AI Code Debugger", layout="wide")

# Initialize session state
def init_session():
    default_values = {
        'chat_history': [],
        'analysis_results': {},
        'current_code': "",
        'file_extension': None,
        'processing': False
    }
    for key, value in default_values.items():
        if key not in st.session_state:
            st.session_state[key] = value
init_session()

# Google API setup
try:
    credentials = None
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if cred_json := os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON"):
        credentials_dict = json.loads(cred_json)
        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict,
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
    genai.configure(api_key=google_api_key)
    MODEL = genai.GenerativeModel('gemini-pro')
except Exception as e:
    st.error(f"Initialization error: {str(e)}")
    st.stop()

# Function to validate images
def validate_image(file):
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    if file_size > MAX_IMAGE_SIZE:
        return False, "File too large (max 5MB)"
    image_type = imghdr.what(file)
    if image_type not in ALLOWED_IMAGE_TYPES:
        return False, "Unsupported image format"
    return True, ""

# Function to validate and extract code from a file
def validate_code_file(file):
    ext = file.name.split('.')[-1].lower()
    if ext not in ALLOWED_CODE_EXTENSIONS:
        return False, "", "Unsupported file type"
    content = file.read().decode('utf-8')
    if len(content) > MAX_CODE_LENGTH:
        return False, "", "File too large"
    return True, content, ext

# Function to extract text from an image
def extract_code_from_image(image):
    try:
        client = vision.ImageAnnotatorClient(credentials=credentials)
        content = image.read()
        response = client.text_detection(image=vision.Image(content=content))
        if response.error.message:
            return False, "API Error"
        if not response.text_annotations:
            return False, "No text detected"
        return True, response.text_annotations[0].description.strip()
    except Exception as e:
        return False, str(e)

# Function to analyze code
def analyze_code(code, language):
    try:
        prompt = f"""
        Analyze the following {language} code and return JSON with bugs, fixes, optimized code, and explanations.
        Code:
        {code}
        """
        response = MODEL.generate_content(prompt)
        return json.loads(response.text)
    except Exception as e:
        return {"error": str(e)}

# Sidebar for chat history
with st.sidebar:
    st.title("🧠 AI Assistant")
    for msg in st.session_state.chat_history:
        st.markdown(f"**{msg['role'].capitalize()}:** {msg['content']}")

# Main app
st.title("🛠️ AI Code Debugger")
input_method = st.radio("Select Input Method:", ["📷 Upload Image", "📁 Upload File", "📝 Paste Code"], horizontal=True)

# Reset state on input change
if "last_input_method" not in st.session_state or st.session_state.last_input_method != input_method:
    st.session_state.current_code = ""
    st.session_state.analysis_results = {}
    st.session_state.last_input_method = input_method

# Handle different inputs
if input_method == "📷 Upload Image":
    img_file = st.file_uploader("Upload Image", type=ALLOWED_IMAGE_TYPES)
    if img_file:
        valid, msg = validate_image(img_file)
        if valid:
            success, extracted_code = extract_code_from_image(img_file)
            if success:
                st.session_state.current_code = extracted_code
            else:
                st.error(extracted_code)
        else:
            st.error(msg)

elif input_method == "📁 Upload File":
    code_file = st.file_uploader("Upload Code File", type=ALLOWED_CODE_EXTENSIONS)
    if code_file:
        valid, content, ext = validate_code_file(code_file)
        if valid:
            st.session_state.current_code = content
            st.session_state.file_extension = ext
        else:
            st.error(content)

elif input_method == "📝 Paste Code":
    st.session_state.current_code = st.text_area("Paste Code Here:", height=300, max_chars=MAX_CODE_LENGTH)

# Show extracted code
if st.session_state.current_code:
    st.subheader("📄 Extracted Code")
    st.code(st.session_state.current_code, language=st.session_state.file_extension or "text")

# Analyze Code
if st.button("🚀 Analyze Code") and st.session_state.current_code.strip():
    with st.spinner("Analyzing code..."):
        st.session_state.analysis_results = analyze_code(st.session_state.current_code, st.session_state.file_extension or "text")

# Display results
if st.session_state.analysis_results:
    results = st.session_state.analysis_results
    if "error" in results:
        st.error(results["error"])
    else:
        st.subheader("🔍 Analysis Results")
        st.write("**Bugs:**", results.get("bugs", []))
        st.write("**Fixes:**", results.get("fixes", []))
        st.write("**Optimized Code:**")
        st.code(results.get("corrected_code", ""))
        st.write("**Explanation:**", results.get("explanation", []))
