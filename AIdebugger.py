import streamlit as st
import google.generativeai as genai
import json
import re
import time
import os
from PIL import Image
import io
from google.cloud import vision
from google.oauth2 import service_account

# ======================
# Configuration
# ======================
MAX_RETRIES = 3
RETRY_DELAY = 1.5  # seconds
MAX_CODE_LENGTH = 15000
SUPPORTED_LANGUAGES = ["python", "javascript", "java"]
SAFETY_SETTINGS = {
    'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE',
    'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE',
    'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE',
    'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_NONE'
}

ANALYSIS_PROMPT = """Analyze this {language} code and provide detailed feedback:
1. Identify all syntax errors with line numbers
2. Find logical errors with explanations
3. Suggest performance optimizations
4. Highlight security vulnerabilities

Return structured JSON response:
{{
    "metadata": {{
        "analysis_time": "...",
        "code_length": number,
        "language": "..."
    }},
    "issues": {{
        "syntax_errors": ["error details"],
        "logical_errors": ["error details"],
        "security_issues": ["vulnerability details"]
    }},
    "improvements": {{
        "corrected_code": "full_code",
        "optimizations": ["optimization details"],
        "security_fixes": ["fix details"]
    }}
}}

Code:
```{language}
{code}
```"""

# ======================
# Initialization
# ======================
def initialize_apis():
    """Initialize API clients with credentials"""
    try:
        # Configure Gemini
        genai.configure(api_key=st.secrets["GEMINI"]["api_key"])
        
        # Configure Vision API
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["GCP"]
        )
        vision_client = vision.ImageAnnotatorClient(credentials=credentials)
        
        return vision_client
        
    except Exception as e:
        st.error(f"API Initialization Failed: {str(e)}")
        st.stop()

vision_client = initialize_apis()

# ======================
# Image Processing
# ======================
def preprocess_image(image_bytes):
    """Enhance image quality for OCR"""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img = img.convert('L')  # Grayscale
        img = img.point(lambda x: 0 if x < 150 else 255)  # Thresholding
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()
    except Exception as e:
        st.error(f"Image Processing Error: {str(e)}")
        return None

def extract_code_from_image(image_file):
    """Extract code from image with validation"""
    try:
        processed_image = preprocess_image(image_file.read())
        if not processed_image:
            return None, "Image processing failed"
            
        image = vision.Image(content=processed_image)
        response = vision_client.text_detection(
            image=image,
            image_context={"language_hints": ["en"]}
        )
        
        if response.error.message:
            return None, f"Vision API Error: {response.error.message}"
            
        if not response.text_annotations:
            return None, "No text detected in image"
            
        raw_text = response.text_annotations[0].description
        
        # Validate code structure
        if not re.search(r'(def|function|class|{|}|;)', raw_text):
            return None, "No recognizable code structure"
            
        return raw_text, ""
    except Exception as e:
        return None, f"OCR Failed: {str(e)}"

# ======================
# Code Analysis
# ======================
def validate_code(code):
    """Validate code before analysis"""
    if not code or len(code.strip()) < 20:
        return False, "Code too short (minimum 20 characters)"
    if len(code) > MAX_CODE_LENGTH:
        return False, f"Code exceeds {MAX_CODE_LENGTH} character limit"
    return True, ""

def analyze_code(code, language):
    """Analyze code with retry logic"""
    for attempt in range(MAX_RETRIES):
        try:
            model = genai.GenerativeModel('gemini-pro', safety_settings=SAFETY_SETTINGS)
            response = model.generate_content(
                ANALYSIS_PROMPT.format(language=language, code=code),
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=4000
                )
            )
            
            if not response.text:
                raise ValueError("Empty API response")
                
            return parse_response(response.text)
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
            continue
    return {"error": "Analysis failed after multiple attempts"}

def parse_response(response_text):
    """Parse and validate API response"""
    try:
        # Clean response
        cleaned = re.sub(r'[\x00-\x1F]', '', response_text)
        
        # Try different parsing strategies
        json_str = None
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # Try extracting JSON from markdown code block
        json_match = re.search(r'```(?:json)?\n(.*?)```', cleaned, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Find JSON object in text
            json_str_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            if json_str_match:
                json_str = json_str_match.group()

        if json_str:
            result = json.loads(json_str)
            # Validate response structure
            if all(key in result for key in ["issues", "improvements"]):
                return result
        
        raise ValueError("Invalid JSON structure")
    except Exception as e:
        return {"error": f"Response Parsing Failed: {str(e)}"}

# ======================
# Streamlit UI
# ======================
def main():
    st.set_page_config(
        page_title="AI Code Debugger Pro",
        page_icon="🤖",
        layout="wide"
    )
    
    st.title("🤖 AI Code Debugger Pro")
    st.markdown("---")
    
    # File Upload Section
    upload_type = st.radio("Input Method:", ["📝 Paste Code", "📁 Upload File", "🖼️ Image"])
    
    code = None
    language = "python"
    
    # Handle different input methods
    if upload_type == "📝 Paste Code":
        code = st.text_area("Enter Code:", height=300)
        language = st.selectbox("Select Language:", SUPPORTED_LANGUAGES)
        
    elif upload_type == "📁 Upload File":
        file = st.file_uploader("Upload Code File", type=["py", "js", "java"])
        if file:
            try:
                code = file.read().decode()
                ext = file.name.split(".")[-1]
                language = {"py": "python", "js": "javascript", "java": "java"}.get(ext)
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
                return
            
    elif upload_type == "🖼️ Image":
        img_file = st.file_uploader("Upload Code Image", type=["png", "jpg", "jpeg"])
        if img_file:
            code, error = extract_code_from_image(img_file)
            if error:
                st.error(error)
            else:
                language = st.selectbox("Select Language:", SUPPORTED_LANGUAGES)
    
    # Analysis Section
    if code:
        st.markdown("---")
        st.subheader("🔍 Code Preview")
        st.code(code, language=language)
        
        if st.button("Analyze Code", type="primary"):
            is_valid, msg = validate_code(code)
            if not is_valid:
                st.error(msg)
                return
                
            with st.spinner("🧠 Analyzing Code (this may take 20-30 seconds)..."):
                start_time = time.time()
                result = analyze_code(code, language)
                analysis_time = time.time() - start_time
                
                if "error" in result:
                    st.error(f"Analysis Failed: {result['error']}")
                else:
                    display_results(result, language, analysis_time)

def display_results(result, lang, time_taken):
    """Display analysis results"""
    st.markdown("---")
    st.subheader("📊 Analysis Results")
    
    # Metadata
    with st.expander("📄 Metadata", expanded=False):
        st.write(f"Analysis Time: {time_taken:.2f}s")
        st.write(f"Language: {lang.capitalize()}")
    
    # Issues Column
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🚨 Identified Issues")
        
        with st.expander("Syntax Errors", expanded=True):
            if result.get("issues", {}).get("syntax_errors"):
                st.write("\n\n".join(f"• {e}" for e in result["issues"]["syntax_errors"]))
            else:
                st.success("No syntax errors found!")
                
        with st.expander("Logical Errors"):
            if result.get("issues", {}).get("logical_errors"):
                st.write("\n\n".join(f"• {e}" for e in result["issues"]["logical_errors"]))
            else:
                st.info("No logical errors found")
                
        with st.expander("Security Issues"):
            if result.get("issues", {}).get("security_issues"):
                st.write("\n\n".join(f"⚠️ {e}" for e in result["issues"]["security_issues"]))
            else:
                st.success("No security issues found!")
    
    # Improvements Column
    with col2:
        st.subheader("✨ Improvements")
        
        with st.expander("Corrected Code", expanded=True):
            st.code(result.get("improvements", {}).get("corrected_code", "No corrected code provided"), 
                  language=lang)
            
        with st.expander("Optimizations"):
            if result.get("improvements", {}).get("optimizations"):
                st.write("\n\n".join(f"• {o}" for o in result["improvements"]["optimizations"]))
            else:
                st.info("No optimizations suggested")
                
        with st.expander("Security Fixes"):
            if result.get("improvements", {}).get("security_fixes"):
                st.write("\n\n".join(f"🔒 {f}" for f in result["improvements"]["security_fixes"]))
            else:
                st.info("No security fixes needed")

if __name__ == "__main__":
    main()
