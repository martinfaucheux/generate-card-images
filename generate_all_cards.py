import os

from card_generator import CardGenerator
from notion import fetch_notion_card_database
from utils import slugify_name

SUIT_COLOR_MAP = {
    # primary (vibrant), secondary (lighter)
    "Chat": ("#D32F2F", "#FF8B8B"),  # Red: vibrant red, light red
    "Lieu": ("#7E7E7E", "#9E9E9E"),  # Black: dark grey, medium grey
    "Rituel": ("#1976D2", "#63B7FD"),  # Dark blue: vibrant blue, light blue
    "Esprit": ("#388E3C", "#C8E6C9"),  # Green: vibrant green, light green
    "Festival": ("#FD80C3", "#FFDDED"),  # Pink: vibrant pink, light pink
    "Démon": ("#7B1FA2", "#E1BEE7"),  # Purple: vibrant purple, light purple
    "Relique": ("#FFE100", "#FFFBD3"),  # Yellow
    "Idole": ("#F57C00", "#F8C578"),  # Orange: vibrant orange-yellow, light yellow
    "Nourriture": ("#8D6E63", "#D7CCC8"),  # Brown: vibrant brown, light brown
    "Potion": ("#00C9B1", "#B2EBF2"),  # Light blue: vibrant cyan, light cyan
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

LOGO_MAP = {
    "Chat": "paw.png",
    "Lieu": "place.png",
    "Rituel": "yoga.png",
    "Esprit": "lotus.png",
    "Festival": "party.png",
    "Démon": "demon.png",
    "Relique": "vase.png",
    "Idole": "star.png",
    "Nourriture": "burger.png",
    "Potion": "potion.png",
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


def generate_card_from_notion_row(notion_row, extra_bold_words):
    card_title = notion_row["name"].strip()
    description = notion_row["description"].replace("  ", " ").strip()
    points = notion_row["points"]
    suit_name = notion_row["suit"]
    primary_color, secondary_color = SUIT_COLOR_MAP[suit_name]

    img_path = get_image_path(card_title)
    slug = slugify_name(card_title)

    generator = CardGenerator(
        bg_color_primary=primary_color,
        bg_color_secondary=secondary_color,
        extra_bold_words=extra_bold_words,
    )
    return slug, generator.create_card(
        img_path,
        f"inputs/logos/{LOGO_MAP[suit_name]}",
        card_title,
        description,
        suit_name,
        points,
    )


if __name__ == "__main__":
    notion_rows = fetch_notion_card_database()
    extra_bold_words = {row["name"] for row in notion_rows}
    for idx, notion_row in enumerate(notion_rows):
        slug, card = generate_card_from_notion_row(notion_row, extra_bold_words)
        output_path = f"outputs/cards/{slug}.png"

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        card.save(output_path, "PNG")
        print(f"{idx}\tSaved card to {output_path}")
