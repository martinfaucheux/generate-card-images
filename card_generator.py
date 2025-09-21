from PIL import Image, ImageDraw, ImageFont


class CardGenerator:
    def __init__(self, full_card_size: tuple = (750, 1050)):
        self.output_size = full_card_size

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

    def create_card(
        self, character_image: str, name: str, stats: dict, description: str
    ) -> Image.Image:
        # Create base card with rounded corners
        card = self.create_rounded_card_base()

        # Add character image
        char_img = Image.open(character_image)
        img_size = 750
        char_img = char_img.resize((img_size, img_size))

        img_start_x = (self.output_size[0] - char_img.width) // 2
        img_start_y = 100
        card.paste(char_img, (img_start_x, img_start_y))

        # Add text elements
        draw = ImageDraw.Draw(card)

        # Add scroll image under the name
        scroll_img = Image.open("inputs/scroll.png")
        # Resize scroll to fit nicely under the name (make it narrower than the card)
        scroll_width = 700  # Slightly narrower than card width (750)
        scroll_height = int(scroll_img.height * (scroll_width / scroll_img.width) * 1.2)
        scroll_img = scroll_img.resize((scroll_width, scroll_height))

        # Position scroll under the name
        scroll_x = (self.output_size[0] - scroll_width) // 2  # Center horizontally
        scroll_y = 20  # Position under the name text
        card.paste(scroll_img, (scroll_x, scroll_y), scroll_img)

        # Add name
        font_large = ImageFont.truetype("Arial.ttf", 50)
        # Get text bounding box to calculate width for centering
        bbox = draw.textbbox((0, 0), name, font=font_large)
        text_width = bbox[2] - bbox[0]
        text_x = (self.output_size[0] - text_width) // 2
        draw.text((text_x, 80), name, fill=(0, 0, 0), font=font_large)

        # Add stats
        font_medium = ImageFont.truetype("Arial.ttf", 24)
        y_pos = 900
        for stat, value in stats.items():
            draw.text((50, y_pos), f"{stat}: {value}", fill=(0, 0, 0), font=font_medium)
            y_pos += 40

        return card

    def save_card(self, card: Image.Image, output_path: str):
        card.save(output_path, "PNG")


if __name__ == "__main__":
    img_path = "outputs/yogi.png"
    generator = CardGenerator()
    stats = {"Strength": 10, "Agility": 8, "Intelligence": 7}
    card = generator.create_card(img_path, "Hero", stats, "A brave warrior.")
    generator.save_card(card, "outputs/output_card.png")
