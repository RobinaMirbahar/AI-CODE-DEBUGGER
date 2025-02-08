import google.generativeai as genai
import streamlit as st
import difflib
import re
from datetime import datetime

# Configure Gemini API
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

@st.cache_data(show_spinner=False)
def correct_code(code_snippet, language):
    """Analyze and correct code using Gemini AI with enhanced error handling."""
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
        
        model = genai.GenerativeModel('gemini-2.0-pro-exp')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"**API Error**: {str(e)}"

def parse_response(response_text):
    """Parse AI response into structured sections"""
    sections = {'code': '', 'explanation': '', 'improvements': ''}
    
    code_match = re.search(r'```[^
]*\n(.*?)```', response_text, re.DOTALL)
    if code_match:
        sections['code'] = code_match.group(1)
    
    explanation_match = re.search(r'### Error Explanation(.*?)### Optimization Suggestions', response_text, re.DOTALL)
    if explanation_match:
        sections['explanation'] = explanation_match.group(1).strip()
    
    improvements_match = re.search(r'### Optimization Suggestions(.*?)$', response_text, re.DOTALL)
    if improvements_match:
        sections['improvements'] = improvements_match.group(1).strip()
    
    return sections

# Streamlit UI Configuration
st.set_page_config(page_title="AI Code Debugger Pro", page_icon="🤖", layout="wide")

# Custom CSS for better layout
st.markdown("""
    <style>
        .stMarkdown pre {border-radius: 10px; padding: 15px!important; font-size: 14px;}
        .table-container {overflow-x: auto;}
        th, td {text-align: left; padding: 10px; font-size: 14px;}
        .diff-added {background: #e6ffe6;}
        .diff-removed {background: #ffe6e6;}
        .diff-container {padding: 10px; border-radius: 5px;}
    </style>
""", unsafe_allow_html=True)

# Session State Initialization
if 'history' not in st.session_state:
    st.session_state.history = []

# UI Elements
st.title("🤖 AI Code Debugger Pro")
st.write("Advanced code analysis powered by Google Gemini")

col1, col2 = st.columns([3, 1])
with col1:
    uploaded_file = st.file_uploader("📤 Upload code file", type=["py","js","java","cpp","cs","go","rs","ts"])
    code = ""
    if uploaded_file is not None:
        code = uploaded_file.getvalue().decode("utf-8")
    code = st.text_area("📝 Paste code here:", height=300, value=code)

with col2:
    lang = st.selectbox("🌐 Language:", ["Auto-Detect", "Python", "JavaScript", "Java", "C++", "C#", "Go", "Rust", "TypeScript"])
    analysis_type = st.radio("🔍 Analysis Type:", ["Full Audit", "Quick Fix", "Security Review"])
    st.info("💡 Tip: Use 'Full Audit' for complete code review")

# Process Analysis
if st.button("🚀 Analyze Code", use_container_width=True):
    if not code.strip():
        st.error("⚠️ Please input code or upload a file")
    else:
        with st.spinner("🔬 Deep code analysis in progress..."):
            start_time = datetime.now()
            response = correct_code(code, lang.lower() if lang != "Auto-Detect" else "auto-detect")
            process_time = (datetime.now() - start_time).total_seconds()
            
            st.session_state.history.append({'code': code, 'response': response, 'timestamp': start_time})
        
        if response.startswith("**API Error**"):
            st.error(response)
        else:
            sections = parse_response(response)
            st.success(f"✅ Analysis completed in {process_time:.2f}s")
            tab1, tab2, tab3 = st.tabs(["🛠 Corrected Code", "📖 Explanation", "💎 Optimizations"])
            
            with tab1:
                st.subheader("Original vs. Corrected Code")
                st.markdown("""
                <div class='table-container'>
                    <table>
                        <tr>
                            <th style="width: 50%;">🔴 Original Code</th>
                            <th style="width: 50%;">✅ Corrected Code</th>
                        </tr>
                        <tr>
                            <td style="font-size: 14px; overflow-x: auto;">
                                <pre style="white-space: pre-wrap; word-wrap: break-word; max-height: 300px; overflow-y: auto;">{original}</pre>
                            </td>
                            <td style="font-size: 14px; overflow-x: auto;">
                                <pre style="white-space: pre-wrap; word-wrap: break-word; max-height: 300px; overflow-y: auto;">{corrected}</pre>
                            </td>
                        </tr>
                    </table>
                </div>
                """.format(original=code, corrected=sections['code']), unsafe_allow_html=True)
            
            with tab2:
                st.markdown(f"### Error Breakdown\n{sections['explanation']}")
            
            with tab3:
                st.markdown(f"### Optimization Recommendations\n{sections['improvements']}")

# Sidebar History
with st.sidebar:
    st.subheader("📚 Analysis History")
    for idx, entry in enumerate(reversed(st.session_state.history)):
        if st.button(f"Analysis {len(st.session_state.history)-idx} - {entry['timestamp'].strftime('%H:%M:%S')}"):
            st.session_state.code = entry['code']
            st.experimental_rerun()

st.markdown("---")
st.markdown("🔒 **Security Note:** Code is processed securely through Google's API and not stored.")
