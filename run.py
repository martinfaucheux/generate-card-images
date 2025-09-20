# To run this code you need to install the following dependencies:
# pip install google-genai

import argparse
import base64
import mimetypes
import os
import re
from datetime import datetime

from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables from .env file
load_dotenv()


def save_binary_file(file_name, data):
    f = open(file_name, "wb")
    f.write(data)
    f.close()
    print(f"File saved to to: {file_name}")


def sanitize_filename(prompt):
    """Convert prompt to a safe filename."""
    # Take first 50 characters and remove special characters
    clean_name = re.sub(r"[^\w\s-]", "", prompt[:50])
    clean_name = re.sub(r"[-\s]+", "_", clean_name)
    return clean_name.strip("_").lower()


def load_base_style_image():
    """Load and encode the base style image."""
    base_style_path = "inputs/base_style.png"

    if not os.path.exists(base_style_path):
        raise FileNotFoundError(f"Base style image not found at {base_style_path}")

    with open(base_style_path, "rb") as f:
        image_data = f.read()

    # Get the MIME type
    mime_type, _ = mimetypes.guess_type(base_style_path)
    if mime_type is None:
        mime_type = "image/png"  # Default to PNG

    return image_data, mime_type


def generate(prompt):
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    model = "gemini-2.5-flash-image-preview"
    # Load the base style image
    base_image_data, base_image_mime_type = load_base_style_image()

    prompt = prompt.strip()
    if prompt[-1] != ".":
        prompt += "."

    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(
                    text=f"""{prompt}

All the characters on the picture should be cats with cartoonish style, big eyes, and expressive faces, and cartoon proportions (large heads, small bodies).
Please use the provided base style image as a reference for the visual style, color palette, and artistic approach. Generate the image with a 1:1 aspect ratio (square format). The image should be perfectly square with equal width and height dimensions, following the style of the reference image."""
                ),
                types.Part.from_bytes(
                    data=base_image_data, mime_type=base_image_mime_type
                ),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        response_modalities=[
            "IMAGE",
            "TEXT",
        ],
    )

    # Create base filename from prompt
    base_filename = sanitize_filename(prompt)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    file_index = 0
    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        if (
            chunk.candidates is None
            or chunk.candidates[0].content is None
            or chunk.candidates[0].content.parts is None
        ):
            continue
        if (
            chunk.candidates[0].content.parts[0].inline_data
            and chunk.candidates[0].content.parts[0].inline_data.data
        ):
            file_name = f"outputs/{base_filename}_{timestamp}_{file_index}"
            file_index += 1
            inline_data = chunk.candidates[0].content.parts[0].inline_data
            data_buffer = inline_data.data
            file_extension = mimetypes.guess_extension(inline_data.mime_type)

            # Ensure outputs directory exists
            os.makedirs("outputs", exist_ok=True)

            save_binary_file(f"{file_name}{file_extension}", data_buffer)
        else:
            print(chunk.text)


def main():
    parser = argparse.ArgumentParser(
        description="Generate AI images with 1:1 aspect ratio"
    )
    parser.add_argument("prompt", help="The prompt for image generation")

    args = parser.parse_args()

    # Check if API key is set
    if not os.environ.get("GEMINI_API_KEY"):
        print("Error: GEMINI_API_KEY environment variable is not set")
        print("Please set it with: export GEMINI_API_KEY=your_api_key")
        return 1

    print(f"Generating image for prompt: '{args.prompt}'")
    generate(args.prompt)
    return 0


if __name__ == "__main__":
    exit(main())
