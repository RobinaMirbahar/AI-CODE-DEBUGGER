# Add these new functions
def generate_code_from_text(prompt_text, language, template=None, refinement=None):
    """Advanced code generation with templates and refinements"""
    try:
        template_prompt = ""
        if template and template != "Custom":
            template_prompt = f" using the {template} template structure"
        
        refinement_prompt = ""
        if refinement:
            refinement_prompt = f"\nPrevious code feedback: {refinement}"

        prompt = f"""
        You are an expert AI developer. Generate {language} code{template_prompt} that:
        {prompt_text}
        
        Requirements:
        1. Production-quality code
        2. Follow {language} best practices
        3. Include error handling
        4. Add relevant comments
        5. Support easy extension
        
        {refinement_prompt}
        
        Format response with:
        - Markdown code block with syntax highlighting
        - Brief overview in bullet points
        - Key features list
        - Potential extension ideas
        """
        
        model = genai.GenerativeModel('gemini-2.0-pro-exp')
        response = model.generate_content(prompt)
        return response.text
    
    except Exception as e:
        return f"**Generation Error**: {str(e)}"

def parse_generated_response(response):
    """Parse generated code and documentation"""
    components = {
        'code': '',
        'overview': '',
        'features': '',
        'extensions': ''
    }
    
    # Extract code block
    code_match = re.search(r'```[\w+]*\n(.*?)```', response, re.DOTALL)
    if code_match:
        components['code'] = code_match.group(1)
    
    # Extract documentation sections
    components['overview'] = '\n'.join(re.findall(r'- (Overview: .+)', response))
    components['features'] = '\n'.join(re.findall(r'- (Feature: .+)', response))
    components['extensions'] = '\n'.join(re.findall(r'- (Extension: .+)', response))
    
    return components

# Add to UI components
with st.expander("🚀 AI Code Generator Pro", expanded=True):
    gen_col1, gen_col2 = st.columns([3, 1])
    
    with gen_col1:
        prompt_text = st.text_area("💡 Describe your desired functionality:", 
                                 height=150,
                                 placeholder="e.g., 'Python REST API for user management with JWT auth'")
        
        refinement = st.text_input("🔧 Refine generated code:", 
                                 placeholder="e.g., 'Add rate limiting and database connection pooling'")
    
    with gen_col2:
        template = st.selectbox("📁 Template:", 
                              ["Custom", "Web API", "CLI Tool", "Data Pipeline", 
                               "ML Model", "GUI Application", "Microservice"])
        
        gen_lang = st.selectbox("⌨️ Language:", 
                              ["Python", "JavaScript", "Java", "Go", "C#", "TypeScript"])

    if st.button("✨ Generate Code", key="gen_button"):
        if not prompt_text.strip():
            st.error("⚠️ Please describe the functionality you want")
        else:
            with st.spinner("🚀 Crafting production-ready code..."):
                response = generate_code_from_text(prompt_text, gen_lang, template, refinement)
                
                if not response.startswith("**"):
                    components = parse_generated_response(response)
                    st.session_state.generated_components = components
                    
                    # Display results in tabs
                    gen_tab1, gen_tab2, gen_tab3, gen_tab4 = st.tabs(["🧑💻 Code", "📄 Overview", "⭐ Features", "🔮 Extensions"])
                    
                    with gen_tab1:
                        st.code(components['code'], language=gen_lang.lower())
                        st.download_button("📥 Download Code", components['code'], 
                                         file_name=f"generated_{gen_lang.lower()}.{get_extension(gen_lang)}")
                        
                        if st.button("🧩 Insert into Editor"):
                            st.session_state.code = components['code']
                            st.rerun()
                    
                    with gen_tab2:
                        st.markdown(f"### System Overview\n{components['overview']}")
                    
                    with gen_tab3:
                        st.markdown(f"### Key Features\n{components['features']}")
                    
                    with gen_tab4:
                        st.markdown(f"### Future Extensions\n{components['extensions']}")
                else:
                    st.error(response)

# Add helper function for file extensions
def get_extension(language):
    extensions = {
        "Python": "py",
        "JavaScript": "js",
        "Java": "java",
        "Go": "go",
        "C#": "cs",
        "TypeScript": "ts"
    }
    return extensions.get(language, "txt")
