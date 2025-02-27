import streamlit as st
import json
import re
from google.cloud import vision
from google.oauth2 import service_account
from io import BytesIO

# Constants
MAX_CODE_LENGTH = 10000
ALLOWED_CODE_EXTENSIONS = ["py", "java", "js", "cpp", "c", "html", "css", "sh", "rb", "go"]

# Load Google Vision API credentials
try:
    credentials = service_account.Credentials.from_service_account_info(json.loads(st.secrets["google_api_credentials"]))
    client = vision.ImageAnnotatorClient(credentials=credentials)
except Exception as e:
    st.error(f"Failed to load Google API credentials: {e}")
    credentials = None

# Initialize session state
if "current_input_method" not in st.session_state:
    st.session_state.current_input_method = "Text Input"
if "current_code" not in st.session_state:
    st.session_state.current_code = ""
if "file_extension" not in st.session_state:
    st.session_state.file_extension = None
if "processing" not in st.session_state:
    st.session_state.processing = False
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = {}

def extract_code_from_image(image) -> tuple[bool, str]:
    """Extracts text/code from an uploaded image using Google Vision API."""
    try:
        if not credentials:
            return False, "Google API credentials missing."

        content = image.read()
        response = client.text_detection(image=vision.Image(content=content))

        if response.error.message:
            return False, f"Vision API Error: {response.error.message}"

        if not response.text_annotations:
            return False, "No text detected in image."

        raw_text = response.text_annotations[0].description
        cleaned = re.sub(r'\n{3,}', '\n\n', raw_text).strip()
        return True, cleaned

    except Exception as e:
        return False, f"Image processing error: {str(e)}"

def validate_code_file(file) -> tuple[bool, str, str]:
    """Validates the uploaded code file and extracts content if valid."""
    try:
        filename = file.name.lower()
        ext = filename.split('.')[-1]
        if ext not in ALLOWED_CODE_EXTENSIONS:
            return False, "", f"Unsupported file type: .{ext}"

        file.seek(0)
        content = file.read().decode('utf-8')
        file.seek(0)

        if len(content) > MAX_CODE_LENGTH:
            return False, "", f"File too large ({len(content)} > {MAX_CODE_LENGTH} chars)"

        if not any(c in content for c in ['{', '(', ';', 'def', 'class', '<']):
            return False, "", "File does not appear to contain code."

        return True, content, ext

    except UnicodeDecodeError:
        return False, "", "Invalid text encoding in file."
    except Exception as e:
        return False, "", f"File processing error: {str(e)}"

def analyze_code(code: str, language: str):
    """Runs AI-based code analysis (mocked for now)."""
    return {
        "syntax": "Valid" if "def" in code or "class" in code else "Potential Issues",
        "complexity": "Moderate" if len(code) < 500 else "High",
        "comments": "Needs more comments" if code.count("#") < 5 else "Well documented"
    }

# Sidebar: Choose Input Method
input_method = st.sidebar.radio("Choose input method:", ["Text Input", "Upload File", "Upload Image"])

# Reset session state when switching input methods
if st.session_state.current_input_method != input_method:
    st.session_state.current_input_method = input_method
    st.session_state.current_code = ""
    st.session_state.file_extension = None
    st.session_state.analysis_results = {}
    st.session_state.processing = False
    st.rerun()

# User Input Handling
if input_method == "Text Input":
    st.session_state.current_code = st.text_area("Enter your code:", st.session_state.current_code, height=200)

elif input_method == "Upload File":
    uploaded_file = st.file_uploader("Upload a code file:", type=ALLOWED_CODE_EXTENSIONS)
    if uploaded_file:
        success, code, ext = validate_code_file(uploaded_file)
        if success:
            st.session_state.current_code = code
            st.session_state.file_extension = ext
        else:
            st.error(code)  # Show error message

elif input_method == "Upload Image":
    uploaded_image = st.file_uploader("Upload an image with code:", type=["png", "jpg", "jpeg"])
    if uploaded_image:
        success, extracted_code = extract_code_from_image(uploaded_image)
        if success:
            st.session_state.current_code = extracted_code
        else:
            st.error(extracted_code)  # Show error message

# Show Extracted Code
if st.session_state.current_code:
    st.subheader("Extracted Code:")
    st.code(st.session_state.current_code, language=st.session_state.file_extension or "python")

    if st.button("Analyze Code"):
        st.session_state.processing = True
        st.session_state.analysis_results = analyze_code(st.session_state.current_code, st.session_state.file_extension or "python")

# Show Analysis Results
if st.session_state.analysis_results:
    st.subheader("Analysis Results")
    for key, value in st.session_state.analysis_results.items():
        st.write(f"**{key.capitalize()}**: {value}")

