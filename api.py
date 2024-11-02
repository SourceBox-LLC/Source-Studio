import logging
import requests
from dotenv import load_dotenv
import os, io
import random
import string
import uuid
from PIL import Image
import time
import replicate


load_dotenv()


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

api_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")

# URLs for various Hugging Face models (Stability AI, Boreal, Flux, and Phantasma Anime)
stability_api_url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
boreal_api_url = "https://api-inference.huggingface.co/models/kudzueye/Boreal"
flux_api_url = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-dev"
phantasma_anime_api_url = "https://api-inference.huggingface.co/models/alvdansen/phantasma-anime"

# Prepare headers for API requests to Hugging Face, including the authorization token
hf_headers = {"Authorization": f"Bearer {api_token}"}

#uniqe image identifier
def random_sig():
    """Generates a 3-character random signature, which can be a combination of letters or digits."""
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(3))



def query_image(prompt, api_url, retries=3, delay=5):
    """
    Generic function to query a Hugging Face API for generating images based on a prompt.
    The function sends a POST request to the specified API URL with the prompt data.
    Returns the binary content of the generated image or None if an error occurred.
    """
    for attempt in range(retries):
        try:
            logging.info(f"Querying {api_url} with prompt: {prompt}")
            response = requests.post(api_url, headers=hf_headers, json={"inputs": prompt})
            response.raise_for_status()  # Raise an error for bad responses (4xx, 5xx)
            logging.info(f"Received response with status code {response.status_code}")
            return response.content  # Return the image content as bytes
        except requests.exceptions.RequestException as e:
            logging.info(f"Error querying {api_url}: {e}")
            if attempt < retries - 1:
                logging.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                logging.error("Max retries reached. Failed to generate image.")
                return None


def query_flux_image(prompt):
    return query_image(prompt, flux_api_url)

def query_boreal_image(prompt):
    return query_image(prompt, boreal_api_url)

def query_stability_image(prompt):
    return query_image(prompt, stability_api_url)

def query_phantasma_anime_image(prompt):
    return query_image(prompt, phantasma_anime_api_url)



def generate_image(prompt, generator, session_dir):
    try:
        logging.info("Received request to generate image")
        logging.info(f"Prompt: {prompt}, Generator: {generator}")

        if not prompt or not generator:
            logging.error("Prompt and generator type are required.")
            return "Prompt and generator type are required."

        unique_prompt = f"{prompt} - {random_sig()}"
        logging.debug(f"Unique prompt: {unique_prompt}")

        image_bytes = None
        
        if generator == "flux":
            image_bytes = query_flux_image(unique_prompt)
        elif generator == "stability":
            image_bytes = query_stability_image(unique_prompt)
        elif generator == "boreal":
            image_bytes = query_boreal_image(unique_prompt)
        elif generator == "phantasma-anime":
            image_bytes = query_phantasma_anime_image(unique_prompt)
        else:
            logging.error("Invalid generator selected")
            return "error: Invalid generator selected"

        if not image_bytes:
            logging.error("Failed to generate image from the selected API.")
            return "error: Failed to generate image from the selected API."

        image_name = f"{generator}_{uuid.uuid4().hex[:8]}.png"
        image_path = os.path.join(session_dir, image_name)
        logging.debug(f"Saving image to: {image_path}")

        try:
            image = Image.open(io.BytesIO(image_bytes))
            image.save(image_path)
            logging.info(f"Image saved successfully: {image_name}")
            return image_path  # Return the path of the saved image
        except Exception as e:
            logging.error(f"Error saving image: {e}")
            return "error: Error saving image"

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return str(e)



def generate_video(image_path, session_dir):
    try:
        logging.info("Starting video generation process")

        api_token = os.getenv("REPLICATE_API_TOKEN")
        if not api_token:
            logging.error("API Token not found. Please check your .env file.")
            return "error: API Token not found"

        # Get the model and version
        logging.debug("Fetching model and version")
        try:
            model = replicate.models.get("sunfjun/stable-video-diffusion")
            version = model.versions.get("d68b6e09eedbac7a49e3d8644999d93579c386a083768235cabca88796d70d82")
        except Exception as e:
            logging.error(f"Error fetching model or version: {e}")
            return "error: Error fetching model or version"

        if not image_path:
            logging.error("No image path provided")
            return "error: Image path is required"

        # Construct the full path to the image
        full_image_path = image_path
        logging.debug(f"Full image path: {full_image_path}")

        # Open the image file
        with open(full_image_path, 'rb') as image_file:
            logging.info(f"Creating prediction for image file: {full_image_path}")
            try:
                # Create a prediction
                prediction = replicate.predictions.create(
                    version=version,
                    input={
                        "input_image": image_file,
                        "cond_aug": 0.05,
                        "decoding_t": 14,
                        "video_length": "14_frames_with_svd",
                        "sizing_strategy": "maintain_aspect_ratio",
                        "motion_bucket_id": 127,
                        "frames_per_second": 6
                    }
                )
            except Exception as e:
                logging.error(f"Error creating prediction: {e}")
                return "error: Error creating prediction"

            # Wait for the prediction to complete
            logging.info("Waiting for prediction to complete")
            prediction.wait()

            # Check the status and get the output
            if prediction.status == 'succeeded':
                output_url = prediction.output
                logging.info(f"Prediction succeeded, video URL: {output_url}")

                # Download the video
                video_response = requests.get(output_url)
                video_response.raise_for_status()

                # Save the video to the static directory
                video_name = f"video_{uuid.uuid4().hex[:8]}.mp4"
                video_path = os.path.join(session_dir, video_name)
                with open(video_path, 'wb') as video_file:
                    video_file.write(video_response.content)

                logging.info(f"Video saved successfully at {video_path}")

                return video_path  # Return the path of the saved video
            else:
                logging.error(f"Prediction failed with status: {prediction.status}, detail: {prediction.error}")
                return f"error: Prediction failed with status: {prediction.status}"

    except replicate.exceptions.ReplicateError as e:
        logging.error(f"Replicate API error during video generation: {e}")
        return "error: An error occurred with the Replicate API"

    except Exception as e:
        logging.error(f"Unexpected error during video generation: {e}")
        return f"error: An unexpected error occurred: {e}"




def upscale_image(image_path, session_dir):
    logging.debug("Received request to upscale image")

    if not image_path:
        logging.error("Image path not provided in the request")
        return "error: Image path is required"

    try:
        # Use the full path directly from the input
        full_image_path = image_path
        logging.debug(f"Full image path: {full_image_path}")

        # Open the image file
        with open(full_image_path, 'rb') as image_file:
            logging.info("Creating prediction for image upscaling")
            # Correctly use the replicate API
            prediction = replicate.run(
                "batouresearch/magic-image-refiner:507ddf6f977a7e30e46c0daefd30de7d563c72322f9e4cf7cbac52ef0f667b13",
                input={
                    "hdr": 0,
                    "image": image_file,
                    "steps": 20,
                    "prompt": "UHD 4k",
                    "scheduler": "DDIM",
                    "creativity": 0.25,
                    "guess_mode": False,
                    "resolution": "original",
                    "resemblance": 0.75,
                    "guidance_scale": 7,
                    "negative_prompt": "teeth, tooth, open mouth, longbody, lowres, bad anatomy, bad hands, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, mutant"
                }
            )

            # Check if the prediction is successful
            if isinstance(prediction, list) and len(prediction) > 0:
                output_url = prediction[0]
                logging.info(f"Prediction succeeded, output URL: {output_url}")

                # Download the upscaled image
                upscaled_image_response = requests.get(output_url)
                upscaled_image_response.raise_for_status()

                # Save the upscaled image to the static directory
                upscaled_image_name = f"upscaled_{uuid.uuid4().hex[:8]}.png"
                upscaled_image_path = os.path.join(session_dir, upscaled_image_name)
                with open(upscaled_image_path, 'wb') as upscaled_image_file:
                    upscaled_image_file.write(upscaled_image_response.content)

                logging.info(f"Upscaled image saved successfully at {upscaled_image_path}")

                # Return the path of the saved upscaled image
                return upscaled_image_path
            else:
                logging.error("Prediction failed or returned no output")
                return "error: Prediction failed or returned no output"

    except FileNotFoundError:
        logging.error(f"Image file not found at path: {full_image_path}")
        return "error: Image file not found"

    except replicate.exceptions.ReplicateError as e:
        logging.error(f"Replicate API error during prediction: {e}")
        return "error: An error occurred with the Replicate API"

    except requests.exceptions.RequestException as e:
        logging.error(f"HTTP request error: {e}")
        return "error: An error occurred while making an HTTP request"

    except Exception as e:
        logging.error(f"Unexpected error during prediction: {e}")
        return f"error: An unexpected error occurred: {e}"



if __name__ == "__main__":
    generate_image("a cat on the moon with a banana", "flux", "session_dir")