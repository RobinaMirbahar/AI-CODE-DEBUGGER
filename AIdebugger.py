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
MAX_RETRIES = 5
RETRY_DELAY = 2.5
MAX_CODE_LENGTH = 8000
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
        if "GEMINI" not in st.secrets or "GCP" not in st.secrets:
            raise ValueError("Missing required secrets configuration")

        genai.configure(api_key=st.secrets.GEMINI.api_key)
        credentials = service_account.Credentials.from_service_account_info(st.secrets.GCP)
        return vision.ImageAnnotatorClient(credentials=credentials)
        
    except Exception as e:
        st.error(f"API Initialization Failed: {str(e)}")
        st.stop()

vision_client = initialize_apis()

# ======================
# Validation Functions
# ======================
def validate_code(code):
    """Validate code before analysis"""
    if not code or len(code.strip()) < 20:
        return False, "Code too short (minimum 20 characters)"
    if len(code) > MAX_CODE_LENGTH:
        return False, f"Code exceeds {MAX_CODE_LENGTH} character limit"
    return True, ""

# ======================
# Image Processing
# ======================
def preprocess_image(image_bytes):
    """Enhance image quality for OCR"""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img = img.convert('L').point(lambda x: 0 if x < 150 else 255)
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
        response = vision_client.text_detection(image=image)
        
        if response.error.message:
            return None, f"Vision API Error: {response.error.message}"
            
        if not response.text_annotations:
            return None, "No text detected in image"
            
        raw_text = response.text_annotations[0].description
        if not re.search(r'(def|function|class|{|}|;)', raw_text):
            return None, "No recognizable code structure"
            
        return raw_text, ""
    except Exception as e:
        return None, f"OCR Failed: {str(e)}"

# ======================
# Code Analysis
# ======================
def analyze_code(code, language):
    """Analyze code with enhanced error handling"""
    for attempt in range(MAX_RETRIES):
        try:
            model = genai.GenerativeModel('gemini-pro', safety_settings=SAFETY_SETTINGS)
            code_chunks = [code[i:i+4000] for i in range(0, len(code), 4000)]
            responses = []
            
            for chunk in code_chunks:
                response = model.generate_content(
                    ANALYSIS_PROMPT.format(language=language, code=chunk),
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.1,
                        max_output_tokens=4000,
                        response_mime_type="application/json"
                    )
                )
                responses.append(response.text)
                
            return parse_response("".join(responses))
            
        except (genai.types.StopCandidateException, genai.types.BlockedPromptException) as e:
            st.error(f"Content safety violation: {str(e)}")
            return {"error": "Content blocked by safety filters"}
        except Exception as e:
            time.sleep(RETRY_DELAY * (attempt + 1))
            
    return {"error": f"Analysis failed after {MAX_RETRIES} attempts"}

def parse_response(response_text):
    """Enhanced JSON parsing with validation"""
    try:
        normalized = re.sub(r'(?<!\\)\\(?!["\\/bfnrt]|u[0-9a-fA-F]{4})', r'\\\\', response_text)
        
        # Try multiple parsing strategies
        for strategy in [json.loads, _parse_json_blocks]:
            try:
                result = strategy(normalized)
                if _validate_result(result):
                    return result
            except:
                continue
                
        return {"error": "Could not parse valid JSON response"}
    except Exception as e:
        return {"error": f"Parsing failed: {str(e)}"}

def _parse_json_blocks(text):
    """Extract JSON from markdown code blocks"""
    json_blocks = re.findall(r'```(?:json)?\n(.*?)\n```', text, re.DOTALL)
    return json.loads("\n".join(json_blocks))

def _validate_result(result):
    """Validate response structure"""
    required_keys = {
        'issues': ['syntax_errors', 'logical_errors', 'security_issues'],
        'improvements': ['corrected_code', 'optimizations', 'security_fixes']
    }
    return all(
        category in result and all(key in result[category] for key in keys)
        for category, keys in required_keys.items()
    )

# ======================
# Streamlit UI
# ======================
def main():
    st.set_page_config(page_title="AI Code Debugger Pro", page_icon="🤖", layout="wide")
    st.title("🤖 AI Code Debugger Pro")
    st.markdown("---")
    
    upload_type = st.radio("Input Method:", ["📝 Paste Code", "📁 Upload File", "🖼️ Image"])
    code = None
    language = "python"
    
    if upload_type == "📝 Paste Code":
        code = st.text_area("Enter Code:", height=300)
        language = st.selectbox("Select Language:", SUPPORTED_LANGUAGES)
    elif upload_type == "📁 Upload File":
        file = st.file_uploader("Upload Code File", type=["py", "js", "java"])
        if file:
            try:
                code = file.read().decode()
                language = {"py": "python", "js": "javascript", "java": "java"}.get(file.name.split(".")[-1])
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
    elif upload_type == "🖼️ Image":
        img_file = st.file_uploader("Upload Code Image", type=["png", "jpg", "jpeg"])
        if img_file:
            code, error = extract_code_from_image(img_file)
            if error:
                st.error(error)
            else:
                language = st.selectbox("Select Language:", SUPPORTED_LANGUAGES)
    
    if code:
        st.markdown("---")
        st.subheader("🔍 Code Preview")
        st.code(code, language=language)
        
        if st.button("Analyze Code", type="primary"):
            is_valid, msg = validate_code(code)
            if not is_valid:
                st.error(msg)
                return
                
            with st.spinner("🧠 Analyzing Code..."):
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
    
    with st.expander("📄 Metadata", expanded=False):
        st.write(f"Analysis Time: {time_taken:.2f}s | Language: {lang.capitalize()}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🚨 Identified Issues")
        _display_issues(result.get("issues", {}))
    
    with col2:
        st.subheader("✨ Improvements")
        _display_improvements(result.get("improvements", {}), lang)

def _display_issues(issues):
    with st.expander("Syntax Errors", expanded=True):
        if issues.get("syntax_errors"):
            st.write("\n\n".join(f"• {e}" for e in issues["syntax_errors"]))
        else:
            st.success("No syntax errors found!")
    
    with st.expander("Logical Errors"):
        if issues.get("logical_errors"):
            st.write("\n\n".join(f"• {e}" for e in issues["logical_errors"]))
        else:
            st.info("No logical errors found")
    
    with st.expander("Security Issues"):
        if issues.get("security_issues"):
            st.write("\n\n".join(f"⚠️ {e}" for e in issues["security_issues"]))
        else:
            st.success("No security issues found!")

def _display_improvements(improvements, lang):
    with st.expander("Corrected Code", expanded=True):
        st.code(improvements.get("corrected_code", "No corrected code provided"), language=lang)
    
    with st.expander("Optimizations"):
        if improvements.get("optimizations"):
            st.write("\n\n".join(f"• {o}" for o in improvements["optimizations"]))
        else:
            st.info("No optimizations suggested")
    
    with st.expander("Security Fixes"):
        if improvements.get("security_fixes"):
            st.write("\n\n".join(f"🔒 {f}" for f in improvements["security_fixes"]))
        else:
            st.info("No security fixes needed")

if __name__ == "__main__":
    main()
