import os
from time import sleep

from notion import fetch_notion_database
from run import generate

SLEEP = 0


def slugify_name(name: str) -> str:
    """Convert a name to a slug suitable for filenames."""
    return (
        name.strip()
        .lower()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("'", "")
        .replace("-", "_")
    )


if __name__ == "__main__":
    notion_db_data = fetch_notion_database()

    for notion_row in notion_db_data:
        name = notion_row.get("name")
        prompt = notion_row.get("prompt")

        if not prompt:
            print(f"Skipping '{name}' as it has no prompt.")
            continue

        slug_name = slugify_name(name)

        filepath = f"outputs/full_run1/{slug_name}/{slug_name}_v1"

        if os.path.exists(f"{filepath}.png"):
            print(f"Skipping '{name}' as file already exists.")
            continue

        try:
            generate(prompt, output_path=filepath)

        except Exception as e:
            print(f"Failed to generate image for '{name}': {e}\n")
        else:
            # wait
            sleep(SLEEP)
