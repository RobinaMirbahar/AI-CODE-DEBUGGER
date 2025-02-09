import google.generativeai as genai
import streamlit as st
import re
from datetime import datetime

# Configure Gemini API
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

@st.cache_data(show_spinner=False)
def correct_code(code_snippet, language, analysis_type="Full Audit"):
    """Enhanced AI-driven code analysis"""
    try:
        lang = language.lower() if language != "Auto-Detect" else "python"
        code_block = f"```{lang}\n{code_snippet}\n```"

        base_prompt = f"""
        You are an AI Code Debugger. Given the {lang} code below, follow these strict steps:

        1️⃣ **Correct the Code**  
        - Fix syntax errors, logical issues, and best practices  
        - Preserve original structure and comments  
        - Output **only the corrected code** inside a code block  

        2️⃣ **Error Explanation**  
        - List errors found and describe how they were fixed  
        - Use bullet points for readability  

        3️⃣ **Best Practices & Recommendations**  
        - Suggest improvements for performance, security, and maintainability  

        💡 **Important Formatting Rules:**  
        ✅ Use `### CORRECTED CODE` before the fixed code  
        ✅ Use `### ERROR EXPLANATION` for explanations  
        ✅ Use `### BEST PRACTICES & RECOMMENDATIONS` for best practices  

        Here is the code to analyze:
        ```{lang}
        {code_snippet}
        ```
        """

        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(base_prompt)
        return response.text
    except Exception as e:
        return f"**API Error**: {str(e)}"

def parse_response(response_text):
    """Improved response parser for AI-generated corrections"""
    sections = {'code': '', 'explanation': '', 'recommendations': ''}

    try:
        corrected_code_match = re.search(r'### CORRECTED CODE\s*```.*?\n([\s\S]+?)```', response_text, re.IGNORECASE)
        explanation_match = re.search(r'### ERROR EXPLANATION\s*([\s\S]+?)(?=###|\Z)', response_text, re.IGNORECASE)
        recommendations_match = re.search(r'### BEST PRACTICES & RECOMMENDATIONS\s*([\s\S]+?)(?=###|\Z)', response_text, re.IGNORECASE)

        sections['code'] = corrected_code_match.group(1).strip() if corrected_code_match else "⚠️ No valid corrections detected"
        sections['explanation'] = explanation_match.group(1).strip() if explanation_match else "⚠️ No errors detected"
        sections['recommendations'] = recommendations_match.group(1).strip() if recommendations_match else "⚠️ No recommendations available"

    except Exception as e:
        st.error(f"⚠️ Parsing Error: {str(e)}")

    return sections

# Streamlit UI Configuration
st.set_page_config(page_title="🚀 AI Code Debugger Pro", page_icon="💡", layout="wide")

st.markdown("""
    <style>
        .stMarkdown pre {border-radius: 10px; padding: 15px!important;}
        .stTextArea textarea {font-family: monospace !important;}
        .highlight {border-left: 3px solid #4CAF50; padding-left: 10px;}
        .stButton>button {transition: all 0.3s ease;}
        .stButton>button:hover {transform: scale(1.05);}
        .stExpander .st-ae {border-radius: 10px!important;}
    </style>
""", unsafe_allow_html=True)

if 'history' not in st.session_state:
    st.session_state.history = []
if 'code' not in st.session_state:
    st.session_state.code = ""

st.title("🚀 AI Code Debugger Pro")
col1, col2 = st.columns([3, 1])

with col1:
    uploaded_file = st.file_uploader("📤 Upload Code", type=["py","js","java","cpp","cs","go"])
    if uploaded_file:
        try:
            st.session_state.code = uploaded_file.read().decode("utf-8")
        except UnicodeDecodeError:
            st.error("⚠️ Invalid file format - please upload text-based source files")

    code = st.text_area("📝 Code Editor", height=300, 
                      value=st.session_state.code,
                      help="Write or paste your code here")

with col2:
    lang = st.selectbox("🌐 Language", ["Auto-Detect", "Python", "JavaScript", 
                                      "Java", "C++", "C#", "Go", "Rust"])
    analysis_type = st.radio("🔍 Analysis Mode", ["Full Audit", "Quick Fix", "Security Review"])

col3, col4 = st.columns(2)
with col3:
    analyze_btn = st.button("🔍 Analyze Code", use_container_width=True)
with col4:
    doc_btn = st.button("📚 Generate Docs", use_container_width=True)

if analyze_btn:
    if code.strip():
        with st.spinner("🧠 Analyzing code..."):
            response = correct_code(code, lang, analysis_type)
            sections = parse_response(response)

            tab1, tab2, tab3 = st.tabs(["🛠 Corrected Code", "📖 Error Explanation", "✅ Best Practices"])
            
            with tab1:
                st.code(sections['code'], language=lang.lower())
            
            with tab2:
                st.markdown(f"```\n{sections['explanation']}\n```")
            
            with tab3:
                st.markdown(f"```\n{sections['recommendations']}\n```")
            
            st.session_state.history.append({
                'code': code,
                'response': response,
                'timestamp': datetime.now()
            })
    else:
        st.error("⚠️ Please input code to analyze")

if doc_btn:
    if code.strip():
        with st.spinner("📝 Generating documentation..."):
            docs = f"📖 Auto-generated API documentation for {lang} code:\n\n```yaml\n# OpenAPI Specification\n# TODO: Implement AI-generated documentation\n```"
            st.markdown(docs)
            st.download_button("📥 Download Spec", docs, file_name="api_spec.yaml", mime="text/yaml")
    else:
        st.error("⚠️ Please input code to document")

with st.sidebar:
    st.subheader("💬 Code Chat")
    user_question = st.text_input("Ask about the code:")
    if user_question and code.strip():
        st.markdown(f"**AI Response:**\n\n🚀 *AI explanation coming soon...*")  # Placeholder

    st.subheader("📚 History")
    for idx, item in enumerate(st.session_state.history[-3:]):
        with st.expander(f"Analysis {idx+1} - {item['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}"):
            st.code(item['code'][:300] + "...")

st.markdown("---")
st.markdown("🔒 *Code processed securely via Google's AI APIs*")
