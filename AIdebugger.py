import google.generativeai as genai
import streamlit as st
import re

# Configure Gemini API
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# Function to correct and analyze code
@st.cache_data(show_spinner=False)
def correct_code(code_snippet, language, analysis_type="Full Audit"):
    """Analyze and correct code using Google Gemini AI"""
    try:
        lang = language.lower() if language != "Auto-Detect" else ""
        code_block = f"```{lang}\n{code_snippet}\n```" if lang else f"```\n{code_snippet}\n```"
        
        base_prompt = f"""
        You are an expert code assistant. Analyze this code:

        {code_block}

        Provide markdown response with these sections:
        ### Corrected Code
        - Line numbers
        - Change comments
        
        ### Error Explanation
        - Categorize errors
        - Bullet-point fixes
        """
        
        if analysis_type == "Security Review":
            base_prompt += """
            ### Security Findings
            - OWASP Top 10 vulnerabilities
            - Severity ratings
            - Remediation steps
            """
        else:
            base_prompt += """
            ### Optimization Suggestions
            - Performance improvements
            - Best practices
            - Security enhancements
            """
        
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(base_prompt)

        if not response or not response.text:
            return "**Error:** No response received from the AI model."
        
        return response.text
    except Exception as e:
        return f"**API Error:** {str(e)}"

# Function to parse response
def parse_response(response_text):
    """Parse AI response into structured sections"""
    sections = {'code': '', 'explanation': '', 'improvements': ''}
    
    code_match = re.search(r'```[\w+]*\n(.*?)```', response_text, re.DOTALL)
    if code_match:
        sections['code'] = code_match.group(1)
    
    explanation_match = re.search(r'### Error Explanation(.*?)###', response_text, re.DOTALL)
    if explanation_match:
        sections['explanation'] = explanation_match.group(1).strip()
    
    improvements_match = re.search(r'### (Optimization Suggestions|Security Findings)(.*?)$', response_text, re.DOTALL)
    if improvements_match:
        sections['improvements'] = improvements_match.group(2).strip()
    
    return sections

# Streamlit UI Configuration
st.set_page_config(page_title="AI Code Analyzer", page_icon="🚀", layout="wide")

# Custom Styling
st.markdown("""
    <style>
        .stMarkdown pre {border-radius: 10px; padding: 15px!important;}
        .stTextArea textarea {font-family: monospace !important;}
        .stButton>button:hover {transform: scale(1.05);}
    </style>
""", unsafe_allow_html=True)

# Session State for History
if 'history' not in st.session_state:
    st.session_state.history = []

# Main Interface
st.title("🚀 AI Code Analyzer")
st.write("Analyze and improve your code with Google Gemini AI.")

col1, col2 = st.columns([3, 1])

with col1:
    code = st.text_area("📝 Paste Your Code Below", height=300, 
                        value=st.session_state.get('code', ''),
                        help="Write or paste your code here")

with col2:
    lang = st.selectbox("🌐 Programming Language", ["Auto-Detect", "Python", "JavaScript", "Java", "C++", "C#", "Go", "Rust"])
    analysis_type = st.radio("🔍 Analysis Mode", ["Full Audit", "Quick Fix", "Security Review"])

# Analyze Button
if st.button("🔍 Analyze Code", use_container_width=True):
    if code.strip():
        with st.spinner("🧠 Analyzing your code..."):
            response = correct_code(code, lang, analysis_type)
            
            # Debugging Output
            st.write("### 📝 Raw API Response")
            st.markdown(f"```\n{response}\n```")  # Display raw response
            
            sections = parse_response(response)
            
            # Show results in tabs
            tab1, tab2, tab3 = st.tabs(["🛠 Corrected Code", "📖 Explanation", "🔍 Findings"])
            with tab1:
                st.code(sections['code'], language=lang.lower())
            with tab2:
                st.markdown(f"```\n{sections['explanation']}\n```")
            with tab3:
                st.markdown(f"```\n{sections['improvements']}\n```")

            # Save to history
            st.session_state.history.append({'code': code, 'analysis': sections})
    else:
        st.error("⚠️ Please enter some code to analyze.")

# Display Analysis History
st.sidebar.subheader("📚 Analysis History")
for idx, item in enumerate(st.session_state.history[-3:]):  # Show last 3 analyses
    with st.sidebar.expander(f"Analysis {idx+1}"):
        st.code(item['code'][:300] + "...")  # Show snippet of code
