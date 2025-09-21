#!/usr/bin/env python3
"""
Test script for the Notion database fetcher.

This script demonstrates how to use the notion.py module to fetch data from a Notion database.
Make sure to set up your .env file with the required credentials before running.
"""

from notion import fetch_notion_card_database, print_database_content


def test_notion_fetcher():
    """Test the Notion database fetcher with different configurations."""

    print("=== Testing Notion Database Fetcher ===\n")

    try:
        # Test 1: Fetch with default configuration
        print("Test 1: Fetching with default fields...")
        data = fetch_notion_card_database()
        print_database_content(data)

        # Test 2: Fetch with custom fields (if you want to test specific fields)
        print("\nTest 2: Fetching with custom fields...")
        custom_fields = ["Nom"]  # Only fetch the name field
        data_custom = fetch_notion_card_database(fields=custom_fields)
        print_database_content(data_custom)

        # Test 3: Return the data as a list of dictionaries for programmatic use
        print("\nTest 3: Working with data programmatically...")
        for i, record in enumerate(data[:3]):  # Show first 3 records
            print(f"Record {i + 1} as dict:", record)

        print(f"\nTotal records fetched: {len(data)}")

    except Exception as e:
        print(f"Error during testing: {e}")
        return False

    return True


if __name__ == "__main__":
    success = test_notion_fetcher()
    if success:
        print("\n✅ Test completed successfully!")
    else:
        print("\n❌ Test failed. Please check your configuration.")
        print("\nSetup checklist:")
        print("1. Create a .env file based on .env.example")
        print("2. Set NOTION_TOKEN with your integration token")
        print("3. Set NOTION_DATABASE_ID with your database ID")
        print("4. Make sure your Notion integration has access to the database")
