import streamlit as st
import google.generativeai as genai
import json
import re
import time

# ======================
# Configuration
# ======================
DEBUG_PROMPT = """Analyze and debug this {language} code with:
1. Line-specific error identification
2. Runtime behavior analysis
3. Security vulnerability detection
4. Performance optimization
5. Corrected implementation

Return strict JSON format:
{{
  "metadata": {{
    "analysis_time": float,
    "complexity": string
  }},
  "errors": [
    {{
      "line": int,
      "type": string,
      "description": string,
      "fix": string
    }}
  ],
  "corrected_code": string,
  "warnings": [string]
}}"""

VERIFICATION_PROMPT = """Verify user's debugging request:
User Input: {user_input}
Code Context: {code_context}

Respond with JSON:
{{
  "needs_verification": bool,
  "verification_questions": [string],
  "risk_level": "low/medium/high"
}}"""

# ======================
# Gemini Initialization
# ======================
def initialize_debugger():
    """Configure Gemini debugger engine"""
    try:
        if "GEMINI_API_KEY" not in st.secrets:
            raise ValueError("Missing GEMINI_API_KEY in secrets")
            
        genai.configure(
            api_key=st.secrets["GEMINI_API_KEY"],
            transport='rest',
            client_options={
                'api_endpoint': 'https://generativelanguage.googleapis.com/v1'
            }
        )
        return genai.GenerativeModel('gemini-1.5-pro-latest')
    except Exception as e:
        st.error(f"🔧 Debugger Initialization Failed: {str(e)}")
        st.stop()

model = initialize_debugger()

# ======================
# AI Verification Agent
# ======================
class VerificationAgent:
    def __init__(self):
        self.verification_stage = 0
        self.questions = []
        self.answers = []
        self.code_context = ""

    def verify_request(self, user_input, code_snippet):
        """Verify debugging request with AI agent"""
        self.code_context = code_snippet[:500]  # Keep context short
        
        response = model.generate_content(
            VERIFICATION_PROMPT.format(
                user_input=user_input,
                code_context=self.code_context
            ),
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                max_output_tokens=1000,
                response_mime_type="application/json"
            )
        )
        
        verification_data = json.loads(response.text)
        return verification_data

    def handle_verification(self, verification_data):
        """Manage verification conversation flow"""
        if verification_data["needs_verification"]:
            self.questions = verification_data["verification_questions"]
            return self.questions
        return None

# ======================
# Core Debugging Logic
# ======================
def debug_code(code: str, language: str) -> dict:
    """Execute AI-powered debugging"""
    try:
        response = model.generate_content(
            DEBUG_PROMPT.format(language=language, code=code),
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,
                max_output_tokens=4000,
                response_mime_type="application/json"
            )
        )
        return parse_debug_response(response.text)
    except genai.types.generation_types.StopCandidateException as e:
        return {"error": f"Content safety blocked: {str(e)}"}
    except Exception as e:
        return {"error": f"API Error: {str(e)}"}

def parse_debug_response(response: str) -> dict:
    """Process and validate debug output"""
    try:
        json_str = re.search(r'```json\n(.*?)\n```', response, re.DOTALL)
        if not json_str:
            raise ValueError("No JSON found in response")
            
        debug_data = json.loads(json_str.group(1))
        
        required_keys = {
            "metadata": ["analysis_time", "complexity"],
            "errors": ["line", "type", "description", "fix"],
            "corrected_code": str,
            "warnings": list
        }
        
        for category, keys in required_keys.items():
            if not all(key in debug_data.get(category, {}) for key in keys):
                raise ValueError(f"Missing {category} data")
                
        return debug_data
    except Exception as e:
        return {"error": f"Response parsing failed: {str(e)}"}

# ======================
# Streamlit Interface
# ======================
def main():
    st.set_page_config(page_title="AI Code Debugger", layout="wide")
    st.title("🤖 Secure Code Debugger Pro")
    
    agent = VerificationAgent()
    
    if 'verified' not in st.session_state:
        st.session_state.verified = False
        st.session_state.verification_data = None
    
    code = st.text_area("Input Code:", height=300)
    language = st.selectbox("Language:", ["python", "javascript", "java", "c++"])
    
    if st.button("Debug Code"):
        if not code.strip():
            st.warning("Please enter code to debug")
            return
            
        # Initial verification
        if not st.session_state.verified:
            verification = agent.verify_request("User requested code debugging", code)
            st.session_state.verification_data = verification
            
            if verification["needs_verification"]:
                st.session_state.questions = verification["verification_questions"]
                st.session_state.verification_step = 0
                st.rerun()
        
        # Handle verification questions
        if st.session_state.get("verification_step") is not None:
            current_step = st.session_state.verification_step
            if current_step < len(st.session_state.questions):
                question = st.session_state.questions[current_step]
                answer = st.text_input(f"Verification Question {current_step+1}: {question}")
                
                if answer:
                    agent.answers.append(answer)
                    st.session_state.verification_step += 1
                    st.rerun()
            else:
                st.success("Verification complete! Proceeding with debugging...")
                st.session_state.verified = True
                del st.session_state.verification_step
                st.rerun()
        
        # Main debugging process
        if st.session_state.verified:
            with st.spinner("🔍 Analyzing code..."):
                start = time.time()
                result = debug_code(code, language.lower())
                elapsed = time.time() - start
                
                if "error" in result:
                    st.error(f"🚨 {result['error']}")
                else:
                    display_results(result, elapsed, language.lower())

def display_results(data: dict, time_taken: float, language: str):
    """Visualize debugging results"""
    st.subheader("📊 Debug Report")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Analysis Time", f"{time_taken:.2f}s")
    col2.metric("Code Complexity", data['metadata']['complexity'].upper())
    col3.metric("Issues Found", len(data['errors']))
    
    st.subheader("🚨 Code Issues")
    for error in data['errors']:
        with st.expander(f"Line {error['line']}: {error['type']}", expanded=True):
            st.markdown(f"""
            **Description**: {error['description']}
            ```diff
            - Problem: {error['description'].split('.')[0]} 
            + Fix: {error['fix']}
            """)
    
    st.subheader("✅ Optimized Code")
    st.code(data['corrected_code'], language=language)
    
    if data['warnings']:
        st.subheader("⚠️ Important Notes")
        for warning in data['warnings']:
            st.warning(warning)

if __name__ == "__main__":
    main()
