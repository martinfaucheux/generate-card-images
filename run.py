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


def find_last_generated_image():
    """Find the most recently generated image in the outputs directory."""
    outputs_dir = "outputs"

    if not os.path.exists(outputs_dir):
        raise FileNotFoundError("No outputs directory found")

    # Get all image files in the outputs directory
    image_extensions = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp")
    image_files = []

    for filename in os.listdir(outputs_dir):
        if filename.lower().endswith(image_extensions):
            filepath = os.path.join(outputs_dir, filename)
            # Get the modification time
            mtime = os.path.getmtime(filepath)
            image_files.append((filepath, mtime))

    if not image_files:
        raise FileNotFoundError("No generated images found in outputs directory")

    # Sort by modification time (most recent first)
    image_files.sort(key=lambda x: x[1], reverse=True)

    return image_files[0][0]  # Return the path of the most recent image


def load_image_for_modification(image_path):
    """Load an image file for modification."""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found at {image_path}")

    with open(image_path, "rb") as f:
        image_data = f.read()

    # Get the MIME type
    mime_type, _ = mimetypes.guess_type(image_path)
    if mime_type is None:
        # Try to guess from common extensions
        ext = os.path.splitext(image_path)[1].lower()
        mime_type_map = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".bmp": "image/bmp",
            ".webp": "image/webp",
        }
        mime_type = mime_type_map.get(ext, "image/png")

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


def modify(prompt, image_path=None):
    """Modify an existing image based on a prompt."""
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    model = "gemini-2.5-flash-image-preview"

    # Load the image to modify
    if image_path is None:
        image_path = find_last_generated_image()
        print(f"Using last generated image: {image_path}")

    image_data, image_mime_type = load_image_for_modification(image_path)

    prompt = prompt.strip()
    if prompt[-1] != ".":
        prompt += "."

    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(
                    text=f"""Please modify this image: {prompt}

Keep the same cartoonish style with cats having big eyes, expressive faces, and cartoon proportions (large heads, small bodies).
Maintain the 1:1 aspect ratio (square format) and the overall artistic style of the original image."""
                ),
                types.Part.from_bytes(data=image_data, mime_type=image_mime_type),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        response_modalities=[
            "IMAGE",
            "TEXT",
        ],
    )

    # Create base filename from prompt and original filename
    original_name = os.path.splitext(os.path.basename(image_path))[0]
    modification_desc = sanitize_filename(prompt)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = f"{original_name}_modified_{modification_desc}"

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

    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Create parser for the 'new' command
    new_parser = subparsers.add_parser("new", help="Generate a new image")
    new_parser.add_argument("prompt", help="The prompt for image generation")

    # Create parser for the 'modify' command
    modify_parser = subparsers.add_parser("modify", help="Modify an existing image")
    modify_parser.add_argument("prompt", help="The modification prompt")
    modify_parser.add_argument(
        "-p",
        "--path",
        help="Path to the image to modify (if not provided, uses the last generated image)",
    )

    args = parser.parse_args()

    # Check if API key is set
    if not os.environ.get("GEMINI_API_KEY"):
        print("Error: GEMINI_API_KEY environment variable is not set")
        print("Please set it with: export GEMINI_API_KEY=your_api_key")
        return 1

    # Handle different commands
    if args.command == "new":
        print(f"Generating new image for prompt: '{args.prompt}'")
        generate(args.prompt)
    elif args.command == "modify":
        try:
            if args.path:
                print(f"Modifying image at '{args.path}' with prompt: '{args.prompt}'")
                modify(args.prompt, args.path)
            else:
                print(f"Modifying last generated image with prompt: '{args.prompt}'")
                modify(args.prompt)
        except FileNotFoundError as e:
            print(f"Error: {e}")
            return 1
    else:
        parser.print_help()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
