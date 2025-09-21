import os

from card_generator import CardGenerator
from notion import fetch_notion_card_database
from utils import slugify_name

SUIT_COLOR_MAP = {
    # primary (pastel), secondary (lighter)
    "Chat": ("#E6A8A8", "#F5D4D4"),  # Red: pastel red, lighter red
    "Lieu": ("#8B8B8B", "#C4C4C4"),  # Black: pastel grey, lighter grey
    "Rituel": ("#8BA8E6", "#C4D4F5"),  # Dark blue: pastel blue, lighter blue
    "Esprit": ("#A8E6A8", "#D4F5D4"),  # Green: pastel green, lighter green
    "Festival": ("#E6A8E6", "#F5D4F5"),  # Pink: pastel pink, lighter pink
    "Démon": ("#C8A8E6", "#E4D4F5"),  # Purple: pastel purple, lighter purple
    "Relique": ("#B8B8B8", "#DCDCDC"),  # Grey: pastel grey, lighter grey
    "Idole": ("#E6E6A8", "#F5F5D4"),  # Yellow: pastel yellow, lighter yellow
    "Nourriture": ("#D4B08A", "#E8CDB0"),  # Brown: pastel brown, lighter brown
    "Potion": ("#A8D4E6", "#D4E8F5"),  # Light blue
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
            card_title,
            description,
            suit_name,
            points,
        )
        output_path = f"outputs/cards/{slug}.png"
        generator.save_card(card, output_path)
        print(f"{idx}\tSaved card to {output_path}")
