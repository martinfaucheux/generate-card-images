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
