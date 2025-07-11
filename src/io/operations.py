#!/usr/bin/env python3
"""
Pure functions for file I/O operations.
"""

import json
import os
import yaml
from rich.console import Console

from src.core.types import (
    FlashCard,
    FlashcardSet,
    FlashcardSetStats,
    CardStats,
)


def load_flashcard_file(file_path: str) -> FlashcardSet | None:
    """Load flashcards from a YAML file."""
    try:
        with open(file_path, "r") as f:
            data = yaml.safe_load(f)

        # Extract set name from file path
        set_name = (
            os.path.basename(file_path)
            .replace(".yaml", "")
            .replace(".yml", "")
        )

        # Get custom title or use filename as fallback
        title = data.get("title", set_name.replace("_", " ").title())

        cards = [
            FlashCard(
                question=card["question"],
                answer=card["answer"],
                code_example=card.get("code_example"),
            )
            for card in data["flashcards"]
        ]

        return FlashcardSet(
            cards=cards, name=set_name, title=title, file_path=file_path
        )

    except FileNotFoundError:
        console = Console()
        console.print(f"[red]Error: Could not find {file_path}[/red]")
        return None
    except yaml.YAMLError as e:
        console = Console()
        console.print(
            f"[red]Error: Invalid YAML format in {file_path}: {e}[/red]"
        )
        return None


def load_statistics_file(stats_file: str) -> dict[str, FlashcardSetStats]:
    """Load statistics from JSON file."""
    try:
        with open(stats_file, "r") as f:
            stats = json.load(f)

        # Check if this is the old format (needs migration)
        if "correct_answers" in stats and "flashcard_sets" not in stats:
            # Migrate old format to new per-set format
            legacy_card_stats = {}
            for card_key, card_data in stats.get("card_stats", {}).items():
                legacy_card_stats[card_key] = CardStats(
                    correct=card_data.get("correct", 0),
                    total=card_data.get("total", 0),
                )

            return {
                "legacy_data": FlashcardSetStats(
                    correct_answers=stats.get("correct_answers", 0),
                    total_attempts=stats.get("total_attempts", 0),
                    card_stats=legacy_card_stats,
                )
            }
        else:
            # Load new format
            flashcard_sets_data = stats.get("flashcard_sets", {})
            result = {}

            for set_name, set_data in flashcard_sets_data.items():
                card_stats = {}
                for card_key, card_data in set_data.get(
                    "card_stats", {}
                ).items():
                    card_stats[card_key] = CardStats(
                        correct=card_data.get("correct", 0),
                        total=card_data.get("total", 0),
                    )

                result[set_name] = FlashcardSetStats(
                    correct_answers=set_data.get("correct_answers", 0),
                    total_attempts=set_data.get("total_attempts", 0),
                    card_stats=card_stats,
                )

            return result

    except FileNotFoundError:
        # First time running, stats file doesn't exist yet
        return {}
    except json.JSONDecodeError:
        # Corrupted stats file, reset to defaults
        return {}


def save_statistics_file(
    stats_file: str, set_stats: dict[str, FlashcardSetStats]
) -> bool:
    """Save statistics to JSON file."""
    # Convert dataclasses to dictionaries for JSON serialization
    flashcard_sets_dict = {}
    for set_name, stats in set_stats.items():
        card_stats_dict = {}
        for card_key, card_stats in stats.card_stats.items():
            card_stats_dict[card_key] = {
                "correct": card_stats.correct,
                "total": card_stats.total,
            }

        flashcard_sets_dict[set_name] = {
            "correct_answers": stats.correct_answers,
            "total_attempts": stats.total_attempts,
            "card_stats": card_stats_dict,
        }

    stats_data = {"flashcard_sets": flashcard_sets_dict}
    try:
        with open(stats_file, "w") as f:
            json.dump(stats_data, f, indent=2)
        return True
    except Exception as e:
        console = Console()
        console.print(
            f"[yellow]Warning: Could not save statistics: {e}[/yellow]"
        )
        return False


def discover_flashcard_sets(
    directory: str = "flashcard_sets",
) -> list[tuple[str, str]]:
    """Discover all flashcard files in the specified directory."""
    flashcard_sets: list[tuple[str, str, str]] = []

    if not os.path.exists(directory):
        return []

    for filename in os.listdir(directory):
        valid_extensions = (".yaml", ".yml")
        if filename.endswith(valid_extensions) and not filename.startswith(
            "."
        ):
            file_path = os.path.join(directory, filename)

            # Try to read the custom title from the file
            try:
                with open(file_path, "r") as f:
                    data = yaml.safe_load(f)

                # Use custom title and icon if available, otherwise fallback to filename
                if data and "title" in data:
                    title = data["title"]
                    icon = data.get("icon", "")
                    display_name = f"{icon} {title}".strip() if icon else title
                    sort_key = title  # Sort by title only, ignoring icon
                else:
                    display_name = filename.replace(".yaml", "").replace(
                        ".yml", ""
                    )
                    display_name = display_name.replace("_", " ").title()
                    sort_key = display_name
            except Exception:
                # If file can't be read, use filename as fallback
                display_name = filename.replace(".yaml", "").replace(
                    ".yml", ""
                )
                display_name = display_name.replace("_", " ").title()
                sort_key = display_name

            flashcard_sets.append((display_name, file_path, sort_key))

    # Sort by title alphabetically (ignoring icons)
    flashcard_sets.sort(key=lambda x: x[2].lower())

    # Return only display_name and file_path (remove sort_key)
    return [
        (display_name, file_path)
        for display_name, file_path, _ in flashcard_sets
    ]


def get_set_display_name(set_name: str) -> str:
    """Get the display name for a flashcard set."""
    directory = "flashcard_sets"
    if os.path.exists(directory):
        for filename in os.listdir(directory):
            if filename.endswith((".yaml", ".yml")):
                file_set_name = filename.replace(".yaml", "").replace(
                    ".yml", ""
                )
                if file_set_name == set_name:
                    try:
                        file_path = os.path.join(directory, filename)
                        with open(file_path, "r") as f:
                            data = yaml.safe_load(f)

                        if data and "title" in data:
                            title = data["title"]
                            icon = data.get("icon", "")
                            return f"{icon} {title}".strip() if icon else title
                    except Exception:
                        pass

    # Fallback to formatted filename
    return set_name.replace("_", " ").title()


def get_set_card_count(set_name: str) -> int:
    """Get the number of cards in a flashcard set."""
    directory = "flashcard_sets"
    if os.path.exists(directory):
        for filename in os.listdir(directory):
            if filename.endswith((".yaml", ".yml")):
                file_set_name = filename.replace(".yaml", "").replace(
                    ".yml", ""
                )
                if file_set_name == set_name:
                    try:
                        file_path = os.path.join(directory, filename)
                        with open(file_path, "r") as f:
                            data = yaml.safe_load(f)

                        if data and "flashcards" in data:
                            return len(data["flashcards"])
                    except Exception:
                        pass
    return 0
