import os
import re
from typing import Any, Dict, List

from dotenv import load_dotenv
from notion_client import Client

# Load environment variables from .env file
load_dotenv()

NOTION_CARD_DATABASE_URL = "https://www.notion.so/21602a43b30080c6b950ddae9bad2c5f?v=21602a43b30080fb9187000c588080e2&source=copy_link"
NOTION_SUIT_DATABASE_URL = "https://www.notion.so/21602a43b300804fa47acc1036ce1959?v=21602a43b30080bda6b2000cc82c0e3c&source=copy_link"

NAME_FIELD = ("name", "Nom")
PROMPT_FIELD = ("prompt", "AI image prompt")
SUIT_FIELD = ("suit", "Type de carte")
POINT_FIELD = ("points", "Points")
DESCRIPTION_FIELD = ("description", "Description")

DATABASE_FIELDS = [NAME_FIELD, PROMPT_FIELD, SUIT_FIELD, POINT_FIELD, DESCRIPTION_FIELD]
field_map = {verbose: slug for slug, verbose in DATABASE_FIELDS}


def extract_database_id(url: str) -> str:
    """Extract database ID from Notion database URL."""
    # Pattern to match database ID from various Notion URL formats
    pattern = r"([a-f0-9]{32})"
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    raise ValueError(f"Could not extract database ID from URL: {url}")


def get_text_from_rich_text(rich_text_property: List[Dict]) -> str:
    """Extract plain text from Notion rich text property."""
    if not rich_text_property:
        return ""
    return "".join([text.get("plain_text", "") for text in rich_text_property])


def get_title_from_title_property(title_property: List[Dict]) -> str:
    """Extract plain text from Notion title property."""
    if not title_property:
        return ""
    return "".join([text.get("plain_text", "") for text in title_property])


def get_page_name_from_id(notion_client: Client, page_id: str) -> str:
    """Fetch the page name/title from a page ID."""
    try:
        page = notion_client.pages.retrieve(page_id=page_id)
        properties = page.get("properties", {})

        # Find the title property (it could have various names)
        for prop_name, prop_data in properties.items():
            if prop_data.get("type") == "title":
                return get_title_from_title_property(prop_data.get("title", []))

        # If no title property found, return the page ID
        return page_id
    except Exception as e:
        print(f"Warning: Could not fetch page name for ID {page_id}: {e}")
        return page_id


def extract_simple_field_value(
    property_data: Dict,
    property_type: str,
    notion_client: Client = None,
    suit_cache: Dict[str, str] = None,
) -> Any:
    """Extract value from a simple Notion property based on its type."""
    if property_type == "title":
        return get_title_from_title_property(property_data.get("title", []))
    elif property_type == "rich_text":
        return get_text_from_rich_text(property_data.get("rich_text", []))
    elif property_type == "number":
        return property_data.get("number")
    elif property_type == "checkbox":
        return property_data.get("checkbox", False)
    elif property_type == "date":
        date_data = property_data.get("date")
        return date_data.get("start") if date_data else None
    elif property_type == "select":
        select_data = property_data.get("select")
        return select_data.get("name") if select_data else None
    elif property_type == "multi_select":
        multi_select_data = property_data.get("multi_select", [])
        return [item.get("name") for item in multi_select_data]
    elif property_type == "relation":
        relation_data = property_data.get("relation", [])
        if not relation_data:
            return None

        # Extract page IDs from relations
        page_ids = [item.get("id") for item in relation_data]

        # If we have a suit cache, use it to resolve page names
        if suit_cache is not None:
            for page_id in page_ids:
                if page_id in suit_cache:
                    return suit_cache[page_id]
                else:
                    raise ValueError(
                        f"Relation page ID {page_id} not found in suit cache. Please ensure all referenced pages are cached."
                    )
            else:
                # If none of the page IDs were found in the cache
                return None

        else:
            return None
    elif property_type == "url":
        return property_data.get("url")
    elif property_type == "email":
        return property_data.get("email")
    elif property_type == "phone_number":
        return property_data.get("phone_number")
    else:
        # For unsupported types, return None
        return None


def fetch_notion_card_database(
    database_id: str = None, fields: List[str] = None
) -> List[Dict[str, Any]]:
    """
    Fetch content from a Notion database and return as a list of dictionaries.

    Args:
        database_id: Notion database ID. If None, uses environment variable or extracts from URL.
        fields: List of field names to extract. If None, uses DATABASE_FIELDS constant.

    Returns:
        List of dictionaries containing the specified fields for each database row.
    """
    # Initialize Notion client
    token = os.environ.get("NOTION_TOKEN")
    if not token:
        raise ValueError("NOTION_TOKEN environment variable is required")

    notion = Client(auth=token)

    # Determine database ID
    if database_id is None:
        database_id = os.environ.get("NOTION_DATABASE_ID")
        if database_id is None:
            database_id = extract_database_id(NOTION_CARD_DATABASE_URL)

    # Determine fields to extract
    if fields is None:
        fields = [f[1] for f in DATABASE_FIELDS]  # Use list instead of generator

    try:
        # Prefetch suit names for relation resolution
        suit_cache = fetch_notion_suit_database()

        # Query the database
        response = notion.databases.query(database_id=database_id)

        results = []

        for page in response.get("results", []):
            page_data = {}
            page_properties = page.get("properties", {})

            for notion_field_name in fields:
                field_slug = field_map[notion_field_name]
                if notion_field_name in page_properties:
                    property_data = page_properties[notion_field_name]
                    property_type = property_data.get("type")

                    # Extract the value based on property type
                    value = extract_simple_field_value(
                        property_data, property_type, notion, suit_cache
                    )
                    page_data[field_slug] = value
                else:
                    # Field not found in this page
                    page_data[field_slug] = None

            results.append(page_data)

        return results

    except Exception as e:
        raise Exception(f"Error fetching Notion database: {str(e)}")


def fetch_notion_suit_database() -> dict[str, str]:
    """
    Fetch the database and map the page id to the page name
    """
    # Initialize Notion client
    token = os.environ.get("NOTION_TOKEN")
    if not token:
        raise ValueError("NOTION_TOKEN environment variable is required")

    notion = Client(auth=token)

    # Determine database ID
    database_id = os.environ.get("NOTION_SUIT_DATABASE_ID")
    if database_id is None:
        database_id = extract_database_id(NOTION_SUIT_DATABASE_URL)

    try:
        # Query the database
        response = notion.databases.query(database_id=database_id)

        results = {}

        for page in response.get("results", []):
            page_properties = page.get("properties", {})
            name_property = page_properties.get("Nom")
            if name_property and name_property.get("type") == "title":
                name = get_title_from_title_property(name_property.get("title", []))
                results[page["id"]] = name

        return results

    except Exception as e:
        raise Exception(f"Error fetching Notion database: {str(e)}")


def print_database_content(data: List[Dict[str, Any]]) -> None:
    """Pretty print the database content."""
    if not data:
        print("No data found in database.")
        return

    print(f"Found {len(data)} records:")
    print("-" * 50)

    for i, record in enumerate(data, 1):
        print(f"Record {i}:")
        for field, value in record.items():
            print(f"  {field}: {value}")
        print()


if __name__ == "__main__":
    # Example usage
    try:
        database_content = fetch_notion_card_database()
        from pprint import pprint

        pprint(database_content)
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure to:")
        print("1. Set NOTION_TOKEN in your .env file")
        print(
            "2. Set NOTION_DATABASE_ID in your .env file (or update NOTION_DATABASE_URL)"
        )
        print("3. Grant your Notion integration access to the database")
