import streamlit as st

# This MUST be the first Streamlit command
st.set_page_config(
    page_title="AI Code Debugger Pro", 
    page_icon="🤖", 
    layout="wide"
)

# THEN configure API keys and other components
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
        st.error("🔑 Gemini API Key required in .streamlit/secrets.toml or environment")
        st.stop()

# Rest of your code follows...
