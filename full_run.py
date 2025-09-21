import os
from time import sleep

from notion import fetch_notion_card_database
from run import generate
from utils import slugify_name

SLEEP = 0


if __name__ == "__main__":
    notion_db_data = fetch_notion_card_database()

    for notion_row in notion_db_data:
        name = notion_row.get("name")
        prompt = notion_row.get("prompt")

        if not prompt:
            print(f"Skipping '{name}' as it has no prompt.")
            continue

        slug_name = slugify_name(name)

        filepath = f"outputs/full_run/{slug_name}/{slug_name}_v1"

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
