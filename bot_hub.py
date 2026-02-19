"""
bot_hub.py — Chatlippytm.ai.Bots Connection HQ
Loads the repository/platform catalog and prints a summary of all connections.
"""

import json
import os


def load_connections(path: str = "connections.json") -> dict:
    """Load the connections catalog from JSON."""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise SystemExit(f"Error: catalog file not found at '{path}'. Ensure connections.json is present.")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Error: '{path}' contains invalid JSON — {exc}")


def print_banner(hub_name: str, description: str) -> None:
    """Print the Connection HQ banner."""
    print("=" * 60)
    print(f"  {hub_name}")
    print(f"  {description}")
    print("=" * 60)


def list_repositories(repositories: list) -> None:
    """Print all registered repositories grouped by category."""
    categories: dict = {}
    for repo in repositories:
        cat = repo.get("category", "other")
        categories.setdefault(cat, []).append(repo)

    print("\n📂 Repositories by Category")
    print("-" * 40)
    for category, repos in sorted(categories.items()):
        print(f"\n  [{category.upper()}]")
        for repo in repos:
            lang = f" ({repo['language']})" if repo.get("language") else ""
            print(f"    • {repo['name']}{lang}")
            print(f"      {repo['url']}")


def list_bot_platforms(platforms: list) -> None:
    """Print all registered bot platforms."""
    print("\n🤖 Bot Platforms Connected")
    print("-" * 40)
    for platform in platforms:
        print(f"  • {platform['name']}: {platform['description']}")
        print(f"    {platform['url']}")


def main() -> None:
    catalog_path = os.path.join(os.path.dirname(__file__), "connections.json")
    data = load_connections(catalog_path)

    print_banner(data["hub"], data["description"])
    list_repositories(data["repositories"])
    list_bot_platforms(data["bot_platforms"])

    total = len(data["repositories"])
    print(f"\n✅ Connection HQ active — {total} repositories registered.\n")


if __name__ == "__main__":
    main()
