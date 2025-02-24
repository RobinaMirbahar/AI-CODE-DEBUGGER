def extract_code_from_image(image) -> Tuple[bool, str]:
    """OCR processing with strict timeout handling"""
    try:
        from concurrent.futures import TimeoutError
        
        client = vision.ImageAnnotatorClient(
            credentials=credentials,
            client_options={
                "api_endpoint": "eu-vision.googleapis.com",
                "timeout": 15.0  # Total client timeout
            }
        )
        
        content = image.read()
        
        # Set up timeout wrapper
        try:
            response = client.text_detection(
                image=vision.Image(content=content),
                timeout=15,  # Per-request timeout
                retry=vision.types.Retry(deadline=15)  # Total deadline
            )
        except TimeoutError:
            return False, "OCR processing timed out after 15 seconds"

        if response.error.message:
            return False, f"API Error: {response.error.message}"
            
        if not response.text_annotations:
            return False, "No text detected in image"
            
        raw_text = response.text_annotations[0].description
        cleaned = re.sub(r'\n{3,}', '\n\n', raw_text).strip()
        return True, cleaned
        
    except (GoogleAPICallError, RetryError) as e:
        return False, f"API Error: {str(e)}"
    except Exception as e:
        return False, f"Processing Error: {str(e)}"

# In the image upload section:
if input_method == "📷 Upload Image":
    img_file = st.file_uploader("Upload Code Screenshot", type=ALLOWED_IMAGE_TYPES)
    
    if img_file:
        current_file_id = f"image_{img_file.file_id}"
        
        if st.session_state.processed_file_id != current_file_id:
            processing_container = st.empty()
            with processing_container:
                with st.spinner("Extracting code (15s max)..."):
                    is_valid, validation_msg = validate_image(img_file)
                    
                    if not is_valid:
                        error_message = f"❌ Invalid image: {validation_msg}"
                        st.session_state.processed_file_id = None
                    else:
                        success, result = extract_code_from_image(img_file)
                        
                        if success:
                            code_text = result
                            st.session_state.processed_file_id = current_file_id
                            st.session_state.current_code = code_text
                        else:
                            error_message = f"❌ Extraction failed: {result}"
                            st.session_state.processed_file_id = None
            
            # Clear spinner container regardless of outcome
            processing_container.empty()
            st.experimental_rerun()
