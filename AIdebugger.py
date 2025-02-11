import google.generativeai as genai
import google.cloud.vision as vision
import streamlit as st
import re
import io

# ========== AI Code Debugger Workflow Integration ==========
# 1. Code Input & Preprocessing
# 2. Static Analysis
# 3. Dynamic Analysis (Runtime Debugging)
# 4. AI-Assisted Debugging
# 5. Automated Testing
# 6. Fix Suggestions & Auto-Refactoring
# 7. Verification & Final Testing

# Initialize Gemini API once
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# Initialize Google Vision API client
vision_client = vision.ImageAnnotatorClient()

# ========== Constants & Configs ==========
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

# Initialize model once
MODEL = genai.GenerativeModel('gemini-pro',
    safety_settings=SAFETY_SETTINGS,
    generation_config=GENERATION_CONFIG
)

# ========== Helper Functions ==========
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
    """Efficient code block parsing with regex"""
    return re.findall(r'```[a-z]*\n(.*?)```', response_text, re.DOTALL)

def extract_text_from_image(image_file):
    """Extract text from uploaded image using Google Vision API"""
    content = image_file.read()
    image = vision.Image(content=content)
    response = vision_client.text_detection(image=image)
    texts = response.text_annotations
    return texts[0].description if texts else ""

# ========== Core Debugging Functions ==========
def analyze_code(code_snippet, language):
    """Optimized analysis function with AI-assisted debugging"""
    if not code_snippet.strip():
        return {"error": "⚠️ No code provided"}

    lang = language.lower() if language != "Auto-Detect" else "python"
    
    prompt = f"""Analyze and debug this {lang} code:
    ```{lang}
    {code_snippet}
    ```
    Provide structured response with:
    - Static analysis (syntax errors, linting, type checking)
    - Runtime analysis (execution flow, error detection)
    - AI-assisted debugging suggestions
    - Optimized code refactoring
    """

    try:
        response = MODEL.generate_content(prompt)
        return handle_response(response)
    except Exception as e:
        return {"error": f"⚠️ Analysis failed: {str(e)}"}

def handle_response(response):
    """Centralized response handler"""
    response_text, error = handle_api_response(response)
    return error_response(error) if error else parse_response(response_text)

def error_response(error):
    """Standard error formatting"""
    return {"error": error}

def parse_response(response_text):
    """Efficient response parsing with structured debugging workflow"""
    code_blocks = parse_code_blocks(response_text)
    sections = re.split(r'### \w+', response_text)
    
    return {
        'corrected_code': code_blocks[0].strip() if code_blocks else '',
        'static_analysis': extract_items(sections, 'STATIC ANALYSIS'),
        'runtime_analysis': extract_items(sections, 'RUNTIME ANALYSIS'),
        'debugging_suggestions': extract_items(sections, 'AI-ASSISTED DEBUGGING'),
        'optimizations': extract_items(sections, 'CODE REFACTORING')
    }

def extract_items(sections, header):
    """Efficient section item extraction"""
    for section in sections:
        if header in section:
            return [line.strip() for line in section.split('\n') if line.strip()]
    return []

# ========== UI Components ==========
def main_content():
    """Main content area components"""
    with st.container():
        uploaded_file = st.file_uploader("📤 Upload Code File or Image", type=["py", "js", "java", "cpp", "cs", "go", "png", "jpg", "jpeg"])
        
        if uploaded_file is not None:
            if uploaded_file.type in ["image/png", "image/jpeg"]:
                extracted_text = extract_text_from_image(uploaded_file)
                st.text_area("Extracted Code", extracted_text, height=400)
            else:
                code = uploaded_file.getvalue().decode()
                st.text_area("📝 Editor", code, height=400)
        
        if st.button("🚀 Debug Code", use_container_width=True) and extracted_text.strip():
            with st.spinner("Analyzing..."):
                st.session_state.results = analyze_code(extracted_text, "Python")

def sidebar_content():
    """Sidebar components"""
    with st.container(border=True):
        st.markdown("### ⚙️ Settings")
        lang = st.selectbox("Language", ["Auto-Detect", "Python", "JavaScript", "Java", "C++", "C#", "Go", "Rust"])
        
        if st.button("💡 Generate Code", help="Describe functionality in main input"):
            # Implement AI code generation logic
            pass

# ========== App Initialization ==========
def init_app():
    """Initialize Streamlit app"""
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

if __name__ == "__main__":
    init_app()
