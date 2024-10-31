import streamlit as st
from api import generate_image, generate_video
import os

# Set up the Streamlit app
st.title("Source Studio")
st.write("Generate images using different AI models by providing a prompt and selecting a generator.")

# Initialize session state for conversation history
if 'history' not in st.session_state:
    st.session_state.history = []

# Initialize session state for the current image being edited
if 'current_edit' not in st.session_state:
    st.session_state.current_edit = None

# Input for the prompt
prompt = st.chat_input("Say something")

# Dropdown for selecting the generator
generator = st.selectbox(
    "Select a generator",
    ("flux", "stability", "boreal", "phantasma-anime")
)

# Automatically generate the image when a prompt is entered
if prompt:
    st.write(f"Prompt: {prompt}")
    result = generate_image(prompt, generator)
    
    if result.startswith("error"):
        st.error(result)
    else:
        # Add the prompt and result to the conversation history
        st.session_state.history.append((prompt, result))

# Display the conversation history
st.write("### Conversation History")
for i, (past_prompt, image_path) in enumerate(st.session_state.history):
    st.write(f"Prompt {i+1}: {past_prompt}")
    st.image(image_path, caption=f"Generated Image {i+1}")

    # Extract the image name from the path
    image_name = image_path.split('/')[-1]
    
    # Add a button for each image to edit
    if st.button(f"Edit {image_name}", key=f"edit_{i}"):
        st.session_state.current_edit = image_name

# Sidebar content
if st.session_state.current_edit:
    # Display editing options for the selected image
    st.sidebar.title(f"Edit {st.session_state.current_edit}")
    
    # Custom CSS for buttons
    st.markdown(
        """
        <style>
        .stButton > button {
            width: 90%;
            margin: 5px auto;
            display: block;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    if st.sidebar.button("Upscale"):
        st.sidebar.write("Upscaling image...")  # Placeholder for upscaling functionality
    if st.sidebar.button("Regenerate"):
        st.sidebar.write("Regenerating image...")  # Placeholder for regenerating functionality
    if st.sidebar.button("Image to Video"):
        video_result = generate_video(st.session_state.current_edit)
        if video_result.startswith("error"):
            st.sidebar.error(video_result)
        else:
            st.video(video_result)
            st.session_state.history.append((f"Video from {st.session_state.current_edit}", video_result))
    if st.sidebar.button("Edit Prompt"):
        st.sidebar.write("Editing prompt...")  # Placeholder for prompt editing functionality
    if st.sidebar.button("Download"):
        st.sidebar.write("Downloading image...")  # Placeholder for downloading functionality
else:
    # Default sidebar content when no image is selected
    st.sidebar.title("Edit Images")
    st.sidebar.write("Press the edit button under the image to open editing and more options.")
    st.sidebar.write("Options include:")
    st.sidebar.write("- Upscaling")
    st.sidebar.write("- Regenerating")
    st.sidebar.write("- Image to video generation")
    st.sidebar.write("- Prompt Editing")
    st.sidebar.write("- Downloading images/videos")