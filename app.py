import streamlit as st
from api import generate_image, generate_video, upscale_image
import os
import uuid
import logging
from PIL import Image
from session_manager import SessionManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Set up the Streamlit app
st.title("Source Studio")
st.write("Generate images using different AI models by providing a prompt and selecting a generator.")
logger.info("Source Studio app started.")

# Initialize session state for conversation history
if 'history' not in st.session_state:
    st.session_state.history = []
    logger.info("Initialized conversation history.")

# Initialize session state for the current image being edited
if 'current_edit' not in st.session_state:
    st.session_state.current_edit = None
    logger.info("Initialized current edit session state.")

# Initialize session state for uploaded file
if 'uploaded_file_processed' not in st.session_state:
    st.session_state.uploaded_file_processed = False
    logger.info("Initialized uploaded file processed session state.")

# Initialize session manager
session_manager = SessionManager()

# Initialize session state
if 'session_id' not in st.session_state:
    st.session_state.session_id = uuid.uuid4().hex[:8]
    
# Get session directory
session_dir = session_manager.get_session_dir(st.session_state.session_id)

# Clean up expired sessions on app start
session_manager.cleanup_expired_sessions()

# Input for the prompt
prompt = st.chat_input("Say something")
logger.info(f"Received prompt: {prompt}")

# Dropdown for selecting the generator
generator = st.selectbox(
    "Select a generator",
    ("flux", "stability", "boreal", "phantasma-anime")
)
logger.info(f"Generator selected: {generator}")

# Automatically generate the image when a prompt is entered
if prompt:
    st.write(f"Prompt: {prompt}")
    result = generate_image(prompt, generator, session_dir)
    logger.info(f"Generated image with prompt '{prompt}' using generator '{generator}'")

    if result.startswith("error"):
        st.error(result)
        logger.error(f"Error generating image: {result}")
    else:
        st.session_state.history.append((prompt, result))
        logger.info(f"Image generation successful, added to history.")

# Upload an image
uploaded_file = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg", "webp"])

if uploaded_file is not None and not st.session_state.uploaded_file_processed:
    uploaded_image_name = f"uploaded_image_{uuid.uuid4().hex[:8]}.png"
    uploaded_image_path = os.path.join('static', uploaded_image_name)
    
    with open(uploaded_image_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    logger.info(f"Uploaded image saved at path: {uploaded_image_path}")
    
    st.session_state.history.append(("Uploaded Image", uploaded_image_path))
    st.session_state.uploaded_file_processed = True
    st.success("Image uploaded successfully!")

# Display the conversation history
st.write("### Conversation History")
for i, (past_prompt, image_path) in enumerate(st.session_state.history):
    st.write(f"Prompt {i+1}: {past_prompt}")
    logger.info(f"Displaying history entry {i+1} - Prompt: {past_prompt}")

    try:
        with open(image_path, "rb") as img_file:
            img = Image.open(img_file)
            img.verify()
            st.image(image_path, caption=f"Generated Image {i+1}")
            logger.info(f"Image {i+1} displayed successfully.")
    except (FileNotFoundError, Image.UnidentifiedImageError) as e:
        st.error(f"Error displaying image {i+1}: {e}")
        logger.error(f"Error encountered for image {i+1}: {e}")

    image_name = os.path.basename(image_path)

    if st.button(f"Edit {image_name}", key=f"edit_{i}"):
        st.session_state.current_edit = image_name
        logger.info(f"Set current edit to image: {image_name}")

# Sidebar content
if st.session_state.current_edit:
    st.sidebar.title(f"Edit {st.session_state.current_edit}")

    current_prompt, current_image_path = next(
        ((p, img) for p, img in st.session_state.history if os.path.basename(img) == st.session_state.current_edit), 
        (None, None)
    )
    logger.info(f"Editing image: {current_image_path} with prompt: '{current_prompt}'")

    if st.sidebar.button("Upscale"):
        upscaled_result = upscale_image(current_image_path, session_dir)
        if upscaled_result.startswith("error"):
            st.sidebar.error(upscaled_result)
            logger.error(f"Error upscaling image: {upscaled_result}")
        else:
            st.image(upscaled_result, caption="Upscaled Image")
            if (f"Upscaled {st.session_state.current_edit}", upscaled_result) not in st.session_state.history:
                st.session_state.history.append((f"Upscaled {st.session_state.current_edit}", upscaled_result))
                logger.info(f"Upscaled image added to history: {upscaled_result}")

    if st.sidebar.button("Regenerate"):
        if current_prompt:
            new_image_path = generate_image(current_prompt, generator, session_dir)
            if new_image_path.startswith("error"):
                st.sidebar.error(new_image_path)
                logger.error(f"Error regenerating image: {new_image_path}")
            else:
                st.image(new_image_path, caption="Regenerated Image")
                if (current_prompt, new_image_path) not in st.session_state.history:
                    st.session_state.history.append((current_prompt, new_image_path))
                    logger.info(f"Regenerated image added to history: {new_image_path}")
                st.session_state.current_edit = os.path.basename(new_image_path)

    if st.sidebar.button("Image to Video"):
        video_result = generate_video(current_image_path, session_dir)
        if video_result.startswith("error"):
            st.sidebar.error(video_result)
            logger.error(f"Error generating video: {video_result}")
        else:
            st.video(video_result)
            if (f"Video from {st.session_state.current_edit}", video_result) not in st.session_state.history:
                st.session_state.history.append((f"Video from {st.session_state.current_edit}", video_result))
                logger.info(f"Video added to history: {video_result}")

    if current_image_path:
        with open(current_image_path, "rb") as file:
            st.sidebar.download_button(
                label="Download Image",
                data=file,
                file_name=st.session_state.current_edit,
                mime="image/png"
            )
            logger.info(f"Download button created for image: {current_image_path}")

else:
    st.sidebar.title("Edit Images")
    st.sidebar.write("Press the edit button under the image to open editing and more options.")
    st.sidebar.write("Options include:")
    st.sidebar.write("- Upscaling")
    st.sidebar.write("- Regenerating")
    st.sidebar.write("- Image to video generation")
    st.sidebar.write("- Downloading images/videos")
    logger.info("No image selected for editing.")
