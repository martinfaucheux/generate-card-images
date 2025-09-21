from PIL import Image, ImageDraw, ImageFont

TITLE_FONT = "fonts/DynaPuff-VariableFont_wdth,wght.ttf"


class CardGenerator:
    def __init__(
        self,
        full_card_size: tuple = (750, 1050),
        bg_color_primary=(255, 255, 255),
        bg_color_secondary=(240, 240, 240),
    ):
        self.output_size = full_card_size
        self.bg_color_primary = bg_color_primary
        self.bg_color_secondary = bg_color_secondary

    def create_rounded_card_base(self, corner_radius: int = 30) -> Image.Image:
        """Generate a white card base with rounded corners."""
        width, height = self.output_size

        # Create a transparent image
        card = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(card)

        # Draw rounded rectangle
        draw.rounded_rectangle(
            [(0, 0), (width - 1, height - 1)],
            radius=corner_radius,
            fill=(255, 255, 255, 255),
            outline=(200, 200, 200, 255),
            width=2,
        )

        return card

    def create_rounded_mask(self, size: tuple, corner_radius: int = 30) -> Image.Image:
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

    def apply_color_mapping(self, image: Image.Image) -> Image.Image:
        """Apply color mapping to texture: transparent -> secondary, opaque -> based on grayscale"""
        # Ensure we have RGBA mode to work with transparency
        if image.mode != "RGBA":
            image = image.convert("RGBA")

        # Get pixel data
        pixels = image.load()
        width, height = image.size

        # Apply color interpolation
        for x in range(width):
            for y in range(height):
                r, g, b, alpha = pixels[x, y]

                if alpha == 0:
                    # Transparent areas = "white" -> use secondary color
                    new_r, new_g, new_b = self.bg_color_secondary
                    new_alpha = 255  # Make it opaque
                else:
                    # Convert RGB to grayscale for color mapping
                    gray_value = int(0.299 * r + 0.587 * g + 0.114 * b)

                    # Normalize gray value to 0-1 range
                    t = gray_value / 255.0

                    # Interpolate between primary (black=0) and secondary (white=255)
                    new_r = int(
                        self.bg_color_primary[0] * (1 - t)
                        + self.bg_color_secondary[0] * t
                    )
                    new_g = int(
                        self.bg_color_primary[1] * (1 - t)
                        + self.bg_color_secondary[1] * t
                    )
                    new_b = int(
                        self.bg_color_primary[2] * (1 - t)
                        + self.bg_color_secondary[2] * t
                    )
                    new_alpha = 255  # Make it opaque

                pixels[x, y] = (new_r, new_g, new_b, new_alpha)

        return image

    def create_card(
        self, character_image: str, name: str, stats: dict, description: str
    ) -> Image.Image:
        # Create base card with rounded corners
        card = self.create_rounded_card_base()

        # bottom texture
        bottom_texture = Image.open("inputs/paw_texture.png")
        texture_width = self.output_size[0]
        texture_height = int(
            bottom_texture.height * (texture_width / bottom_texture.width)
        )
        bottom_texture = bottom_texture.resize((texture_width, texture_height))

        # Apply color mapping: white -> secondary, black -> primary
        bottom_texture = self.apply_color_mapping(bottom_texture)

        texture_x = 0
        texture_y = self.output_size[1] - texture_height
        card.paste(bottom_texture, (texture_x, texture_y), bottom_texture)

        # Add character image
        char_img = Image.open(character_image)
        img_size = 750
        char_img = char_img.resize((img_size, img_size))

        img_start_x = (self.output_size[0] - char_img.width) // 2
        img_start_y = 0
        card.paste(char_img, (img_start_x, img_start_y))  # Add text elements
        draw = ImageDraw.Draw(card)

        # Add scroll image under the name
        scroll_img = Image.open("inputs/flat_scroll.png")
        scroll_width = 1000  # Slightly narrower than card width (750)
        scroll_height = int(scroll_img.height * (scroll_width / scroll_img.width) * 0.8)
        scroll_img = scroll_img.resize((scroll_width, scroll_height))

        # Position scroll under the name
        scroll_x = (self.output_size[0] - scroll_width) // 2 - 90
        scroll_y = 0  # Position under the name text
        card.paste(scroll_img, (scroll_x, scroll_y), scroll_img)

        # Add name
        font_large = ImageFont.truetype(TITLE_FONT, 45)
        # Get text bounding box to calculate width for centering
        bbox = draw.textbbox((0, 0), name, font=font_large)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_x = (self.output_size[0] - text_width) // 2
        # Center the text vertically in the scroll
        text_y = scroll_y + (scroll_height - text_height) // 2 - 10
        draw.text(
            (text_x, text_y),
            name,
            fill=(0, 0, 0),
            font=font_large,
        )

        # Add stats
        font_medium = ImageFont.truetype("Arial.ttf", 24)
        y_pos = 900
        for stat, value in stats.items():
            draw.text((50, y_pos), f"{stat}: {value}", fill=(0, 0, 0), font=font_medium)
            y_pos += 40

        # Apply rounded corner mask to the entire final card
        final_mask = self.create_rounded_mask(self.output_size, corner_radius=30)
        card.putalpha(final_mask)

        return card

    def save_card(self, card: Image.Image, output_path: str):
        card.save(output_path, "PNG")


if __name__ == "__main__":
    img_path = "outputs/yogi.png"
    # Test with more distinct colors to see the texture effect
    generator = CardGenerator(
        bg_color_primary=(100, 50, 20),  # Brown for dark areas
        bg_color_secondary=(220, 180, 140),  # Beige for light areas
    )
    stats = {"Strength": 10, "Agility": 8, "Intelligence": 7}
    card = generator.create_card(
        img_path, "Warren Libre-d'en-bas", stats, "A brave warrior."
    )
    generator.save_card(card, "outputs/output_card.png")
