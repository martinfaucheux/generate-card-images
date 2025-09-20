# To run this code you need to install the following dependencies:
# pip install google-genai

import argparse
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


def load_image(image_path):
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


def find_last_generated_image() -> str:
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


def _generate(prompt, image_path_list: list[str] | None = None, output_path=None):
    image_path_list = image_path_list or []
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    model = "gemini-2.5-flash-image-preview"

    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=prompt),
                *[
                    types.Part.from_bytes(data=img_data, mime_type=img_mime_type)
                    for img_data, img_mime_type in (
                        load_image(img_path) for img_path in image_path_list
                    )
                ],
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        response_modalities=["IMAGE", "TEXT"],
    )

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
            file_name = (
                output_path
                if output_path
                else (
                    dir.lstrip("/")
                    + "/"
                    + generate_image_filename(f"{prompt}_{file_index}")
                )
            )
            file_index += 1
            inline_data = chunk.candidates[0].content.parts[0].inline_data
            data_buffer = inline_data.data
            file_extension = mimetypes.guess_extension(inline_data.mime_type)

            # Ensure outputs directory exists
            os.makedirs(file_name.rsplit("/", 1)[0], exist_ok=True)

            save_binary_file(f"{file_name}{file_extension}", data_buffer)
        else:
            print(chunk.text)


def generate_image_filename(base_filename, max_char=50):
    base_filename = sanitize_filename(base_filename)
    epoch_timestamp = int(datetime.now().timestamp())
    return f"outputs/{epoch_timestamp}_{base_filename}.png"


def sanitize_prompt(prompt):
    prompt = prompt.strip()
    if prompt[-1] != ".":
        prompt += "."
    return prompt


def generate(prompt, output_path=None):
    refined_prompt = f"""{sanitize_prompt(prompt)}

All the characters on the picture should be humanoid cats with cartoonish style, big eyes, and expressive faces, and cartoon proportions (large heads, small bodies). The characters shouldn't have weapons unless specified in the prompt.
Use only the prompt to define the number of characters. Usually it is only 1 unless specified otherwise.
Please use the provided base style image as a reference for the visual style, color palette, and artistic approach. Generate the image with a 1:1 aspect ratio (square format). The image should be perfectly square with equal width and height dimensions, following the style of the reference image."""

    return _generate(refined_prompt, ["inputs/base_style.png"], output_path=output_path)


def modify(prompt, image_path=None):
    """Modify an existing image based on a prompt."""

    # Load the image to modify
    if image_path is None:
        image_path = find_last_generated_image()
        print(f"Using last generated image: {image_path}")

    refined_prompt = f"""Please modify this image: {sanitize_prompt(prompt)}

Keep the same cartoonish style with cats having big eyes, expressive faces, and cartoon proportions (large heads, small bodies).
Maintain the 1:1 aspect ratio (square format) and the overall artistic style of the original image."""

    return _generate(refined_prompt, [image_path])


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
