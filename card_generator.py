from PIL import Image, ImageDraw, ImageFont

TITLE_FONT = "fonts/DynaPuff-VariableFont_wdth,wght.ttf"
TEXT_FONT = "fonts/Sniglet-Regular.ttf"


class CardGenerator:
    def __init__(
        self,
        full_card_size: tuple[int, int] = (750, 1050),
        bg_color_primary=(255, 255, 255),
        bg_color_secondary=(240, 240, 240),
    ):
        # if color input is a hex string, convert to RGB tuple
        if isinstance(bg_color_primary, str) and bg_color_primary.startswith("#"):
            bg_color_primary = tuple(
                int(bg_color_primary[i : i + 2], 16) for i in (1, 3, 5)
            )
        if isinstance(bg_color_secondary, str) and bg_color_secondary.startswith("#"):
            bg_color_secondary = tuple(
                int(bg_color_secondary[i : i + 2], 16) for i in (1, 3, 5)
            )

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
        """Apply color mapping to grayscale image: white -> secondary, black -> primary"""
        # Ensure we have RGBA mode to work with transparency
        if image.mode != "RGBA":
            image = image.convert("RGBA")

        # Create a background with secondary color
        background = Image.new("RGBA", image.size, (*self.bg_color_secondary, 255))

        # Composite the texture over the background to fill transparent areas
        composite = Image.alpha_composite(background, image)

        # Get pixel data
        pixels = composite.load()
        width, height = composite.size

        # Apply color interpolation
        for x in range(width):
            for y in range(height):
                r, g, b, alpha = pixels[x, y]

                # Convert RGB to grayscale for color mapping
                gray_value = int(0.299 * r + 0.587 * g + 0.114 * b)

                # Normalize gray value to 0-1 range
                t = gray_value / 255.0

                # Interpolate between primary (black=0) and secondary (white=255)
                new_r = int(
                    self.bg_color_primary[0] * (1 - t) + self.bg_color_secondary[0] * t
                )
                new_g = int(
                    self.bg_color_primary[1] * (1 - t) + self.bg_color_secondary[1] * t
                )
                new_b = int(
                    self.bg_color_primary[2] * (1 - t) + self.bg_color_secondary[2] * t
                )

                pixels[x, y] = (new_r, new_g, new_b, alpha)

        return composite

    def _draw_justified_text(self, draw, text, x, y, max_width, font):
        """Draw justified text with word wrapping within max_width."""
        words = text.split()
        lines = []
        current_line = []

        # Build lines that fit within max_width
        for word in words:
            test_line = current_line + [word]
            test_text = " ".join(test_line)
            bbox = draw.textbbox((0, 0), test_text, font=font)
            text_width = bbox[2] - bbox[0]

            if text_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(current_line)
                current_line = [word]

        if current_line:
            lines.append(current_line)

        # Draw each line with justification (except the last line)
        line_height = font.size + 5  # Add some line spacing
        current_y = y

        for i, line_words in enumerate(lines):
            is_last_line = i == len(lines) - 1
            line_text = " ".join(line_words)

            if is_last_line or len(line_words) == 1:
                # Last line or single word: left-aligned
                draw.text((x, current_y), line_text, fill=(0, 0, 0), font=font)
            else:
                # Justify the line by distributing extra space between words
                bbox = draw.textbbox((0, 0), line_text, font=font)
                line_width = bbox[2] - bbox[0]
                extra_space = max_width - line_width
                space_per_gap = (
                    extra_space // (len(line_words) - 1) if len(line_words) > 1 else 0
                )

                current_x = x
                for j, word in enumerate(line_words):
                    draw.text((current_x, current_y), word, fill=(0, 0, 0), font=font)
                    if j < len(line_words) - 1:  # Not the last word
                        word_bbox = draw.textbbox((0, 0), word, font=font)
                        word_width = word_bbox[2] - word_bbox[0]
                        space_bbox = draw.textbbox((0, 0), " ", font=font)
                        space_width = space_bbox[2] - space_bbox[0]
                        current_x += word_width + space_width + space_per_gap

            current_y += line_height

    def create_card(
        self, character_image: str, name: str, description: str
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

        # Add description with justified text and max width
        font_medium = ImageFont.truetype(TEXT_FONT, 30)
        y_pos = 800
        max_width = 650
        text_x = (self.output_size[0] - max_width) // 2  # Center the text block
        self._draw_justified_text(
            draw, description, text_x, y_pos, max_width, font_medium
        )

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
        bg_color_primary="#CA926E",  # Brown for dark areas
        bg_color_secondary="#deb48c",  # Beige for light areas
    )
    description = 'Si cette carte est dans votre main depuis plus d\'un tour, vous pouvez remplacer votre tour par: "force un joueur à échanger une carte avec celle-ci"'
    card = generator.create_card(img_path, "Warren Libre-d'en-bas", description)
    generator.save_card(card, "outputs/output_card.png")
