import os
import re
import difflib
from datetime import datetime
import streamlit as st
import google.generativeai as genai

# Streamlit configuration MUST be first
st.set_page_config(
    page_title="AI Code Debugger Pro",
    page_icon="🤖",
    layout="wide"
)

# Configure API Keys
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        GEMINI_API_KEY = st.sidebar.text_input(
            "Enter Gemini API Key",
            type="password",
            help="Get from https://aistudio.google.com/app/apikey"
        )
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
    else:
        st.error("🔑 API Key required in secrets.toml, env vars, or input above")
        st.stop()

# Model Configuration
try:
    available_models = [m.name for m in genai.list_models()]
    model_name = "gemini-1.5-pro-latest" if "gemini-1.5-pro-latest" in available_models else "gemini-pro"
    
    MODEL = genai.GenerativeModel(
        model_name,
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
    st.error(f"Model initialization error: {str(e)}")
    st.stop()

# Core Functions
@st.cache_data(show_spinner=False)
def correct_code(code_snippet, language):
    """Analyze and correct code using Gemini AI"""
    try:
        lang = language.lower() if language != "auto-detect" else ""
        code_block = f"```{lang}\n{code_snippet}\n```" if lang else f"```\n{code_snippet}\n```"
        
        prompt = f"""
        You are an expert code correction assistant. Analyze, debug, and improve this code:
        {code_block}
        Provide markdown-formatted response with these exact sections:
        ### Corrected Code
        - Include line numbers in code blocks
        - Highlight key changes with comments
        
        ### Error Explanation
        - Categorize errors (syntax, logic, performance)
        - Explain each fix in bullet points
        
        ### Optimization Suggestions
        - Suggest efficiency improvements
        - Recommend best practices
        - Propose security enhancements
        """
        
        response = MODEL.generate_content(prompt)
        return response.text
    
    except Exception as e:
        return f"**API Error**: {str(e)}"

def generate_code_from_text(prompt_text, language):
    """Generate code from text description"""
    try:
        prompt = f"""
        You are an AI software developer. Generate {language} code based on:
        {prompt_text}
        Provide the output in markdown code blocks with syntax highlighting.
        """
        response = MODEL.generate_content(prompt)
        return response.text
    
    except Exception as e:
        return f"**API Error**: {str(e)}"

def format_code(code_snippet, language): 
    """AI-powered code formatting"""
    try:
        prompt = f"""
        Reformat this {language} code according to best practices:
        ```{language}
        {code_snippet}
        ```
        Apply:
        1. Standard style guide
        2. Proper indentation
        3. Consistent naming
        4. PEP8/ESLint equivalent
        """
        response = MODEL.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"**Formatting Error**: {str(e)}"

def parse_response(response_text):
    """Parse AI response into structured sections"""
    sections = {'code': '', 'explanation': '', 'improvements': ''}
    
    try:
        # Extract code block
        code_match = re.search(r'```[\w+]*\n(.*?)```', response_text, re.DOTALL)
        if code_match:
            sections['code'] = code_match.group(1).strip()
        
        # Extract error explanation
        explanation_match = re.search(r'### Error Explanation(.*?)### Optimization Suggestions', response_text, re.DOTALL)
        if explanation_match:
            sections['explanation'] = explanation_match.group(1).strip()
        
        # Extract optimizations
        improvements_match = re.search(r'### Optimization Suggestions(.*?)$', response_text, re.DOTALL)
        if improvements_match:
            sections['improvements'] = improvements_match.group(1).strip()
    
    except Exception as e:
        st.error(f"Response parsing error: {str(e)}")
    
    return sections

# UI Components
st.markdown("""
    <style>
        .stMarkdown pre {border-radius: 10px; padding: 15px!important;}
        .stCodeBlock {border: 1px solid #e0e0e0; border-radius: 8px;}
        .reportview-container {background: #f8f9fa;}
        .diff-added {background: #e6ffe6; padding: 2px 4px; border-radius: 3px;}
        .diff-removed {background: #ffe6e6; padding: 2px 4px; border-radius: 3px;}
        .stButton>button {width: 100%;}
    </style>
""", unsafe_allow_html=True)

if 'history' not in st.session_state:
    st.session_state.history = []

# Main Interface
st.title("🤖 AI Code Debugger Pro")
st.caption("Advanced code analysis powered by Google Gemini")

col1, col2 = st.columns([3, 1])
with col1:
    uploaded_file = st.file_uploader("📤 Upload code file", 
                                    type=["py","js","java","cpp","cs","go","rs","ts"])
    if uploaded_file:
        st.session_state['code'] = uploaded_file.read().decode("utf-8")
    
    code = st.text_area("📝 Paste code here:", 
                       height=300, 
                       value=st.session_state.get('code', ''),
                       help="Supports 10+ programming languages")
    
    prompt_text = st.text_area("💡 Describe functionality:", 
                              height=150,
                              help="AI will generate code based on your description")

with col2:
    lang = st.selectbox("🌐 Language:", 
                       ["Auto-Detect", "Python", "JavaScript", "Java", 
                        "C++", "C#", "Go", "Rust", "TypeScript"])
    
    analysis_type = st.radio("🔍 Analysis Type:", 
                            ["Full Audit", "Quick Fix", "Security Review"])
    
    st.info("💡 Tip: Use 'Full Audit' for complete code review")

# Action Buttons
col_btn1, col_btn2, col_btn3 = st.columns(3)
with col_btn1:
    analyze_clicked = st.button("🚀 Analyze Code", use_container_width=True)
with col_btn2:
    format_clicked = st.button("✨ Auto-Format", use_container_width=True)
with col_btn3:
    generate_clicked = st.button("🛠 Generate Code", use_container_width=True)

# Handle Actions
if analyze_clicked:
    if not code.strip():
        st.error("⚠️ Please input code or upload a file")
    else:
        with st.spinner("🔬 Deep analysis in progress..."):
            start_time = datetime.now()
            response = correct_code(code, lang.lower() if lang != "Auto-Detect" else "auto-detect")
            process_time = (datetime.now() - start_time).total_seconds()
            
            # Store in history
            st.session_state.history.append({
                'code': code,
                'response': response,
                'timestamp': start_time
            })
        
        if response.startswith("**API Error**"):
            st.error(response)
        else:
            sections = parse_response(response)
            st.success(f"✅ Analysis completed in {process_time:.2f}s")
            
            tab1, tab2, tab3 = st.tabs(["🛠 Corrected Code", "📖 Explanation", "💎 Optimizations"])
            
            with tab1:
                st.subheader("Improved Code")
                st.code(sections['code'], language=lang.lower() if lang != "Auto-Detect" else "")
            
            with tab2:
                st.markdown(f"### Error Breakdown\n{sections['explanation']}")
            
            with tab3:
                st.markdown(f"### Optimization Recommendations\n{sections['improvements']}")

if format_clicked:
    if not code.strip():
        st.error("⚠️ No code to format")
    else:
        with st.spinner("🎨 Formatting code..."):
            formatted_code = format_code(code, lang)
            st.code(formatted_code, language=lang.lower())

if generate_clicked:
    if not prompt_text.strip():
        st.error("⚠️ Please describe the functionality")
    else:
        with st.spinner("🤖 Generating code..."):
            generated_code = generate_code_from_text(prompt_text, lang)
            st.code(generated_code, language=lang.lower())

# History Section
st.markdown("---")
st.markdown("### 📚 Analysis History")
for idx, item in enumerate(st.session_state.history[-3:]):
    with st.expander(f"Analysis {item['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}"):
        st.caption("Original Code Snippet")
        st.code(item['code'][:200] + ("..." if len(item['code']) > 200 else ""))
        st.caption("AI Response Summary")
        st.write(item['response'][:300] + ("..." if len(item['response']) > 300 else ""))

# Security Footer
st.markdown("---")
st.markdown("🔒 **Security Note:** All code is processed securely through Google's API and not stored. API keys are never logged or shared.")

# Error Handling
if 'error' in st.session_state:
    st.error(st.session_state.error)
    del st.session_state.error
