#!/usr/bin/env python3
"""
Main application entry point for the flashcard application.
"""

import argparse
import os
import sys
from rich.console import Console
from rich.prompt import Prompt

from flashcard_types import AppState, FlashcardSetStats
from io_operations import (
    load_flashcard_file,
    load_statistics_file,
    save_statistics_file,
    discover_flashcard_sets,
)
from ui import (
    display_menu,
    display_flashcard_set_menu_with_stats,
    display_global_statistics,
    display_exit_message,
)
from study_session import handle_menu_choice


def create_app_state(stats_file: str) -> AppState:
    """Create initial application state."""
    set_stats = load_statistics_file(stats_file)
    return AppState(flashcard_sets=set_stats)


def run_flashcard_app(file_path: str, stats_file: str) -> None:
    """Run the flashcard application for a specific file."""
    console = Console()

    # Load flashcard set
    flashcard_set = load_flashcard_file(file_path)
    if flashcard_set is None:
        sys.exit(1)

    # Load application state
    app_state = create_app_state(stats_file)

    # Get or create stats for this set
    current_set_stats = app_state.flashcard_sets.get(
        flashcard_set.name, FlashcardSetStats()
    )

    console.print(
        f"[green]Loaded {len(flashcard_set.cards)} flashcards "
        f"successfully![/green]"
    )

    # Main application loop
    while True:
        display_menu(console, flashcard_set.title)
        choice = Prompt.ask(
            "[yellow]Choose an option[/yellow]",
            choices=["1", "2", "s", "q"],
            default="1",
        )

        result = handle_menu_choice(
            console, choice, flashcard_set, current_set_stats
        )

        if result == "exit":
            break
        elif result is not None and isinstance(
            result, type(current_set_stats)
        ):
            # Update stats and save
            current_set_stats = result
            updated_app_state = AppState(
                flashcard_sets={
                    **app_state.flashcard_sets,
                    flashcard_set.name: current_set_stats,
                }
            )
            save_statistics_file(stats_file, updated_app_state.flashcard_sets)
            app_state = updated_app_state


def run_set_selection_menu(stats_file: str) -> None:
    """Run the set selection menu."""
    console = Console()
    app_state = create_app_state(stats_file)

    while True:
        flashcard_sets = discover_flashcard_sets()
        choice = display_flashcard_set_menu_with_stats(console, flashcard_sets)

        if choice == "stats":
            display_global_statistics(console, app_state.flashcard_sets)
        elif choice == "quit":
            display_exit_message(console)
            break
        else:
            # choice is a file path, run the flashcard app
            run_flashcard_app(choice, stats_file)
            # Reload stats after study session
            app_state = create_app_state(stats_file)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Interactive flashcard application for studying "
        "Python concepts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                               # Selection menu
  python main.py flashcard_sets/math.yaml      # Use specific set
  python main.py flashcard_sets/science.json   # Use JSON format
  python main.py --help                        # Show help
        """,
    )
    parser.add_argument(
        "file",
        nargs="?",
        default=None,
        help=(
            "Path to the flashcard file (YAML or JSON format). "
            "If not specified, shows set selection menu."
        ),
    )
    parser.add_argument(
        "--stats",
        default="flashcard_stats.json",
        help="Path to the statistics file (default: flashcard_stats.json)",
    )

    args = parser.parse_args()

    # If no file specified, show set selection menu
    if args.file is None:
        run_set_selection_menu(args.stats)
    else:
        # Direct file specified - validate and run
        if not os.path.exists(args.file):
            print(f"Error: Flashcard file '{args.file}' not found.")
            print(
                "Please make sure the file exists or use --help for usage "
                "information."
            )
            sys.exit(1)

        run_flashcard_app(args.file, args.stats)


if __name__ == "__main__":
    main()
