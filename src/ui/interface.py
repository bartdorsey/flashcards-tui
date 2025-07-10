#!/usr/bin/env python3
"""
Pure functions for UI rendering.
"""

import sys
from typing import Any
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text
from rich.table import Table
from rich.align import Align
from rich.syntax import Syntax

from src.core.types import FlashCard, FlashcardSet, FlashcardSetStats
from src.io.operations import get_set_display_name, get_set_card_count
from src.core.statistics import get_most_challenging_cards


def display_menu(console: Console, set_title: str) -> None:
    """Display the main menu."""
    console.clear()
    title = Text(f"🎓 {set_title}", style="bold blue")
    console.print(Align.center(title))
    console.print()

    menu_options = [
        "1. Study all flashcards",
        "2. Study random flashcards",
        "s. View statistics",
        "q. Exit",
    ]

    for option in menu_options:
        console.print(f"  {option}")

    console.print()


def display_progress(console: Console, current: int, total: int) -> None:
    """Display current progress."""
    progress = f"Card {current}/{total}"
    console.print(f"[dim]{progress}[/dim]")
    console.print()


def display_question(console: Console, card: FlashCard) -> None:
    """Display a flashcard question."""
    question_panel = Panel(
        card.question,
        title="❓ Question",
        border_style="blue",
        padding=(1, 2),
        width=80,
    )
    console.print(question_panel)


def wait_for_user_thinking(console: Console) -> None:
    """Wait for user to think about the answer."""
    Prompt.ask(
        "\n[yellow]Think about it, then press Enter to reveal "
        "the answer[/yellow]",
        default="",
    )


def display_answer(console: Console, card: FlashCard) -> None:
    """Display the flashcard answer."""
    answer_panel = Panel(
        card.answer,
        title="✅ Answer",
        border_style="green",
        padding=(1, 2),
        width=80,
    )
    console.print(answer_panel)


def display_code_example(console: Console, card: FlashCard) -> None:
    """Display code example if available."""
    if card.code_example:
        console.print()
        _display_code_with_expansion(console, card.code_example)


def _calculate_max_code_lines(console: Console) -> int:
    """Calculate maximum code lines based on terminal height."""
    terminal_height = console.size.height
    
    # Reserve space for UI elements:
    # - Question panel: ~6 lines (title, borders, padding, content)
    # - Answer panel: ~6 lines (title, borders, padding, content) 
    # - Progress display: ~2 lines
    # - Prompts and spacing: ~6 lines
    # - Code panel borders/title: ~4 lines
    # - Breathing room: ~3 lines
    reserved_lines = 27
    
    available_lines = terminal_height - reserved_lines
    
    # Set reasonable bounds: minimum 8 lines, maximum 30 lines
    return max(8, min(available_lines, 30))


def _display_code_with_expansion(console: Console, code: str) -> None:
    """Display code with truncation and expansion option."""
    lines = code.split("\n")
    max_lines = _calculate_max_code_lines(console)

    if len(lines) <= max_lines:
        # Short code - display normally
        syntax = Syntax(
            code,
            "python",
            theme="default",
            line_numbers=True,
            background_color="default",
        )
        code_panel = Panel(
            syntax,
            title="💻 Code Example",
            border_style="cyan",
            padding=(1, 2),
            width=80,
        )
        console.print(code_panel)
    else:
        # Long code - show truncated version first
        _show_truncated_code(console, code, lines, max_lines)


def _show_truncated_code(
    console: Console, full_code: str, lines: list[str], max_lines: int
) -> None:
    """Show truncated code with expansion options."""
    truncated_lines = lines[:max_lines]
    truncated_code = "\n".join(truncated_lines)
    remaining_lines = len(lines) - max_lines

    # Add truncation indicator
    truncated_code += (
        f"\n\n# ... {remaining_lines} more lines - press 'e' to expand"
    )

    syntax = Syntax(
        truncated_code,
        "python",
        theme="default",
        line_numbers=True,
        background_color="default",
    )
    code_panel = Panel(
        syntax,
        title="💻 Code Example (Truncated)",
        border_style="cyan",
        padding=(1, 2),
        width=80,
    )
    console.print(code_panel)

    # Ask user if they want to expand
    choice = Prompt.ask(
        "[dim]Press 'e' to expand full code, or Enter to continue[/dim]",
        choices=["e", ""],
        default="",
        show_choices=False,
    )

    if choice.lower() == "e":
        _show_full_code(console, full_code)


def _show_full_code(console: Console, code: str) -> None:
    """Show full code with collapse option."""
    console.clear()

    syntax = Syntax(
        code,
        "python",
        theme="default",
        line_numbers=True,
        background_color="default",
    )
    code_panel = Panel(
        syntax,
        title="💻 Code Example (Full)",
        border_style="cyan",
        padding=(1, 2),
        width=80,
    )
    console.print(code_panel)

    choice = Prompt.ask(
        "[dim]Press 'c' to collapse, or Enter to continue[/dim]",
        choices=["c", ""],
        default="",
        show_choices=False,
    )

    if choice.lower() == "c":
        console.clear()
        # Note: In practice, we'd need to re-display the question/answer context
        # For now, just continue - the main flow will handle redisplay


def get_user_response(console: Console) -> str:
    """Get user's response to whether they got the answer correct."""
    console.print()
    return Prompt.ask(
        "[yellow]Did you get it right?[/yellow] [dim](y)es/(n)o/(s)ummary/(q)uit[/dim]",
        choices=["y", "n", "s", "q"],
        default="y",
        show_choices=False,
    )


def display_user_feedback(console: Console, response: str) -> None:
    """Display feedback based on user response."""
    if response == "y":
        console.print("[green]Great job! 🎉[/green]")
    elif response == "n":
        console.print("[yellow]Keep practicing! 💪[/yellow]")


def continue_to_next_card(
    console: Console, current: int, total: int, response: str
) -> None:
    """Prompt to continue to next card."""
    if current < total and response not in ["s", "q"]:
        Prompt.ask(
            "\n[dim]Press Enter to continue to the next card[/dim]",
            default="",
        )


def show_session_summary(
    console: Console, session_summary: dict[str, Any]
) -> None:
    """Display session summary."""
    if session_summary["total_attempts"] > 0:
        console.print("\n[bold]Session Summary:[/bold]")
        console.print(f"Cards studied: {session_summary['cards_studied']}")
        console.print(f"Accuracy: {session_summary['accuracy']:.1f}%")
        Prompt.ask("\n[dim]Press Enter to return to menu[/dim]", default="")


def display_statistics_table(
    console: Console, flashcard_set: FlashcardSet, set_stats: FlashcardSetStats
) -> None:
    """Display statistics table for current set."""
    console.clear()

    table = Table(
        title=f"📊 {flashcard_set.title} Statistics",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Total Flashcards", str(len(flashcard_set.cards)))
    table.add_row("Total Attempts", str(set_stats.total_attempts))
    table.add_row("Correct Answers", str(set_stats.correct_answers))

    if set_stats.total_attempts > 0:
        table.add_row("Overall Accuracy", f"{set_stats.accuracy:.1f}%")
    else:
        table.add_row("Overall Accuracy", "No attempts yet")

    # Show most challenging cards
    if set_stats.card_stats:
        table.add_row("", "")  # Empty row for spacing
        table.add_row("Most Challenging Cards", "")

        challenging_cards = get_most_challenging_cards(set_stats)
        for i, (card_key, accuracy, total) in enumerate(challenging_cards):
            table.add_row(
                f"  {i+1}. {card_key}...",
                f"{accuracy:.1f}% ({total} attempts)",
            )

    console.print(table)
    Prompt.ask("\n[dim]Press Enter to return to menu[/dim]", default="")


def display_global_statistics(
    console: Console, set_stats: dict[str, FlashcardSetStats]
) -> None:
    """Display statistics for all flashcard sets."""
    console.clear()

    table = Table(
        title="📊 All Flashcard Sets Statistics",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Flashcard Set", style="cyan")
    table.add_column("Total Cards", style="blue")
    table.add_column("Attempts", style="yellow")
    table.add_column("Accuracy", style="green")

    total_attempts_all = 0
    total_correct_all = 0
    sets_with_data = 0

    for set_name_key, stats in set_stats.items():
        if set_name_key != "legacy_data" and not set_name_key.startswith(
            "tmp"
        ):
            display_name = get_set_display_name(set_name_key)
            set_attempts = stats.total_attempts
            set_correct = stats.correct_answers
            total_attempts_all += set_attempts
            total_correct_all += set_correct

            # Try to get card count for this set
            try:
                card_count = get_set_card_count(set_name_key)
                card_count_str = str(card_count) if card_count > 0 else "?"
            except Exception:
                card_count_str = "?"

            if set_attempts > 0:
                set_accuracy = stats.accuracy
                table.add_row(
                    display_name,
                    card_count_str,
                    str(set_attempts),
                    f"{set_accuracy:.1f}%",
                )
                sets_with_data += 1
            elif card_count_str != "?":
                table.add_row(
                    display_name, card_count_str, "0", "No attempts yet"
                )

    # Add overall summary if we have data from multiple sets
    if sets_with_data > 1 and total_attempts_all > 0:
        overall_accuracy = (total_correct_all / total_attempts_all) * 100
        table.add_row(
            "[bold]Overall Summary",
            "-",
            f"[bold]{total_attempts_all}",
            f"[bold]{overall_accuracy:.1f}%",
        )

    if total_attempts_all == 0:
        console.print(
            "[yellow]No statistics available yet. Start studying some "
            "flashcards![/yellow]"
        )
    else:
        console.print(table)

    Prompt.ask("\n[dim]Press Enter to return to menu[/dim]", default="")


def display_flashcard_set_menu(
    console: Console, flashcard_sets: list[tuple[str, str]]
) -> str:
    """Display menu to select flashcard set and return file path."""
    console.clear()
    title = Text("🎓 Choose Your Flashcard Set", style="bold blue")
    console.print(Align.center(title))
    console.print()

    if not flashcard_sets:
        console.print(
            "[red]No flashcard sets found in flashcard_sets directory![/red]"
        )
        console.print(
            "[yellow]Please add some .yaml or .json files to the "
            "flashcard_sets directory.[/yellow]"
        )
        sys.exit(1)

    # Display available sets
    choices = []
    for i, (display_name, file_path) in enumerate(flashcard_sets, 1):
        choices.append(str(i))

        # Try to get card count
        try:
            set_name = (
                file_path.replace(".yaml", "")
                .replace(".yml", "")
                .replace(".json", "")
            )
            card_count = get_set_card_count(set_name)
            card_display = f"({card_count} cards)"
            console.print(f"  {i}. {display_name} ([dim]{card_display}[/dim])")
        except Exception:
            console.print(f"  {i}. {display_name} ([dim]? cards[/dim])")

    choices.append("q")
    console.print("  q. Quit")
    console.print()

    choice = Prompt.ask(
        "[yellow]Select a flashcard set[/yellow]",
        choices=choices,
        default="1" if flashcard_sets else "q",
    )

    if choice == "q":
        sys.exit(0)

    selected_index = int(choice) - 1
    return flashcard_sets[selected_index][1]


def display_flashcard_set_menu_with_stats(
    console: Console, flashcard_sets: list[tuple[str, str]]
) -> str:
    """Display menu to select flashcard set with statistics option."""
    console.clear()
    title = Text("🎓 Choose Your Flashcard Set", style="bold blue")
    console.print(Align.center(title))
    console.print()

    if not flashcard_sets:
        console.print(
            "[red]No flashcard sets found in flashcard_sets directory![/red]"
        )
        console.print(
            "[yellow]Please add some .yaml or .json files to the "
            "flashcard_sets directory.[/yellow]"
        )
        sys.exit(1)

    # Display available sets
    choices = []
    for i, (display_name, file_path) in enumerate(flashcard_sets, 1):
        choices.append(str(i))

        # Try to get card count
        try:
            set_name = (
                file_path.replace(".yaml", "")
                .replace(".yml", "")
                .replace(".json", "")
            )
            card_count = get_set_card_count(set_name)
            card_display = f"({card_count} cards)"
            console.print(f"  {i}. {display_name} ([dim]{card_display}[/dim])")
        except Exception:
            console.print(f"  {i}. {display_name} ([dim]? cards[/dim])")

    choices.extend(["s", "q"])
    console.print("  s. View statistics for all sets")
    console.print("  q. Quit")
    console.print()

    choice = Prompt.ask(
        "[yellow]Select a flashcard set[/yellow]",
        choices=choices,
        default="1" if flashcard_sets else "q",
    )

    if choice == "q":
        return "quit"
    elif choice == "s":
        return "stats"
    else:
        selected_index = int(choice) - 1
        return flashcard_sets[selected_index][1]


def display_exit_message(console: Console) -> None:
    """Display exit message."""
    console.print("[green]Thanks for studying! Keep coding! 👨‍💻[/green]")
