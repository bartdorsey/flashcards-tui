#!/usr/bin/env python3
"""
Pure functions for study session logic.
"""

import random
from rich.console import Console

from src.core.types import (
    FlashCard,
    FlashcardSet,
    FlashcardSetStats,
    StudySession,
)
from src.core.statistics import update_set_stats, calculate_session_summary
from src.ui.interface import (
    display_progress,
    display_question,
    wait_for_user_thinking,
    display_answer,
    display_code_example,
    get_user_response,
    display_user_feedback,
    continue_to_next_card,
    show_session_summary,
    display_statistics_table,
    display_exit_message,
    confirm_reset_stats,
    display_flashcard_browser,
)


def prepare_cards(
    flashcard_set: FlashcardSet, randomize: bool
) -> list[FlashCard]:
    """Prepare cards for study session."""
    cards = flashcard_set.cards.copy()
    if randomize:
        random.shuffle(cards)
    return cards


def create_study_session(
    flashcard_set: FlashcardSet, randomize: bool = False
) -> StudySession:
    """Create a new study session."""
    cards = prepare_cards(flashcard_set, randomize)
    return StudySession(
        cards=cards, current_index=0, correct_count=0, randomized=randomize
    )


def advance_session(session: StudySession, is_correct: bool) -> StudySession:
    """Advance the study session to the next card."""
    return StudySession(
        cards=session.cards,
        current_index=session.current_index + 1,
        correct_count=session.correct_count + (1 if is_correct else 0),
        randomized=session.randomized,
    )


def run_study_session(
    console: Console,
    flashcard_set: FlashcardSet,
    set_stats: FlashcardSetStats,
    randomize: bool = False,
) -> tuple[FlashcardSetStats, int]:
    """Run a complete study session and return updated stats
    and cards studied."""
    if not flashcard_set.cards:
        console.print("[red]No flashcards available![/red]")
        return set_stats, 0

    session = create_study_session(flashcard_set, randomize)
    current_stats = set_stats
    cards_studied = 0

    while not session.is_complete:
        console.clear()

        current, total = session.progress
        display_progress(console, current, total)

        card = session.current_card
        if card is None:
            break

        display_question(console, card)
        wait_for_user_thinking(console)
        display_answer(console, card)
        display_code_example(console, card)

        response = get_user_response(console)

        # Handle quit and skip
        if response == "q":
            break
        elif response == "s":
            cards_studied = current
            break

        # Process response
        is_correct = response == "y"
        display_user_feedback(console, response)

        # Update statistics
        current_stats = update_set_stats(current_stats, card, is_correct)

        # Advance session
        session = advance_session(session, is_correct)
        cards_studied = current

        continue_to_next_card(console, current, total, response)

    # Show session summary
    session_summary = calculate_session_summary(cards_studied, current_stats)
    show_session_summary(console, session_summary)

    return current_stats, cards_studied


def handle_menu_choice(
    console: Console,
    choice: str,
    flashcard_set: FlashcardSet,
    set_stats: FlashcardSetStats,
) -> tuple[FlashcardSetStats | str | None, bool]:
    """Handle menu choice and return updated stats if applicable.

    Returns:
        tuple: (stats_or_result, session_just_completed)
    """
    if choice == "1":
        new_stats, _ = run_study_session(
            console, flashcard_set, set_stats, randomize=False
        )
        return new_stats, True
    elif choice == "2":
        new_stats, _ = run_study_session(
            console, flashcard_set, set_stats, randomize=True
        )
        return new_stats, True
    elif choice == "b":
        display_flashcard_browser(console, flashcard_set)
        return None, False
    elif choice == "s":
        display_statistics_table(console, flashcard_set, set_stats)
        return None, False
    elif choice == "r":
        if confirm_reset_stats(console, flashcard_set.title):
            console.print("[green]✅ Statistics reset successfully![/green]")
            from rich.prompt import Prompt

            Prompt.ask("\n[dim]Press Enter to continue[/dim]", default="")
            # Return a new empty stats object
            return FlashcardSetStats(), False
        else:
            console.print("[dim]Reset cancelled.[/dim]")
            return None, False
    elif choice == "q":
        display_exit_message(console)
        return "exit", False

    return None, False
