# In the File Upload Handling section:
elif input_method == "📁 Upload File":
    code_file = st.file_uploader(
        "Upload Code File",
        type=ALLOWED_CODE_EXTENSIONS,
        help=f"Supported formats: {', '.join(ALLOWED_CODE_EXTENSIONS)}"
    )
    
    if code_file:
        current_file_id = f"file_{code_file.file_id}"
        
        if st.session_state.processed_file_id != current_file_id:
            with st.spinner("Validating file..."):
                is_valid, content, ext = validate_code_file(code_file)
                
            if not is_valid:
                error_message = f"❌ Invalid file: {content}"
                st.session_state.processed_file_id = None
                st.session_state.file_extension = None
            else:
                code_text = content
                language = {
                    "py": "python", "java": "java", 
                    "js": "javascript", "cpp": "cpp",
                    "html": "html", "css": "css", "php": "php"
                }.get(ext, "text")
                st.session_state.processed_file_id = current_file_id
                st.session_state.current_code = code_text
                st.session_state.file_extension = ext  # Store extension in session state
            
            st.experimental_rerun()
        
        if st.session_state.processed_file_id == current_file_id:
            # Get extension from session state
            ext = st.session_state.file_extension or "file"
            st.success(f"✅ Valid {ext.upper()} file uploaded!")
            st.code(st.session_state.current_code, language=language)
        
        if error_message:
            st.error(error_message)
