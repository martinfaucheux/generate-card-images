import os

from card_generator import CardGenerator
from notion import fetch_notion_card_database
from utils import slugify_name

SUIT_COLOR_MAP = {
    # primary (slightly darker), secondary
    "Chat": ("#ca926e", "#deb48c"),  # Warm beige/tan
    "Lieu": ("#8db4a3", "#a8c7b8"),  # Sage green
    "Rituel": ("#b08bb5", "#c4a5c9"),  # Soft lavender
    "Esprit": ("#7fb3d6", "#9bc7e0"),  # Sky blue
    "Festival": ("#f2a69e", "#f7bfb8"),  # Coral pink
    "Démon": ("#d4818a", "#e0a1a9"),  # Dusty rose
    "Relique": ("#c4a373", "#d4b98a"),  # Antique gold
    "Nourriture": ("#9bc08f", "#b0d0a4"),  # Mint green
    "Potion": ("#a492c2", "#b8a8d1"),  # Soft purple
    "Idole": ("#e0b882", "#edc99a"),  # Peach cream
}


def get_image_path(card_title: str) -> str:
    """Get the file path for a card image based on its title."""
    slug_name = slugify_name(card_title)
    dir_path = f"outputs/full_run/{slug_name}/"

    if not os.path.exists(dir_path):
        raise FileNotFoundError(
            f"No directory found for card: {card_title} / {dir_path}"
        )

    files = [
        f
        for f in os.listdir(dir_path)
        if os.path.isfile(os.path.join(dir_path, f))
        and os.path.splitext(f)[1].lower() in [".png", ".jpg", ".jpeg"]
    ]
    if not files:
        raise FileNotFoundError(f"No files found in directory: {dir_path}")

    if "final.png" in files:
        return os.path.join(dir_path, "final.png")
    else:
        return os.path.join(dir_path, files[0])


if __name__ == "__main__":
    for notion_row in fetch_notion_card_database():
        card_title = notion_row["name"]
        description = notion_row["description"].replace("  ", " ").strip()
        points = notion_row["points"]
        suit_name = notion_row["suit"]
        primary_color, secondary_color = SUIT_COLOR_MAP[suit_name]

        img_path = get_image_path(card_title)
        slug = slugify_name(card_title)

        generator = CardGenerator(
            bg_color_primary=primary_color, bg_color_secondary=secondary_color
        )
        card = generator.create_card(
            img_path,
            card_title,
            description,
            suit_name,
            points,
        )
        output_path = f"outputs/cards/{slug}.png"
        generator.save_card(card, output_path)
        print(f"Saved card to {output_path}")
