import streamlit as st
import json
import os
import re
import imghdr
import time
import google.generativeai as genai
from google.cloud import vision
from google.oauth2 import service_account
from google.api_core.exceptions import GoogleAPICallError, RetryError
from concurrent.futures import TimeoutError

# Constants
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_IMAGE_TYPES = ["jpeg", "png"]  # imghdr returns 'jpeg' for JPG files
ALLOWED_CODE_EXTENSIONS = ["py", "java", "js", "cpp", "html", "css", "php"]
MAX_CODE_LENGTH = 5000

# Initialize page configuration
st.set_page_config(page_title="AI Code Debugger", layout="wide")

# ========== SESSION STATE ==========
session_defaults = {
    'chat_history': [],
    'analysis_results': {},
    'current_code': "",
    'processed_file_id': None,
    'current_input_method': None,
    'file_extension': None,
    'processing': False
}

for key, value in session_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ========== CREDENTIAL HANDLING ==========
try:
    credentials = None
    google_api_key = os.getenv("GOOGLE_API_KEY")
    
    if not google_api_key:
        st.error("GOOGLE_API_KEY environment variable is required")
        st.stop()
    
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
    
    genai.configure(api_key=google_api_key)
    MODEL = genai.GenerativeModel('gemini-pro',
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
    st.error(f"Initialization error: {str(e)}")
    st.stop()

# ========== CORE FUNCTIONS ==========
def validate_image(file) -> tuple[bool, str]:
    try:
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        if file_size > MAX_IMAGE_SIZE:
            return False, f"File too large ({file_size//1024}KB > 5MB)"
        
        # Check file type
        image_type = imghdr.what(file)
        if image_type not in ALLOWED_IMAGE_TYPES:
            return False, f"Unsupported format: {image_type or 'unknown'}"
            
        return True, ""
    except Exception as e:
        return False, f"Validation error: {str(e)}"

def validate_code_file(file) -> tuple[bool, str, str]:
    try:
        filename = file.name.lower()
        ext = filename.split('.')[-1]
        if ext not in ALLOWED_CODE_EXTENSIONS:
            return False, "", f"Unsupported file type: .{ext}"
        
        # Read and validate content
        content = file.read().decode('utf-8')
        if len(content) > MAX_CODE_LENGTH:
            return False, "", f"File too large ({len(content)} > {MAX_CODE_LENGTH} chars)"
        
        # Remove strict code structure validation
        return True, content, ext
    except UnicodeDecodeError:
        return False, "", "Invalid text encoding"
    except Exception as e:
        return False, "", f"Validation error: {str(e)}"

def extract_code_from_image(image) -> tuple[bool, str]:
    try:
        if not credentials:
            return False, "Missing Google Cloud credentials"
            
        client = vision.ImageAnnotatorClient(credentials=credentials)
        content = image.read()
        
        # Retry mechanism with exponential backoff
        max_retries = 3
        response = None
        for attempt in range(max_retries):
            try:
                response = client.text_detection(
                    image=vision.Image(content=content),
                    timeout=30
                )
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                time.sleep(2 ** attempt)

        if response.error.message:
            return False, f"API Error: {response.error.message}"
            
        if not response.text_annotations:
            return False, "No text detected"
            
        raw_text = response.text_annotations[0].description
        # Improved text cleaning
        cleaned = re.sub(r'\n{3,}', '\n\n', raw_text).strip()
        cleaned = re.sub(r'(?<!\n)\n(?!\n)', ' ', cleaned)  # Remove single newlines
        return True, cleaned
        
    except TimeoutError:
        return False, "OCR processing timed out"
    except (GoogleAPICallError, RetryError) as e:
        return False, f"API Error: {str(e)}"
    except Exception as e:
        return False, f"Processing Error: {str(e)}"

def analyze_code(code: str, language: str) -> dict:
    try:
        prompt = f"""**CODE ANALYSIS REQUEST**
Return JSON in this EXACT format:
{{
    "bugs": ["Line 5: Missing semicolon"],
    "fixes": ["Add semicolon at line 5"],
    "corrected_code": "function example() {{\\n  console.log('fixed');\\n}}",
    "optimizations": ["Use const instead of let"],
    "explanation": ["Semicolons are required..."]
}}

**RULES:**
1. Output ONLY valid JSON
2. Escape special characters
3. Maintain array lengths

**{language.upper()} CODE:**
{code}
"""
        response = MODEL.generate_content(prompt)
        raw_text = response.text.strip()
        
        # Improved JSON cleaning
        cleaned = re.sub(r'(?i)^\s*(```json|```)', '', raw_text)
        cleaned = re.sub(r'[\x00-\x1F]', '', cleaned)
        repaired = (
            cleaned.replace("'", '"')
            .replace("True", "true")
            .replace("False", "false")
            .replace("None", "null")
            .replace(",\n}", "\n}")
        )
        
        return json.loads(repaired)
    except json.JSONDecodeError as e:
        st.error(f"JSON Parse Error: {str(e)}")
        return {"error": "Failed to parse AI response"}
    except Exception as e:
        return {"error": f"Analysis failed: {str(e)}"}

# ========== SIDEBAR ==========
with st.sidebar:
    st.title("🧠 AI Assistant")
    st.markdown("---")
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    st.markdown("---")
    st.subheader("💡 Usage Tips")
    st.markdown("""
    - **Images:** Clear screenshots <5MB
    - **Files:** Supported: Python, Java, JS, C++
    - **Code:** Max 5000 characters
    """)

# ========== MAIN INTERFACE ==========
st.title("🛠️ AI-Powered Code Debugger")

# Input method selection
input_method = st.radio(
    "SELECT INPUT METHOD:",
    ["📷 Upload Image", "📁 Upload File", "📝 Paste Code"],
    horizontal=True,
    key="input_method"
)

# Reset state when input method changes
if st.session_state.current_input_method != input_method:
    st.session_state.processed_file_id = None
    st.session_state.current_input_method = input_method
    st.session_state.file_extension = None
    st.session_state.processing = False
    st.session_state.current_code = ""
    st.session_state.analysis_results = {}

error_message = ""
language = "text"

# Image Upload Handling
if input_method == "📷 Upload Image":
    img_file = st.file_uploader(
        "Upload Code Screenshot",
        type=['png', 'jpg', 'jpeg'],
        help="Max 5MB, PNG/JPG/JPEG only"
    )
    
    if img_file and not st.session_state.processing:
        current_file_id = f"image_{img_file.name}_{img_file.size}"
        
        if st.session_state.processed_file_id != current_file_id:
            st.session_state.processing = True
            with st.spinner("Extracting code (30s max)..."):
                try:
                    is_valid, validation_msg = validate_image(img_file)
                    
                    if not is_valid:
                        error_message = f"❌ Invalid image: {validation_msg}"
                        st.session_state.processed_file_id = None
                        st.session_state.current_code = ""
                    else:
                        success, result = extract_code_from_image(img_file)
                        
                        if success:
                            st.session_state.processed_file_id = current_file_id
                            st.session_state.current_code = result
                            st.session_state.analysis_results = {}
                        else:
                            error_message = f"❌ Extraction failed: {result}"
                            st.session_state.processed_file_id = None
                            st.session_state.current_code = ""
                finally:
                    st.session_state.processing = False

# File Upload Handling
elif input_method == "📁 Upload File":
    code_file = st.file_uploader(
        "Upload Code File",
        type=ALLOWED_CODE_EXTENSIONS,
        help=f"Supported formats: {', '.join(ALLOWED_CODE_EXTENSIONS)}"
    )
    
    if code_file and not st.session_state.processing:
        current_file_id = f"file_{code_file.name}_{code_file.size}"
        
        if st.session_state.processed_file_id != current_file_id:
            st.session_state.processing = True
            with st.spinner("Validating file..."):
                try:
                    is_valid, content, ext = validate_code_file(code_file)
                    
                    if not is_valid:
                        error_message = f"❌ Invalid file: {content}"
                        st.session_state.processed_file_id = None
                        st.session_state.file_extension = None
                        st.session_state.current_code = ""
                    else:
                        st.session_state.processed_file_id = current_file_id
                        st.session_state.current_code = content
                        st.session_state.file_extension = ext
                        st.session_state.analysis_results = {}
                        language = {
                            "py": "python", "java": "java", 
                            "js": "javascript", "cpp": "cpp",
                            "html": "html", "css": "css", "php": "php"
                        }.get(ext, "text")
                finally:
                    st.session_state.processing = False

# Code Paste Handling
else:
    new_code = st.text_area(
        "Paste Code Here:",
        height=300,
        max_chars=MAX_CODE_LENGTH,
        value=st.session_state.current_code,
        placeholder="// Paste your code here...",
        help=f"Max {MAX_CODE_LENGTH} characters",
        key="pasted_code"
    )
    
    if new_code != st.session_state.current_code:
        st.session_state.current_code = new_code
        st.session_state.analysis_results = {}

# Display current code
if st.session_state.current_code:
    st.subheader("📄 Current Code")
    st.code(st.session_state.current_code, language=language)

# Error messages
if error_message:
    st.error(error_message)

# Analysis Trigger
if st.session_state.current_code.strip() and not error_message:
    if st.button("🚀 Analyze Code", use_container_width=True):
        with st.spinner("Analyzing code (20-30 seconds)..."):
            st.session_state.analysis_results = analyze_code(
                st.session_state.current_code,
                language
            )

# Results Display
if st.session_state.analysis_results:
    results = st.session_state.analysis_results
    
    if "error" in results:
        st.error(f"Analysis Error: {results['error']}")
    else:
        st.subheader("🔍 Analysis Results")
        
        with st.expander("🐛 Bugs", expanded=True):
            for bug in results.get("bugs", []):
                st.error(f"- {bug}")
        
        with st.expander("🛠️ Suggested Fixes"):
            for fix in results.get("fixes", []):
                st.info(f"- {fix}")
        
        with st.expander("✨ Optimized Code"):
            st.code(results.get("corrected_code", ""), language=language)
        
        with st.expander("📖 Detailed Explanation"):
            for exp in results.get("explanation", []):
                st.write(f"- {exp}")

# Chat Interface
user_query = st.chat_input("Ask questions about the code...")
if user_query and MODEL and not st.session_state.processing:
    try:
        st.session_state.chat_history.append({"role": "user", "content": user_query})
        with st.spinner("Generating response..."):
            response = MODEL.generate_content(user_query)
            if response.text:
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response.text
                })
                st.rerun()
    except Exception as e:
        st.error(f"Chat error: {str(e)}")
