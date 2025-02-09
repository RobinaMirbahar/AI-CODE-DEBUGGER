import google.generativeai as genai
import streamlit as st
import re
from datetime import datetime

# Configure Gemini API
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# Existing functions remain unchanged here...
# [Keep all original functions exactly as provided]

# New Additional Functions
def optimize_code(code_snippet, language):
    """Generate code optimizations and improvements"""
    try:
        prompt = f"""
        Analyze this {language} code for optimizations:
        ```{language}
        {code_snippet}
        ```
        Provide:
        1. Performance improvements with before/after examples
        2. Readability enhancements
        3. Best practices recommendations
        4. Memory usage optimization
        
        Format with clear sections for each category.
        """
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"**Optimization Error**: {str(e)}"

def check_dependencies(code_snippet, language):
    """Identify and manage code dependencies"""
    try:
        prompt = f"""
        Analyze this {language} code and:
        1. List all external dependencies
        2. Detect outdated/vulnerable packages
        3. Generate requirements.txt (Python) or package.json (JS)
        4. Suggest alternative lightweight libraries
        
        Include security recommendations and version constraints.
        """
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"**Dependency Error**: {str(e)}"

def explain_code(code_snippet, language):
    """Generate comprehensive code explanation"""
    try:
        prompt = f"""
        Explain this {language} code in detail:
        ```{language}
        {code_snippet}
        ```
        Cover:
        1. Overall architecture
        2. Key algorithms/methods
        3. Data flow diagram
        4. Potential scaling limitations
        5. Alternative approaches
        
        Use beginner-friendly analogies where possible.
        """
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"**Explanation Error**: {str(e)}"

# Modified UI Section with New Features
st.set_page_config(page_title="AI Code Debugger Pro+", page_icon="🚀", layout="wide")

# Existing UI configuration remains unchanged...
# [Keep all original UI setup code]

# Add New UI Elements
st.markdown("""
    <style>
        .new-feature {border: 1px solid #4CAF50; border-radius: 5px; padding: 10px; margin: 10px 0;}
    </style>
""", unsafe_allow_html=True)

# New Buttons Row
col6, col7, col8 = st.columns(3)
with col6:
    optimize_btn = st.button("⚡ Optimize Code", use_container_width=True)
with col7:
    deps_btn = st.button("📦 Dependency Check", use_container_width=True)
with col8:
    explain_btn = st.button("📖 Explain Code", use_container_width=True)

# Existing button handling remains...
# [Keep all original button handlers]

# New Button Handlers
if optimize_btn:
    if code.strip():
        with st.spinner("⚡ Optimizing code..."):
            optimizations = optimize_code(code, lang)
            with st.expander("**Optimization Report**", expanded=True):
                st.markdown(optimizations)
            st.session_state.history.append({
                'type': 'Optimization',
                'result': optimizations,
                'timestamp': datetime.now()
            })
    else:
        st.error("⚠️ Please input code to optimize")

if deps_btn:
    if code.strip():
        with st.spinner("📦 Analyzing dependencies..."):
            dependencies = check_dependencies(code, lang)
            with st.expander("**Dependency Report**", expanded=True):
                st.code(dependencies)
            st.session_state.history.append({
                'type': 'Dependencies',
                'result': dependencies,
                'timestamp': datetime.now()
            })
    else:
        st.error("⚠️ Please input code to check dependencies")

if explain_btn:
    if code.strip():
        with st.spinner("📖 Generating explanation..."):
            explanation = explain_code(code, lang)
            with st.expander("**Code Explanation**", expanded=True):
                st.markdown(explanation)
            st.session_state.history.append({
                'type': 'Explanation',
                'result': explanation,
                'timestamp': datetime.now()
            })
    else:
        st.error("⚠️ Please input code to explain")

# Enhanced History Section in Sidebar
with st.sidebar:
    st.subheader("📚 Activity History")
    for idx, item in enumerate(st.session_state.history[-5:]):
        with st.expander(f"{item['type']} - {item['timestamp'].strftime('%H:%M')}"):
            if item['type'] in ['Optimization', 'Explanation']:
                st.markdown(item['result'][:300] + "...")
            else:
                st.code(item['result'][:200] + "...")

st.markdown("---")
st.markdown("🔒 *Code processed securely via Google's AI APIs*")
