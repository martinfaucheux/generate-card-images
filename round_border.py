#!/usr/bin/env python3
"""
Script to apply rounded corners to the cover_square_border.png image.
Takes inspiration from the CardGenerator class in card_generator.py.
"""

import argparse
import os

from PIL import Image, ImageDraw


def create_rounded_mask(size: tuple[int, int], corner_radius: int = 30) -> Image.Image:
    """Create a mask with rounded corners for clipping images."""
    width, height = size

    # Create a black image (0 = transparent in mask)
    mask = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(mask)

    # Draw white rounded rectangle (255 = opaque in mask)
    draw.rounded_rectangle(
        [(0, 0), (width - 1, height - 1)], radius=corner_radius, fill=255
    )

    return mask


def apply_rounded_corners(
    image_path: str, output_path: str, corner_radius: int = 30
) -> None:
    """
    Load an image and apply rounded corners to it.

    Args:
        image_path: Path to the input image
        output_path: Path where the rounded image will be saved
        corner_radius: Radius of the rounded corners in pixels
    """
    # Load the image
    image = Image.open(image_path)

    # Convert to RGBA if not already (needed for transparency)
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    # Get image dimensions
    width, height = image.size

    # Create rounded mask
    mask = create_rounded_mask((width, height), corner_radius)

    # Apply the mask to create rounded corners
    image.putalpha(mask)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Save the result
    image.save(output_path, "PNG")
    print(f"Rounded image saved to: {output_path}")


def main():
    """Main function to process images with rounded corners."""
    parser = argparse.ArgumentParser(description="Apply rounded corners to an image")
    parser.add_argument(
        "-i",
        "--input",
        default="inputs/cover_square_border.png",
        help="Input image path (default: inputs/cover_square_border.png)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="outputs/cover_square_border_rounded.png",
        help="Output image path (default: outputs/cover_square_border_rounded.png)",
    )
    parser.add_argument(
        "-r",
        "--radius",
        type=int,
        default=30,
        help="Corner radius in pixels (default: 30)",
    )

    args = parser.parse_args()

    # Check if input file exists
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' not found!")
        return

    # Apply rounded corners
    apply_rounded_corners(args.input, args.output, corner_radius=args.radius)

    print("Processing complete!")


if __name__ == "__main__":
    main()
