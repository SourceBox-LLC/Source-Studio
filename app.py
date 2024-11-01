import streamlit as st
from api import generate_image, generate_video, upscale_image
import os
import uuid
from PIL import Image

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

# Upload an image
uploaded_file = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg", "webp"])

if uploaded_file is not None:
    # Save the uploaded file to the static directory
    uploaded_image_name = f"uploaded_image_{uuid.uuid4().hex}.png"
    uploaded_image_path = os.path.join('static', uploaded_image_name)
    
    with open(uploaded_image_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # Add the uploaded image to the conversation history
    st.session_state.history.append(("Uploaded Image", uploaded_image_path))  # Store the full path
    st.success("Image uploaded successfully!")

# Display the conversation history
st.write("### Conversation History")
for i, (past_prompt, image_path) in enumerate(st.session_state.history):
    st.write(f"Prompt {i+1}: {past_prompt}")
    
    # Check if the image file exists and is valid
    try:
        with open(image_path, "rb") as img_file:
            img = Image.open(img_file)
            img.verify()  # Verify that it is, indeed, an image
            st.image(image_path, caption=f"Generated Image {i+1}")
    except (FileNotFoundError, Image.UnidentifiedImageError) as e:
        st.error(f"Error displaying image {i+1}: {e}")

    # Extract the image name from the path
    image_name = os.path.basename(image_path)
    
    # Add a button for each image to edit
    if st.button(f"Edit {image_name}", key=f"edit_{i}"):
        st.session_state.current_edit = image_name

# Sidebar content
if st.session_state.current_edit:
    # Display editing options for the selected image
    st.sidebar.title(f"Edit {st.session_state.current_edit}")
    
    # Extract the prompt associated with the current edit
    current_prompt, current_image_path = next(
        ((p, img) for p, img in st.session_state.history if os.path.basename(img) == st.session_state.current_edit), 
        (None, None)
    )

    # Custom CSS for buttons
    st.markdown(
        """
        <style>
        .stButton > button, .stDownloadButton > button {
            width: 90%;
            margin: 5px auto;
            display: block;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    if st.sidebar.button("Upscale"):
        upscaled_result = upscale_image(current_image_path)
        if upscaled_result.startswith("error"):
            st.sidebar.error(upscaled_result)
        else:
            st.image(upscaled_result, caption="Upscaled Image")
            st.session_state.history.append((f"Upscaled {st.session_state.current_edit}", upscaled_result))

    if st.sidebar.button("Regenerate"):
        if current_prompt:
            new_image_path = generate_image(current_prompt, generator)  # Use the existing generator
            if new_image_path.startswith("error"):
                st.sidebar.error(new_image_path)
            else:
                st.image(new_image_path, caption="Regenerated Image")
                # Update history with the regenerated image
                st.session_state.history.append((current_prompt, new_image_path))
                # Update current edit with new image path
                st.session_state.current_edit = os.path.basename(new_image_path)

    if st.sidebar.button("Image to Video"):
        video_result = generate_video(current_image_path)
        if video_result.startswith("error"):
            st.sidebar.error(video_result)
        else:
            st.video(video_result)
            st.session_state.history.append((f"Video from {st.session_state.current_edit}", video_result))

    # Download button functionality
    if current_image_path:
        with open(current_image_path, "rb") as file:
            st.sidebar.download_button(
                label="Download Image",
                data=file,
                file_name=st.session_state.current_edit,
                mime="image/png"
            )

else:
    # Default sidebar content when no image is selected
    st.sidebar.title("Edit Images")
    st.sidebar.write("Press the edit button under the image to open editing and more options.")
    st.sidebar.write("Options include:")
    st.sidebar.write("- Upscaling")
    st.sidebar.write("- Regenerating")
    st.sidebar.write("- Image to video generation")
    st.sidebar.write("- Downloading images/videos")
