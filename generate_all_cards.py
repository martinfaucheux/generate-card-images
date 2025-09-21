import os

from card_generator import CardGenerator
from notion import fetch_notion_card_database
from utils import slugify_name

SUIT_COLOR_MAP = {
    # primary (vibrant), secondary (lighter)
    "Chat": ("#D32F2F", "#FFCDD2"),  # Red: vibrant red, light red
    "Lieu": ("#424242", "#9E9E9E"),  # Black: dark grey, medium grey
    "Rituel": ("#1976D2", "#BBDEFB"),  # Dark blue: vibrant blue, light blue
    "Esprit": ("#388E3C", "#C8E6C9"),  # Green: vibrant green, light green
    "Festival": ("#E91E63", "#F8BBD9"),  # Pink: vibrant pink, light pink
    "Démon": ("#7B1FA2", "#E1BEE7"),  # Purple: vibrant purple, light purple
    "Relique": ("#757575", "#E0E0E0"),  # Grey: medium grey, light grey
    "Idole": ("#F57C00", "#FFE0B2"),  # Yellow: vibrant orange-yellow, light yellow
    "Nourriture": ("#8D6E63", "#D7CCC8"),  # Brown: vibrant brown, light brown
    "Potion": ("#0097A7", "#B2EBF2"),  # Light blue: vibrant cyan, light cyan
}

TEXTURE_MAP = {
    "Chat": "paw_texture.png",
    "Lieu": "place_texture.png",
    "Rituel": "yoga_texture.png",
    "Esprit": "lotus_texture.png",
    "Festival": "party_texture.png",
    "Démon": "deamon_texture.png",
    "Relique": "vase_texture.png",
    "Idole": "star_texture.png",
    "Nourriture": "burger_texture.png",
    "Potion": "potion_texture.png",
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
    for idx, notion_row in enumerate(fetch_notion_card_database()):
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
            f"inputs/textures/{TEXTURE_MAP[suit_name]}",
            card_title,
            description,
            suit_name,
            points,
        )
        output_path = f"outputs/cards/{slug}.png"
        generator.save_card(card, output_path)
        print(f"{idx}\tSaved card to {output_path}")
