#!/usr/bin/env python3
"""
Pure functions for UI rendering.
"""

import os
import sys
from typing import Any
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text
from rich.table import Table
from rich.syntax import Syntax
from rich.live import Live
from rich import box

from src.core.types import FlashCard, FlashcardSet, FlashcardSetStats
from src.io.operations import get_set_display_name, get_set_card_count
from src.core.statistics import get_most_challenging_cards


def display_menu(
    console: Console, set_title: str, clear_screen: bool = True
) -> str:
    """Display the main menu and return user choice."""
    options = [
        ("📚 Study all flashcards", "1"),
        ("🎲 Study random flashcards", "2"),
        ("👁️ Browse all flashcards", "b"),
        ("📊 View statistics", "s"),
        ("🔄 Reset statistics", "r"),
        ("🚪 Exit", "q"),
    ]

    return _show_arrow_key_menu(
        console,
        f"🎓 {set_title}",
        options,
        default_index=0,
        clear_screen=clear_screen,
    )


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
        _display_code_with_expansion(console, card)


def _calculate_max_code_lines(console: Console) -> int:
    """Calculate maximum code lines based on terminal height."""
    terminal_height = console.size.height

    # Reserve space for UI elements:
    # - Question panel: ~6 lines (title, borders, padding, content)
    # - Answer panel: ~6 lines (title, borders, padding, content)
    # - Progress display: ~2 lines
    # - Arrow key menu: ~6 lines (title + 4 options + spacing)
    # - Code panel borders/title: ~4 lines
    # - Other spacing and prompts: ~4 lines
    # - Breathing room: ~3 lines
    reserved_lines = 31

    available_lines = terminal_height - reserved_lines

    # Set reasonable bounds: minimum 6 lines, maximum 30 lines
    return max(6, min(available_lines, 30))


def _display_code_with_expansion(console: Console, card: FlashCard) -> None:
    """Display code with truncation and expansion option."""
    code = card.code_example
    if code is None:
        return
    lines = code.split("\n")
    max_lines = _calculate_max_code_lines(console)

    if len(lines) <= max_lines:
        # Short code - display normally
        syntax = Syntax(
            code,
            "python",
            theme="catppuccin-mocha",
            line_numbers=True,
            background_color="#1e1e2e",
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
        _show_truncated_code(console, card, lines, max_lines)


def _show_truncated_code(
    console: Console, card: FlashCard, lines: list[str], max_lines: int
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
        theme="catppuccin-mocha",
        line_numbers=True,
        background_color="#1e1e2e",
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
    console.print(
        "[dim]Press 'e' to expand full code, or any other key to continue[/dim]"
    )
    key = _get_arrow_key_input()

    if key.lower() == "e":
        _show_full_code(console, card)


def _show_full_code(console: Console, card: FlashCard) -> None:
    """Show full code with collapse option."""
    console.clear()

    syntax = Syntax(
        card.code_example or "",
        "python",
        theme="catppuccin-mocha",
        line_numbers=True,
        background_color="#1e1e2e",
    )
    code_panel = Panel(
        syntax,
        title="💻 Code Example (Full)",
        border_style="cyan",
        padding=(1, 2),
        width=80,
    )
    console.print(code_panel)

    console.print(
        "[dim]Press 'c' to collapse, or any other key to continue[/dim]"
    )
    key = _get_arrow_key_input()

    if key.lower() == "c":
        # Redraw the original flashcard screen with collapsed code
        _redraw_flashcard_with_collapsed_code(console, card)


def _redraw_flashcard_with_collapsed_code(
    console: Console, card: FlashCard
) -> None:
    """Redraw the flashcard screen with question, answer, and collapsed code."""
    console.clear()

    # Redraw question
    display_question(console, card)

    # Redraw answer
    display_answer(console, card)

    # Redraw code example in collapsed form
    if card.code_example:
        console.print()
        _display_code_with_expansion(console, card)


def _create_menu_display(
    title: str, options: list[tuple[str, str]], selected_index: int
) -> Text:
    """Create a generic menu display with highlighted selection."""
    menu_text = Text()
    menu_text.append(f"{title}\n\n", style="yellow bold")

    for i, (label, _) in enumerate(options):
        if i == selected_index:
            # Highlighted option
            menu_text.append(f"❯ {label}", style="bold green")
        else:
            # Normal option
            menu_text.append(f"  {label}", style="dim")

        if i < len(options) - 1:
            menu_text.append("\n")

    return menu_text


def _create_scrollable_menu_display(
    title: str,
    visible_options: list[tuple[str, str]],
    selected_index: int,
    scroll_offset: int,
    total_items: int,
    max_visible: int,
    search_query: str = "",
    search_mode: bool = False,
) -> Text:
    """Create menu display with scroll indicators for long lists."""
    menu_text = Text()
    menu_text.append(f"{title}\n\n", style="yellow bold")

    # Add search bar if in search mode or has query
    if search_mode or search_query:
        search_display = f"🔍 Search: {search_query}"
        if search_mode:
            search_display += "█"  # cursor indicator
        menu_text.append(f"{search_display}\n\n", style="cyan")

    # Add scroll indicator at top
    if scroll_offset > 0:
        menu_text.append("   ▲ (more items above)\n", style="dim blue")

    # Add visible menu items
    for i, (label, _) in enumerate(visible_options):
        if i == selected_index:
            menu_text.append(f"❯ {label}", style="bold green")
        else:
            menu_text.append(f"  {label}", style="dim")

        if i < len(visible_options) - 1:
            menu_text.append("\n")

    # Add scroll indicator at bottom
    if scroll_offset + len(visible_options) < total_items:
        menu_text.append("\n   ▼ (more items below)", style="dim blue")

    # Add status info
    if search_query and not search_mode:
        filtered_count = (
            len(visible_options)
            if scroll_offset == 0
            and scroll_offset + len(visible_options) >= total_items
            else total_items
        )
        menu_text.append(
            f"\n\nFound {filtered_count} matches | Press ESC to clear search",
            style="dim",
        )
    elif total_items > max_visible:
        current_range_start = scroll_offset + 1
        current_range_end = scroll_offset + len(visible_options)
        menu_text.append(
            f"\n\nShowing {current_range_start}-{current_range_end} of {total_items} items | Use ↑↓ to scroll",
            style="dim",
        )

    # Add search instructions if not in search mode
    if not search_mode and not search_query:
        menu_text.append(
            "\n\nPress / to search | Use ↑↓ arrows to navigate", style="dim"
        )

    return menu_text


def _get_arrow_key_input() -> str:
    """Get keyboard input and return the key pressed."""
    try:
        import termios
        import tty

        # Save current terminal settings
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)

        try:
            # Set terminal to raw mode
            tty.setraw(fd)

            # Read first character
            ch = sys.stdin.read(1)

            # Handle escape sequences (arrow keys)
            if ch == "\x1b":  # ESC
                ch2 = sys.stdin.read(1)
                if ch2 == "[":
                    ch3 = sys.stdin.read(1)
                    if ch3 == "A":
                        return "up"
                    elif ch3 == "B":
                        return "down"
                    elif ch3 == "C":
                        return "right"
                    elif ch3 == "D":
                        return "left"
                else:
                    # Single ESC key
                    return "escape"
            elif ch == "\r" or ch == "\n":  # Enter
                return "enter"
            elif ch == "\x03":  # Ctrl+C
                return "quit"
            elif ch == "\x7f":  # Backspace/Delete
                return "backspace"
            elif ch == "/":
                return "search"
            else:
                return ch.lower()

        finally:
            # Restore terminal settings
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    except (ImportError, OSError):
        # Fallback for systems without termios (Windows, etc.)
        return input().lower() or "enter"

    return ""


def display_flashcard_browser(
    console: Console, flashcard_set: FlashcardSet
) -> None:
    """Browse all flashcards with arrow key navigation and content search."""
    if not flashcard_set.cards:
        console.clear()
        console.print("[red]No flashcards available![/red]")
        Prompt.ask("\n[dim]Press Enter to return to menu[/dim]", default="")
        return

    options = [("🔙 Back to menu", "back")]

    for i, card in enumerate(flashcard_set.cards):
        # Truncate question for menu display (accounting for numbering)
        question_preview = (
            card.question[:55] + "..."
            if len(card.question) > 55
            else card.question
        )
        # Remove newlines and normalize whitespace for menu display
        question_preview = " ".join(question_preview.split())
        options.append((f"{i+1:2d}. {question_preview}", str(i)))

    while True:
        choice = _show_flashcard_searchable_menu(
            console,
            f"📖 Browse: {flashcard_set.title} ({len(flashcard_set.cards)} cards)",
            options,
            flashcard_set.cards,
            default_index=0,
            allow_direct_keys=False,
        )

        if choice == "back":
            break

        # Display selected flashcard
        card_index = int(choice)
        _display_single_flashcard(
            console,
            flashcard_set.cards[card_index],
            card_index + 1,
            len(flashcard_set.cards),
        )


def _display_single_flashcard(
    console: Console, card: FlashCard, card_num: int, total: int
) -> None:
    """Display a single flashcard for browsing."""
    console.clear()

    # Show progress
    display_progress(console, card_num, total)

    # Show question
    display_question(console, card)

    # Show answer
    display_answer(console, card)

    # Show code example if it exists
    if card.code_example:
        display_code_example(console, card)

    Prompt.ask("\n[dim]Press Enter to return to list[/dim]", default="")


def _show_arrow_key_menu(
    console: Console,
    title: str,
    options: list[tuple[str, str]],
    default_index: int = 0,
    allow_direct_keys: bool = True,
    clear_screen: bool = True,
) -> str:
    """Generic arrow key menu function."""
    if clear_screen:
        console.clear()
    selected_index = default_index

    try:
        with Live(console=console, auto_refresh=False) as live:
            while True:
                # Update display
                menu_display = _create_menu_display(
                    title, options, selected_index
                )
                live.update(menu_display)
                live.refresh()

                # Get user input
                key = _get_arrow_key_input()

                if key == "up":
                    selected_index = (selected_index - 1) % len(options)
                elif key == "down":
                    selected_index = (selected_index + 1) % len(options)
                elif key == "enter":
                    return options[selected_index][1]
                elif allow_direct_keys:
                    # Check if key matches any option value
                    for _, value in options:
                        if value == key:
                            return value
                elif key == "quit":
                    # Return appropriate quit value based on options
                    for _, value in options:
                        if value in ["q", "quit"]:
                            return value
                    return "quit"

    except KeyboardInterrupt:
        # Return appropriate quit value
        for _, value in options:
            if value in ["q", "quit"]:
                return value
        return "quit"


def _filter_options(
    options: list[tuple[str, str]], query: str
) -> list[tuple[str, str]]:
    """Filter options based on search query."""
    if not query:
        return options

    query_lower = query.lower()
    filtered = []

    for label, value in options:
        # Search in the label text (case-insensitive)
        if query_lower in label.lower():
            filtered.append((label, value))

    return filtered


def _filter_flashcard_options(
    options: list[tuple[str, str]], flashcards: list[FlashCard], query: str
) -> list[tuple[str, str]]:
    """Filter flashcard options based on search query through full card content."""
    if not query:
        return options

    query_lower = query.lower()
    filtered = []

    for i, (label, value) in enumerate(options):
        # Skip the "Back to menu" option - always include it
        if value == "back":
            filtered.append((label, value))
            continue

        # For flashcard options, search through the actual flashcard content
        if value.isdigit():
            card_index = int(value)
            if 0 <= card_index < len(flashcards):
                card = flashcards[card_index]

                # Search in question, answer, and code example
                searchable_text = f"{card.question} {card.answer}"
                if card.code_example:
                    searchable_text += f" {card.code_example}"

                if query_lower in searchable_text.lower():
                    filtered.append((label, value))
        else:
            # Fallback to label search for non-flashcard options
            if query_lower in label.lower():
                filtered.append((label, value))

    return filtered


def _show_scrollable_arrow_key_menu(
    console: Console,
    title: str,
    options: list[tuple[str, str]],
    default_index: int = 0,
    allow_direct_keys: bool = True,
    clear_screen: bool = True,
) -> str:
    """Enhanced arrow key menu with scrolling and search for long lists."""
    if clear_screen:
        console.clear()

    selected_index = default_index
    scroll_offset = 0
    search_query = ""
    search_mode = False
    filtered_options = options

    # Calculate available height for menu items
    terminal_height = console.size.height
    reserved_lines = (
        10  # title, spacing, instructions, scroll indicators, search bar
    )
    max_visible_items = max(5, terminal_height - reserved_lines)

    try:
        with Live(console=console, auto_refresh=False) as live:
            while True:
                # Apply search filter
                filtered_options = _filter_options(options, search_query)

                # Reset selection if out of bounds after filtering
                if (
                    selected_index >= len(filtered_options)
                    and len(filtered_options) > 0
                ):
                    selected_index = 0
                    scroll_offset = 0
                elif len(filtered_options) == 0:
                    selected_index = 0
                    scroll_offset = 0

                # Calculate viewport window
                if len(filtered_options) <= max_visible_items:
                    # All items fit, show everything
                    visible_options = filtered_options
                    visible_selected = (
                        selected_index if len(filtered_options) > 0 else 0
                    )
                    scroll_offset = 0
                else:
                    # Need scrolling - adjust viewport
                    if selected_index < scroll_offset:
                        scroll_offset = selected_index
                    elif selected_index >= scroll_offset + max_visible_items:
                        scroll_offset = selected_index - max_visible_items + 1

                    visible_options = filtered_options[
                        scroll_offset : scroll_offset + max_visible_items
                    ]
                    visible_selected = selected_index - scroll_offset

                # Create display with scroll indicators and search
                menu_display = _create_scrollable_menu_display(
                    title,
                    visible_options,
                    visible_selected,
                    scroll_offset,
                    len(filtered_options),
                    max_visible_items,
                    search_query,
                    search_mode,
                )
                live.update(menu_display)
                live.refresh()

                # Handle input
                key = _get_arrow_key_input()

                if search_mode:
                    # Handle search input
                    if key == "enter" or key == "escape":
                        search_mode = False
                    elif key == "backspace":
                        search_query = search_query[:-1]
                    elif len(key) == 1 and key.isprintable() and key != "/":
                        search_query += key
                elif key == "search":  # "/" key
                    search_mode = True
                elif key == "escape" and search_query:
                    # Clear search
                    search_query = ""
                    search_mode = False
                    selected_index = 0
                    scroll_offset = 0
                elif key == "up" and len(filtered_options) > 0:
                    selected_index = (selected_index - 1) % len(
                        filtered_options
                    )
                elif key == "down" and len(filtered_options) > 0:
                    selected_index = (selected_index + 1) % len(
                        filtered_options
                    )
                elif key == "enter" and len(filtered_options) > 0:
                    return filtered_options[selected_index][1]
                elif allow_direct_keys and not search_mode:
                    # Check if key matches any option value
                    for _, value in filtered_options:
                        if value == key:
                            return value
                elif key == "quit":
                    # Return appropriate quit value based on options
                    for _, value in options:
                        if value in ["q", "quit"]:
                            return value
                    return "quit"

    except KeyboardInterrupt:
        # Return appropriate quit value
        for _, value in options:
            if value in ["q", "quit"]:
                return value
        return "quit"


def _show_flashcard_searchable_menu(
    console: Console,
    title: str,
    options: list[tuple[str, str]],
    flashcards: list[FlashCard],
    default_index: int = 0,
    allow_direct_keys: bool = True,
    clear_screen: bool = True,
) -> str:
    """Enhanced arrow key menu with scrolling and full-content search for flashcards."""
    if clear_screen:
        console.clear()

    selected_index = default_index
    scroll_offset = 0
    search_query = ""
    search_mode = False
    filtered_options = options

    # Calculate available height for menu items
    terminal_height = console.size.height
    reserved_lines = (
        10  # title, spacing, instructions, scroll indicators, search bar
    )
    max_visible_items = max(5, terminal_height - reserved_lines)

    try:
        with Live(console=console, auto_refresh=False) as live:
            while True:
                # Apply search filter using flashcard content
                filtered_options = _filter_flashcard_options(
                    options, flashcards, search_query
                )

                # Reset selection if out of bounds after filtering
                if (
                    selected_index >= len(filtered_options)
                    and len(filtered_options) > 0
                ):
                    selected_index = 0
                    scroll_offset = 0
                elif len(filtered_options) == 0:
                    selected_index = 0
                    scroll_offset = 0

                # Calculate viewport window
                if len(filtered_options) <= max_visible_items:
                    # All items fit, show everything
                    visible_options = filtered_options
                    visible_selected = (
                        selected_index if len(filtered_options) > 0 else 0
                    )
                    scroll_offset = 0
                else:
                    # Need scrolling - adjust viewport
                    if selected_index < scroll_offset:
                        scroll_offset = selected_index
                    elif selected_index >= scroll_offset + max_visible_items:
                        scroll_offset = selected_index - max_visible_items + 1

                    visible_options = filtered_options[
                        scroll_offset : scroll_offset + max_visible_items
                    ]
                    visible_selected = selected_index - scroll_offset

                # Create display with scroll indicators and search
                menu_display = _create_scrollable_menu_display(
                    title,
                    visible_options,
                    visible_selected,
                    scroll_offset,
                    len(filtered_options),
                    max_visible_items,
                    search_query,
                    search_mode,
                )
                live.update(menu_display)
                live.refresh()

                # Handle input
                key = _get_arrow_key_input()

                if search_mode:
                    # Handle search input
                    if key == "enter" or key == "escape":
                        search_mode = False
                    elif key == "backspace":
                        search_query = search_query[:-1]
                    elif len(key) == 1 and key.isprintable() and key != "/":
                        search_query += key
                elif key == "search":  # "/" key
                    search_mode = True
                elif key == "escape" and search_query:
                    # Clear search
                    search_query = ""
                    search_mode = False
                    selected_index = 0
                    scroll_offset = 0
                elif key == "up" and len(filtered_options) > 0:
                    selected_index = (selected_index - 1) % len(
                        filtered_options
                    )
                elif key == "down" and len(filtered_options) > 0:
                    selected_index = (selected_index + 1) % len(
                        filtered_options
                    )
                elif key == "enter" and len(filtered_options) > 0:
                    return filtered_options[selected_index][1]
                elif allow_direct_keys and not search_mode:
                    # Check if key matches any option value
                    for _, value in filtered_options:
                        if value == key:
                            return value
                elif key == "quit":
                    # Return appropriate quit value based on options
                    for _, value in options:
                        if value in ["q", "quit"]:
                            return value
                    return "quit"

    except KeyboardInterrupt:
        # Return appropriate quit value
        for _, value in options:
            if value in ["q", "quit"]:
                return value
        return "quit"


def get_user_response(console: Console) -> str:
    """Get user's response using arrow key menu."""
    console.print()  # Add spacing before menu

    options = [
        ("✅ Yes, I got it right", "y"),
        ("❌ No, I got it wrong", "n"),
        ("📊 Show session summary", "s"),
        ("🚪 Quit to menu", "q"),
    ]

    return _show_arrow_key_menu(
        console,
        "Did you get it right?",
        options,
        default_index=0,
        clear_screen=False,
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
        console.clear()
        console.print("[bold]Session Summary:[/bold]")
        console.print(f"Cards studied: {session_summary['cards_studied']}")
        console.print(f"Accuracy: {session_summary['accuracy']:.1f}%")
        console.print()  # Add spacing before menu


def display_statistics_table(
    console: Console, flashcard_set: FlashcardSet, set_stats: FlashcardSetStats
) -> None:
    """Display statistics table for current set."""
    console.clear()

    table = Table(
        title=f"📊 {flashcard_set.title} Statistics",
        show_header=True,
        header_style="bold magenta",
        box=box.MINIMAL,
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
        box=box.MINIMAL,
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


def display_flashcard_set_menu_with_stats(
    console: Console, flashcard_sets: list[tuple[str, str]]
) -> str:
    """Display menu to select flashcard set with statistics option."""
    if not flashcard_sets:
        console.clear()
        console.print(
            "[red]No flashcard sets found in flashcard_sets directory![/red]"
        )
        console.print(
            "[yellow]Please add some .yaml or .json files to the "
            "flashcard_sets directory.[/yellow]"
        )
        sys.exit(1)

    # Build options list with flashcard sets
    options = []

    for display_name, file_path in flashcard_sets:
        # Try to get card count
        try:
            # Extract just the filename without directory path
            filename = os.path.basename(file_path)
            set_name = (
                filename.replace(".yaml", "")
                .replace(".yml", "")
                .replace(".json", "")
            )
            card_count = get_set_card_count(set_name)
            card_display = f"({card_count} cards)"
            option_label = f"📚 {display_name} {card_display}"
        except Exception:
            option_label = f"📚 {display_name} (? cards)"

        options.append((option_label, file_path))

    # Add additional options
    options.extend(
        [("📊 View statistics for all sets", "stats"), ("🚪 Quit", "quit")]
    )

    choice = _show_arrow_key_menu(
        console,
        "🎓 Choose Your Flashcard Set",
        options,
        default_index=0,
        allow_direct_keys=False,  # Don't allow number keys since they're dynamic
    )

    return choice


def confirm_reset_stats(console: Console, set_title: str) -> bool:
    """Confirm reset statistics action."""
    console.print()
    console.print(
        f"[yellow]⚠️  Are you sure you want to reset all statistics for '{set_title}'?[/yellow]"
    )
    console.print("[dim]This action cannot be undone.[/dim]")
    console.print()

    options = [
        ("❌ No, keep my stats", "n"),
        ("✅ Yes, reset stats", "y"),
    ]

    choice = _show_arrow_key_menu(
        console, "Confirm Reset", options, default_index=0, clear_screen=False
    )

    return choice == "y"


def display_exit_message(console: Console) -> None:
    """Display exit message."""
    console.print("[green]Thanks for studying! Keep coding! 👨‍💻[/green]")
