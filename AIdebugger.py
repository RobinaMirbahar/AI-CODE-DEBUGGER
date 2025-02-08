import google.generativeai as genai
import streamlit as st
import re
from datetime import datetime

# Configure Gemini API
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

@st.cache_data(show_spinner=False)
def correct_code(code_snippet, language, analysis_type="Full Audit"):
    """Enhanced code analysis with multiple modes"""
    try:
        lang = language.lower() if language != "Auto-Detect" else "python"
        code_block = f"```{lang}\n{code_snippet}\n```"
        
        base_prompt = f"""
        Analyze this {lang} code and provide:
        
        1. CORRECTED CODE with line numbers and change comments
        2. ERROR EXPLANATION with categorized errors and fixes
        3. {analysis_type.upper()} ANALYSIS with relevant suggestions
        
        Format your response EXACTLY like this:
        
        ### CORRECTED CODE
        ```{lang}
        [Your corrected code here]
        ```
        
        ### ERROR EXPLANATION
        - [Error 1]
        - [Error 2]
        
        ### ANALYSIS FINDINGS
        - [Finding 1]
        - [Finding 2]
        """
        
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(base_prompt)
        return response.text
    except Exception as e:
        return f"**API Error**: {str(e)}"

def parse_response(response_text):
    """Robust response parser with fallbacks"""
    sections = {'code': '', 'explanation': '', 'improvements': ''}
    
    try:
        # Case-insensitive regex patterns with fallback matches
        code_match = re.search(r'### CORRECTED CODE\s*```.*?\n(.*?)```', response_text, re.DOTALL | re.IGNORECASE)
        explanation_match = re.search(r'### ERROR EXPLANATION(.*?)(?:###|\Z)', response_text, re.DOTALL | re.IGNORECASE)
        improvements_match = re.search(r'### ANALYSIS FINDINGS(.*?)(?:###|\Z)', response_text, re.DOTALL | re.IGNORECASE)
        
        sections['code'] = code_match.group(1).strip() if code_match else "No code corrections suggested"
        sections['explanation'] = explanation_match.group(1).strip() if explanation_match else "No errors detected"
        sections['improvements'] = improvements_match.group(1).strip() if improvements_match else "No additional findings"
        
    except Exception as e:
        st.error(f"Parsing error: {str(e)}")
    
    return sections

# [Keep all other functions unchanged - generate_code_from_text, generate_test_cases, 
#  generate_api_documentation, code_chat_assistant]

# Streamlit UI Configuration (unchanged)
st.set_page_config(page_title="AI Code Suite Pro", page_icon="🚀", layout="wide")

# [Keep all UI components and other handlers unchanged]

# Modified Analysis Results Section
if analyze_btn:
    if code.strip():
        with st.spinner("🧠 Analyzing code..."):
            response = correct_code(code, lang, analysis_type)
            sections = parse_response(response)
            
            tab1, tab2, tab3 = st.tabs(["🛠 Corrected Code", "📖 Error Explanation", "🔍 Analysis Findings"])
            
            with tab1:
                st.code(sections['code'], language=lang.lower())
                if st.button("🧪 Generate Tests"):
                    tests = generate_test_cases(code, lang)
                    st.code(tests, language='python')
            
            with tab2:
                st.markdown(f"```\n{sections['explanation']}\n```")
            
            with tab3:
                st.markdown(f"```\n{sections['improvements']}\n```")
            
            st.session_state.history.append({
                'code': code,
                'response': response,
                'timestamp': datetime.now()
            })
    else:
        st.error("⚠️ Please input code to analyze")

# [Keep rest of the code identical]
