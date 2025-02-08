import google.generativeai as genai
import streamlit as st
import difflib
import re
from datetime import datetime

# Function to configure API securely
def configure_api():
    """Safely configures Google Gemini API key from Streamlit secrets."""
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    except KeyError:
        st.error("⚠️ API Key not found! Add it to Streamlit secrets.")
        st.stop()

@st.cache_data(show_spinner=False)
def correct_code(code_snippet, language):
    """Analyze and correct code using Gemini AI with enhanced error handling."""
    configure_api()
    
    lang = language.lower() if language != "Auto-Detect" else ""
    code_block = f"```{lang}\n{code_snippet}\n```" if lang else f"```\n{code_snippet}\n```"

    prompt = f"""
    You are an expert code correction assistant. Analyze, debug, and improve this code:

    {code_block}

    Provide markdown-formatted response with these exact sections:
    ### Corrected Code
    ### Error Explanation
    ### Optimization Suggestions
    """
    
    try:
        model = genai.GenerativeModel('gemini-2.0-pro-exp')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"**API Error**: {str(e)}"

def parse_response(response_text):
    """Parse AI response into structured sections."""
    sections = {'code': '', 'explanation': '', 'improvements': ''}

    patterns = {
        'code': r'```[^\n]*\n(.*?)```',
        'explanation': r'### Error Explanation(.*?)### Optimization Suggestions',
        'improvements': r'### Optimization Suggestions(.*?)$'
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, response_text, re.DOTALL | re.MULTILINE)
        sections[key] = match.group(1).strip() if match else "No details provided."

    return sections

# Streamlit UI Configuration
st.set_page_config(page_title="AI Code Debugger Pro", page_icon="🤖", layout="wide")

# Custom CSS Styling
st.markdown("""
    <style>
        .stMarkdown pre {border-radius: 10px; padding: 15px!important;}
        .diff-container {padding: 10px; border-radius: 5px;}
        .table-container {overflow-x: auto;}
        table {width: 100%; border-collapse: collapse;}
        th, td {border: 1px solid #ddd; padding: 8px; text-align: left;}
        th {background-color: #f2f2f2;}
    </style>
""", unsafe_allow_html=True)

# Session State Initialization
if 'history' not in st.session_state:
    st.session_state.history = []

# Main UI
st.title("🤖 AI Code Debugger Pro")
st.write("Advanced code analysis powered by Google Gemini")

# Input Section
col1, col2 = st.columns([3, 1])
with col1:
    uploaded_file = st.file_uploader("📤 Upload a code file", type=["py", "js", "java", "cpp", "cs", "go", "rs", "ts"])

    if uploaded_file:
        try:
            code = uploaded_file.read().decode("utf-8")
            st.success(f"✅ File '{uploaded_file.name}' uploaded successfully")
        except Exception as e:
            st.error(f"❌ Error reading file: {str(e)}")
            code = ""
    else:
        code = st.text_area("📝 Paste your code:", height=300, value=st.session_state.get('code', ''),
                            help="Supports multiple programming languages")

with col2:
    lang = st.selectbox("🌐 Language:", ["Auto-Detect", "Python", "JavaScript", "Java", "C++", "C#", "Go", "Rust", "TypeScript"])
    analysis_type = st.radio("🔍 Analysis Type:", ["Full Audit", "Quick Fix", "Security Review"])
    st.info("💡 Tip: Use 'Full Audit' for a complete review.")

# Process Analysis
if st.button("🚀 Analyze Code", use_container_width=True):
    if not code.strip():
        st.error("⚠️ Please input code or upload a file")
    else:
        with st.spinner("🔬 Deep code analysis in progress..."):
            start_time = datetime.now()
            response = correct_code(code, lang.lower() if lang != "Auto-Detect" else "auto-detect")
            process_time = (datetime.now() - start_time).total_seconds()
            
            # Save to history
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
                st.subheader("Original vs Corrected Code")
                
                # Creating a side-by-side table for code comparison
                st.markdown("""
                <div class='table-container'>
                    <table>
                        <tr>
                            <th>🔴 Original Code</th>
                            <th>✅ Corrected Code</th>
                        </tr>
                        <tr>
                            <td><pre>{original}</pre></td>
                            <td><pre>{corrected}</pre></td>
                        </tr>
                    </table>
                </div>
                """.format(original=code, corrected=sections['code']), unsafe_allow_html=True)
            
            with tab2:
                st.markdown(f"### Error Breakdown\n{sections['explanation']}")
            
            with tab3:
                st.markdown(f"### Optimization Recommendations\n{sections['improvements']}")

# History Sidebar
with st.sidebar:
    st.subheader("📚 Analysis History")
    for idx, entry in enumerate(reversed(st.session_state.history)):
        if st.button(f"Analysis {len(st.session_state.history)-idx} - {entry['timestamp'].strftime('%H:%M:%S')}",
                     use_container_width=True):
            st.session_state.code = entry['code']
            st.experimental_rerun()

# Footer
st.markdown("---")
st.markdown("🔒 **Security Note:** Code is processed securely through Google's API and not stored.")
