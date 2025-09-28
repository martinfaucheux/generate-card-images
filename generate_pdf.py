import os

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from generate_all_cards import generate_card_from_notion_row
from notion import fetch_notion_card_database


def generate_pdf(output_path: str = "outputs/pdf/cards.pdf", max_cards: int = None):
    """
    Generate a PDF file with all cards from the Notion database.
    Each page contains one card with margins and cutting lines for professional printing.

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

    # Define margins and card dimensions
    margin = 20 * mm  # 20mm margin on all sides
    cutting_line_distance = 1 * mm  # 2mm distance from card border
    cutting_line_length = 5 * mm  # 5mm length for cutting lines

    # Fixed card dimensions (63mm x 88mm)
    card_width_mm = 63 * mm
    card_height_mm = 88 * mm

    def draw_cutting_lines(c, card_x, card_y, final_card_width, final_card_height):
        """Draw cutting lines around a card at the specified position."""
        c.setDash()  # Solid lines
        c.setStrokeColorRGB(0.5, 0.5, 0.5)  # Gray color
        c.setLineWidth(0.5)

        # Top-left corner cutting lines
        c.line(
            card_x - cutting_line_length / 2,
            card_y + final_card_height + cutting_line_distance,
            card_x + cutting_line_length / 2,
            card_y + final_card_height + cutting_line_distance,
        )
        c.line(
            card_x - cutting_line_distance,
            card_y + final_card_height - cutting_line_length / 2,
            card_x - cutting_line_distance,
            card_y + final_card_height + cutting_line_length / 2,
        )

        # Top-right corner cutting lines
        c.line(
            card_x + final_card_width - cutting_line_length / 2,
            card_y + final_card_height + cutting_line_distance,
            card_x + final_card_width + cutting_line_length / 2,
            card_y + final_card_height + cutting_line_distance,
        )
        c.line(
            card_x + final_card_width + cutting_line_distance,
            card_y + final_card_height - cutting_line_length / 2,
            card_x + final_card_width + cutting_line_distance,
            card_y + final_card_height + cutting_line_length / 2,
        )

        # Bottom-left corner cutting lines
        c.line(
            card_x - cutting_line_length / 2,
            card_y - cutting_line_distance,
            card_x + cutting_line_length / 2,
            card_y - cutting_line_distance,
        )
        c.line(
            card_x - cutting_line_distance,
            card_y - cutting_line_length / 2,
            card_x - cutting_line_distance,
            card_y + cutting_line_length / 2,
        )

        # Bottom-right corner cutting lines
        c.line(
            card_x + final_card_width - cutting_line_length / 2,
            card_y - cutting_line_distance,
            card_x + final_card_width + cutting_line_length / 2,
            card_y - cutting_line_distance,
        )
        c.line(
            card_x + final_card_width + cutting_line_distance,
            card_y - cutting_line_length / 2,
            card_x + final_card_width + cutting_line_distance,
            card_y + cutting_line_length / 2,
        )

    print(f"Generating PDF with {len(notion_rows)} cards + cover...")

    for idx, notion_row in enumerate(notion_rows):
        print(f"Processing card {idx + 1}/{len(notion_rows)}: {notion_row['name']}")

        try:
            # Generate card image
            slug, card_image = generate_card_from_notion_row(
                notion_row, extra_bold_words
            )

            # Save temporary card image
            temp_card_path = f"outputs/temp_card_{slug}.png"
            card_image.save(temp_card_path, "PNG")

            # Use fixed card dimensions (63mm x 88mm)
            final_card_width = card_width_mm
            final_card_height = card_height_mm

            # Center the card in the page
            card_x = (page_width - final_card_width) / 2
            card_y = (page_height - final_card_height) / 2

            # Draw cutting lines
            draw_cutting_lines(c, card_x, card_y, final_card_width, final_card_height)

            # Draw the card image
            c.drawImage(
                temp_card_path,
                card_x,
                card_y,
                width=final_card_width,
                height=final_card_height,
            )

            # Clean up temporary file
            os.remove(temp_card_path)

        except Exception as e:
            print(f"Error processing card {notion_row['name']}: {e}")
            # Draw error message on the page
            c.setFillColorRGB(1, 0, 0)  # Red color
            c.setFont("Helvetica", 12)
            c.drawString(
                margin, page_height / 2, f"Error generating card: {notion_row['name']}"
            )
            c.drawString(margin, page_height / 2 - 20, f"Error: {str(e)}")

        # Start new page for next card
        if idx < len(notion_rows) - 1:
            c.showPage()

    # Add cover page as the last page
    if len(notion_rows) > 0:
        c.showPage()

    print("Adding cover page...")
    try:
        cover_image_path = "inputs/cover_square_border.png"

        # Use same card dimensions for the cover
        final_card_width = card_width_mm
        final_card_height = card_height_mm

        # Center the cover in the page
        card_x = (page_width - final_card_width) / 2
        card_y = (page_height - final_card_height) / 2

        # Draw cutting lines for cover
        draw_cutting_lines(c, card_x, card_y, final_card_width, final_card_height)

        # Draw the cover image
        c.drawImage(
            cover_image_path,
            card_x,
            card_y,
            width=final_card_width,
            height=final_card_height,
        )

    except Exception as e:
        print(f"Error adding cover page: {e}")
        # Draw error message on the page
        c.setFillColorRGB(1, 0, 0)  # Red color
        c.setFont("Helvetica", 12)
        c.drawString(margin, page_height / 2, "Error adding cover page")
        c.drawString(margin, page_height / 2 - 20, f"Error: {str(e)}")

    # Save the PDF
    c.save()
    print(f"PDF generated successfully: {output_path}")
    print(f"Total pages: {len(notion_rows) + 1} (including cover)")


def generate_test_pdf(num_cards: int = 3):
    """Generate a test PDF with a limited number of cards."""
    output_path = f"outputs/pdf/test_cards_{num_cards}.pdf"
    generate_pdf(output_path, max_cards=num_cards)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Generate test PDF with 3 cards
        generate_test_pdf(3)
    else:
        # Generate full PDF
        generate_pdf()
