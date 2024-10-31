import streamlit as st
from api import generate_image

# Set up the Streamlit app
st.title("Source Studio")
st.write("Generate images using different AI models by providing a prompt and selecting a generator.")

# Initialize session state for conversation history
if 'history' not in st.session_state:
    st.session_state.history = []

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