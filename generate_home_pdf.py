import math
import os

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from generate_all_cards import generate_card_from_notion_row
from notion import fetch_notion_card_database


def generate_home_pdf(
    output_path: str = "outputs/pdf/home_cards.pdf", max_cards: int = None
):
    """
    Generate a PDF file for home printing with 9 cards per page.
    Alternates between card fronts and cover backs for double-sided printing.

    Args:
        output_path: Path where the PDF file will be saved
        max_cards: Maximum number of cards to include (None for all cards)
    """
    # Fetch data from Notion
    print("Fetching card data from Notion...")
    notion_rows = fetch_notion_card_database()

    # Limit number of cards if specified
    if max_cards is not None:
        notion_rows = notion_rows[:max_cards]
        print(f"Limited to first {max_cards} cards")

    extra_bold_words = {row["name"] for row in notion_rows}

    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Create PDF canvas
    c = canvas.Canvas(output_path, pagesize=A4)
    page_width, page_height = A4

    # Define margins and card layout
    margin = 10 * mm  # 10mm margin on all sides
    spacing = 5 * mm  # 5mm spacing between cards
    cards_per_row = 3
    cards_per_col = 3
    cards_per_page = cards_per_row * cards_per_col  # 9 cards per page

    # Calculate available space for cards (accounting for spacing)
    available_width = page_width - 2 * margin - (cards_per_row - 1) * spacing
    available_height = page_height - 2 * margin - (cards_per_col - 1) * spacing

    # Calculate card dimensions to fit 9 cards on a page with spacing
    card_width = available_width / cards_per_row
    card_height = available_height / cards_per_col

    # Cover dimensions
    cover_scale = 1
    cover_width = card_width * cover_scale
    cover_height = card_height * cover_scale

    def get_card_positions():
        """Calculate positions for all 9 cards on a page with spacing."""
        positions = []
        for row in range(cards_per_col):
            for col in range(cards_per_row):
                x = margin + col * (card_width + spacing)
                y = page_height - margin - (row + 1) * card_height - row * spacing
                positions.append((x, y))
        return positions

    def get_cover_positions():
        """Calculate positions for covers (centered on the same positions as cards)."""
        card_positions = get_card_positions()
        cover_positions = []
        for card_x, card_y in card_positions:
            # Center the larger cover on the same position as the card
            cover_x = card_x - (cover_width - card_width) / 2
            cover_y = card_y - (cover_height - card_height) / 2
            cover_positions.append((cover_x, cover_y))
        return cover_positions

    # Calculate total number of pages needed
    total_cards = len(notion_rows)
    pages_for_cards = math.ceil(total_cards / cards_per_page)

    print(
        f"Generating PDF with {total_cards} cards on {pages_for_cards} card pages + {pages_for_cards} cover pages..."
    )

    # Generate all card images first to avoid regenerating them
    print("Generating card images...")
    card_images = []
    temp_files = []

    for idx, notion_row in enumerate(notion_rows):
        print(f"Processing card {idx + 1}/{len(notion_rows)}: {notion_row['name']}")
        try:
            slug, card_image = generate_card_from_notion_row(
                notion_row, extra_bold_words
            )
            temp_card_path = f"outputs/temp_home_card_{slug}.png"
            card_image.save(temp_card_path, "PNG")
            card_images.append(temp_card_path)
            temp_files.append(temp_card_path)
        except Exception as e:
            print(f"Error processing card {notion_row['name']}: {e}")
            card_images.append(None)

    # Generate pages
    card_positions = get_card_positions()
    cover_positions = get_cover_positions()
    cover_image_path = "inputs/cover_square_border.png"

    page_num = 1

    # Generate card pages and corresponding cover pages
    for page_idx in range(pages_for_cards):
        # Card front page
        print(f"Generating page {page_num}: Card fronts")

        start_idx = page_idx * cards_per_page
        end_idx = min(start_idx + cards_per_page, total_cards)

        for pos_idx, card_idx in enumerate(range(start_idx, end_idx)):
            if card_images[card_idx] is not None:
                x, y = card_positions[pos_idx]
                try:
                    c.drawImage(
                        card_images[card_idx],
                        x,
                        y,
                        width=card_width,
                        height=card_height,
                    )
                except Exception as e:
                    print(f"Error drawing card {card_idx}: {e}")
                    # Draw error placeholder
                    c.setFillColorRGB(1, 0, 0)
                    c.setFont("Helvetica", 8)
                    c.drawString(x + 5, y + card_height / 2, f"Error: Card {card_idx}")

        # Start new page for covers
        c.showPage()
        page_num += 1

        # Cover back page (mirrored positions for double-sided printing)
        print(f"Generating page {page_num}: Card backs (covers)")

        # For double-sided printing, we need to mirror the positions horizontally
        # so that when the page is flipped, covers align with fronts
        for pos_idx in range(min(cards_per_page, end_idx - start_idx)):
            # Mirror the column position (0->2, 1->1, 2->0)
            original_row = pos_idx // cards_per_row
            original_col = pos_idx % cards_per_row
            mirrored_col = cards_per_row - 1 - original_col
            mirrored_pos_idx = original_row * cards_per_row + mirrored_col

            x, y = cover_positions[mirrored_pos_idx]

            try:
                c.drawImage(
                    cover_image_path, x, y, width=cover_width, height=cover_height
                )
            except Exception as e:
                print(f"Error drawing cover at position {pos_idx}: {e}")
                # Draw error placeholder
                c.setFillColorRGB(1, 0, 0)
                c.setFont("Helvetica", 8)
                c.drawString(x + 5, y + cover_height / 2, f"Error: Cover {pos_idx}")

        # Start new page if not the last iteration
        if page_idx < pages_for_cards - 1:
            c.showPage()
            page_num += 1

    # Save the PDF
    c.save()

    # Clean up temporary files
    for temp_file in temp_files:
        try:
            os.remove(temp_file)
        except Exception:
            pass

    print(f"PDF generated successfully: {output_path}")
    print(f"Total pages: {page_num}")
    print(f"Cards per page: {cards_per_page}")
    print(f"Card dimensions: {card_width / mm:.1f}mm x {card_height / mm:.1f}mm")
    print(f"Cover dimensions: {cover_width / mm:.1f}mm x {cover_height / mm:.1f}mm")
    print("\nPrinting instructions:")
    print("1. Print double-sided (flip on long edge)")
    print("2. Odd pages contain card fronts")
    print("3. Even pages contain card backs (covers)")


def generate_test_home_pdf(num_cards: int = 18):
    """Generate a test PDF with a limited number of cards (default 18 for 2 pages)."""
    output_path = f"outputs/pdf/test_home_cards_{num_cards}.pdf"
    generate_home_pdf(output_path, max_cards=num_cards)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Generate test PDF with 18 cards (2 pages of 9 cards each)
        generate_test_home_pdf(18)
    else:
        # Generate full PDF
        generate_home_pdf()
