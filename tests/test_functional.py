#!/usr/bin/env python3
"""
Unit tests for the functional flashcard application.
"""

import pytest
import json
import yaml
import tempfile
import os
from unittest.mock import patch

from src.core.types import (
    FlashCard,
    FlashcardSet,
    FlashcardSetStats,
    CardStats,
    StudySession,
)
from src.io.operations import (
    load_flashcard_file,
    load_statistics_file,
    save_statistics_file,
    discover_flashcard_sets,
)
from src.core.statistics import (
    update_card_stats,
    update_set_stats,
    get_most_challenging_cards,
    calculate_overall_accuracy,
    calculate_session_summary,
)
from src.core.session import (
    prepare_cards,
    create_study_session,
    advance_session,
    handle_menu_choice,
)
from src.ui.interface import (
    _create_scrollable_menu_display,
    _filter_options,
    _filter_flashcard_options,
    display_menu,
)
from rich.console import Console
from rich.text import Text


class TestFlashcardTypes:
    """Test the immutable data types."""

    def test_flashcard_creation(self):
        card = FlashCard(
            question="What is Python?",
            answer="A programming language",
            code_example="print('Hello')",
        )
        assert card.question == "What is Python?"
        assert card.answer == "A programming language"
        assert card.code_example == "print('Hello')"

    def test_flashcard_immutable(self):
        card = FlashCard(question="Test", answer="Test")
        with pytest.raises(
            (AttributeError, TypeError)
        ):  # dataclass(frozen=True) raises FrozenInstanceError or
            # AttributeError
            card.question = "Changed"  # type: ignore

    def test_card_stats_accuracy(self):
        stats = CardStats(correct=8, total=10)
        assert stats.accuracy == 80.0

        stats_zero = CardStats(correct=0, total=0)
        assert stats_zero.accuracy == 0.0

    def test_flashcard_set_stats_accuracy(self):
        stats = FlashcardSetStats(correct_answers=15, total_attempts=20)
        assert stats.accuracy == 75.0

        stats_zero = FlashcardSetStats(correct_answers=0, total_attempts=0)
        assert stats_zero.accuracy == 0.0

    def test_study_session_properties(self):
        cards = [
            FlashCard(question="Q1", answer="A1"),
            FlashCard(question="Q2", answer="A2"),
        ]

        session = StudySession(cards=cards, current_index=0)
        assert not session.is_complete
        assert session.current_card == cards[0]
        assert session.progress == (1, 2)

        session_complete = StudySession(cards=cards, current_index=2)
        assert session_complete.is_complete
        assert session_complete.current_card is None
        assert session_complete.progress == (3, 2)


class TestIOOperations:
    """Test file I/O operations."""

    @pytest.fixture
    def sample_flashcard_data(self):
        return {
            "title": "🧪 Test Flashcards",
            "flashcards": [
                {
                    "question": "What is a Python list?",
                    "answer": "A mutable sequence type",
                    "code_example": "my_list = [1, 2, 3]",
                },
                {
                    "question": "What is a Python dictionary?",
                    "answer": "A mutable mapping type",
                    "code_example": "my_dict = {'key': 'value'}",
                },
            ],
        }

    @pytest.fixture
    def temp_yaml_file(self, sample_flashcard_data):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            yaml.dump(sample_flashcard_data, f)
            temp_file = f.name
        yield temp_file
        os.unlink(temp_file)

    def test_load_flashcard_file_yaml(self, temp_yaml_file):
        flashcard_set = load_flashcard_file(temp_yaml_file)

        assert flashcard_set is not None
        assert len(flashcard_set.cards) == 2
        assert flashcard_set.title == "🧪 Test Flashcards"
        assert flashcard_set.cards[0].question == "What is a Python list?"
        assert (
            flashcard_set.cards[1].question == "What is a Python dictionary?"
        )

    def test_load_flashcard_file_not_found(self):
        with patch("rich.console.Console.print") as mock_print:
            result = load_flashcard_file("nonexistent.yaml")
            assert result is None
            mock_print.assert_called_once()

    def test_load_statistics_file_new_format(self):
        stats_data = {
            "flashcard_sets": {
                "test_set": {
                    "correct_answers": 5,
                    "total_attempts": 10,
                    "card_stats": {
                        "What is Python?": {"correct": 3, "total": 5}
                    },
                }
            }
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(stats_data, f)
            temp_file = f.name

        try:
            result = load_statistics_file(temp_file)
            assert "test_set" in result
            assert result["test_set"].correct_answers == 5
            assert result["test_set"].total_attempts == 10
            assert len(result["test_set"].card_stats) == 1
        finally:
            os.unlink(temp_file)

    def test_load_statistics_file_legacy_format(self):
        legacy_stats = {
            "correct_answers": 8,
            "total_attempts": 12,
            "card_stats": {"What is Python?": {"correct": 4, "total": 6}},
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(legacy_stats, f)
            temp_file = f.name

        try:
            result = load_statistics_file(temp_file)
            assert "legacy_data" in result
            assert result["legacy_data"].correct_answers == 8
            assert result["legacy_data"].total_attempts == 12
        finally:
            os.unlink(temp_file)

    def test_save_statistics_file(self):
        stats = {
            "test_set": FlashcardSetStats(
                correct_answers=10,
                total_attempts=15,
                card_stats={"Q1": CardStats(correct=5, total=7)},
            )
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            temp_file = f.name

        try:
            result = save_statistics_file(temp_file, stats)
            assert result is True

            # Verify the file was written correctly
            with open(temp_file, "r") as f:
                saved_data = json.load(f)

            assert "flashcard_sets" in saved_data
            assert "test_set" in saved_data["flashcard_sets"]
            assert (
                saved_data["flashcard_sets"]["test_set"]["correct_answers"]
                == 10
            )
        finally:
            os.unlink(temp_file)

    def test_discover_flashcard_sets(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            yaml_file = os.path.join(temp_dir, "test.yaml")
            with open(yaml_file, "w") as f:
                yaml.dump({"title": "Test YAML", "flashcards": []}, f)

            yml_file = os.path.join(temp_dir, "test2.yml")
            with open(yml_file, "w") as f:
                yaml.dump({"title": "Test YML", "flashcards": []}, f)

            # Create a file to ignore
            with open(os.path.join(temp_dir, ".hidden.yaml"), "w") as f:
                yaml.dump({"flashcards": []}, f)

            result = discover_flashcard_sets(temp_dir)

            # Should find 2 files, sorted by name
            assert len(result) == 2
            display_names = [name for name, _ in result]
            assert "Test YAML" in display_names
            assert "Test YML" in display_names


class TestStatistics:
    """Test statistics functions."""

    def test_update_card_stats(self):
        initial_stats = CardStats(correct=5, total=10)

        # Correct answer
        updated_correct = update_card_stats(initial_stats, True)
        assert updated_correct.correct == 6
        assert updated_correct.total == 11

        # Incorrect answer
        updated_incorrect = update_card_stats(initial_stats, False)
        assert updated_incorrect.correct == 5
        assert updated_incorrect.total == 11

    def test_update_set_stats(self):
        card = FlashCard(
            question="What is Python?", answer="A programming language"
        )
        initial_stats = FlashcardSetStats(correct_answers=3, total_attempts=5)

        # Correct answer
        updated_correct = update_set_stats(initial_stats, card, True)
        assert updated_correct.correct_answers == 4
        assert updated_correct.total_attempts == 6

        # Check card stats were updated
        card_key = card.question[:50]
        assert card_key in updated_correct.card_stats
        assert updated_correct.card_stats[card_key].correct == 1
        assert updated_correct.card_stats[card_key].total == 1

    def test_get_most_challenging_cards(self):
        card_stats = {
            "Easy question": CardStats(correct=9, total=10),  # 90% accuracy
            "Medium question": CardStats(correct=6, total=10),  # 60% accuracy
            "Hard question": CardStats(correct=2, total=10),  # 20% accuracy
            "No attempts": CardStats(correct=0, total=0),  # Should be ignored
        }

        set_stats = FlashcardSetStats(card_stats=card_stats)
        challenging = get_most_challenging_cards(set_stats, limit=2)

        assert len(challenging) == 2
        assert challenging[0][0] == "Hard question"
        assert challenging[0][1] == 20.0
        assert challenging[1][0] == "Medium question"
        assert challenging[1][1] == 60.0

    def test_calculate_overall_accuracy(self):
        set_stats = {
            "set1": FlashcardSetStats(correct_answers=8, total_attempts=10),
            "set2": FlashcardSetStats(correct_answers=15, total_attempts=20),
            "legacy_data": FlashcardSetStats(
                correct_answers=100, total_attempts=200
            ),  # Should be ignored
        }

        accuracy, total = calculate_overall_accuracy(set_stats)
        assert abs(accuracy - 76.67) < 0.01  # (8+15)/(10+20) * 100 = 76.67
        assert total == 30

    def test_calculate_session_summary(self):
        set_stats = FlashcardSetStats(correct_answers=7, total_attempts=10)
        summary = calculate_session_summary(5, set_stats)

        assert summary["cards_studied"] == 5
        assert summary["accuracy"] == 70.0
        assert summary["total_attempts"] == 10
        assert summary["correct_answers"] == 7


class TestStudySession:
    """Test study session logic."""

    def test_prepare_cards(self):
        cards = [
            FlashCard(question="Q1", answer="A1"),
            FlashCard(question="Q2", answer="A2"),
            FlashCard(question="Q3", answer="A3"),
        ]

        flashcard_set = FlashcardSet(
            cards=cards, name="test", title="Test Set", file_path="test.yaml"
        )

        # Test without randomization
        result = prepare_cards(flashcard_set, randomize=False)
        assert result == cards

        # Test with randomization
        with patch("random.shuffle") as mock_shuffle:
            prepare_cards(flashcard_set, randomize=True)
            mock_shuffle.assert_called_once()

    def test_create_study_session(self):
        cards = [
            FlashCard(question="Q1", answer="A1"),
            FlashCard(question="Q2", answer="A2"),
        ]

        flashcard_set = FlashcardSet(
            cards=cards, name="test", title="Test Set", file_path="test.yaml"
        )

        session = create_study_session(flashcard_set, randomize=False)

        assert len(session.cards) == 2
        assert session.current_index == 0
        assert session.correct_count == 0
        assert session.randomized is False

    def test_advance_session(self):
        cards = [
            FlashCard(question="Q1", answer="A1"),
            FlashCard(question="Q2", answer="A2"),
        ]

        session = StudySession(cards=cards, current_index=0, correct_count=0)

        # Advance with correct answer
        advanced_correct = advance_session(session, True)
        assert advanced_correct.current_index == 1
        assert advanced_correct.correct_count == 1

        # Advance with incorrect answer
        advanced_incorrect = advance_session(session, False)
        assert advanced_incorrect.current_index == 1
        assert advanced_incorrect.correct_count == 0

    def test_handle_menu_choice_browse(self):
        """Test handle_menu_choice with browse option."""
        cards = [
            FlashCard(question="Q1", answer="A1"),
            FlashCard(question="Q2", answer="A2"),
        ]
        flashcard_set = FlashcardSet(
            cards=cards,
            name="test_set",
            title="Test Set",
            file_path="test.yaml",
        )
        set_stats = FlashcardSetStats()
        console = Console()

        # Mock the display_flashcard_browser function
        with patch(
            "src.core.session.display_flashcard_browser"
        ) as mock_browser:
            result, session_completed = handle_menu_choice(
                console, "b", flashcard_set, set_stats
            )

            # Should call the browser function
            assert mock_browser.called
            mock_browser.assert_called_once_with(console, flashcard_set)

            # Should return None (no stats update) and False (no session completed)
            assert result is None
            assert session_completed is False

    def test_handle_menu_choice_statistics(self):
        """Test handle_menu_choice with statistics option."""
        cards = [FlashCard(question="Q1", answer="A1")]
        flashcard_set = FlashcardSet(
            cards=cards,
            name="test_set",
            title="Test Set",
            file_path="test.yaml",
        )
        set_stats = FlashcardSetStats()
        console = Console()

        # Mock the display_statistics_table function
        with patch("src.core.session.display_statistics_table") as mock_stats:
            result, session_completed = handle_menu_choice(
                console, "s", flashcard_set, set_stats
            )

            # Should call the statistics function
            assert mock_stats.called
            mock_stats.assert_called_once_with(
                console, flashcard_set, set_stats
            )

            # Should return None and False
            assert result is None
            assert session_completed is False

    def test_handle_menu_choice_exit(self):
        """Test handle_menu_choice with quit option."""
        cards = [FlashCard(question="Q1", answer="A1")]
        flashcard_set = FlashcardSet(
            cards=cards,
            name="test_set",
            title="Test Set",
            file_path="test.yaml",
        )
        set_stats = FlashcardSetStats()
        console = Console()

        # Mock the display_exit_message function
        with patch("src.core.session.display_exit_message") as mock_exit:
            result, session_completed = handle_menu_choice(
                console, "q", flashcard_set, set_stats
            )

            # Should call the exit message function
            assert mock_exit.called
            mock_exit.assert_called_once_with(console)

            # Should return "exit" and False
            assert result == "exit"
            assert session_completed is False


class TestUIInterface:
    """Test the UI interface functions."""

    def test_create_scrollable_menu_display_no_scroll(self):
        """Test scrollable menu display when no scrolling is needed."""
        options = [
            ("Option 1", "1"),
            ("Option 2", "2"),
            ("Option 3", "3"),
        ]

        display = _create_scrollable_menu_display(
            title="Test Menu",
            visible_options=options,
            selected_index=1,
            scroll_offset=0,
            total_items=3,
            max_visible=5,
        )

        display_str = str(display)

        # Should contain title
        assert "Test Menu" in display_str
        # Should contain all options
        assert "Option 1" in display_str
        assert "Option 2" in display_str
        assert "Option 3" in display_str
        # Should show selection indicator on option 2 (index 1)
        assert "❯ Option 2" in display_str
        # Should not show scroll indicators
        assert "▲" not in display_str
        assert "▼" not in display_str
        # Should not show status line
        assert "Showing" not in display_str

    def test_create_scrollable_menu_display_with_scroll_top(self):
        """Test scrollable menu display at top of list."""
        visible_options = [
            ("Option 1", "1"),
            ("Option 2", "2"),
            ("Option 3", "3"),
        ]

        display = _create_scrollable_menu_display(
            title="Test Menu",
            visible_options=visible_options,
            selected_index=0,
            scroll_offset=0,
            total_items=10,
            max_visible=3,
        )

        display_str = str(display)

        # Should not show up arrow at top
        assert "▲" not in display_str
        # Should show down arrow at bottom
        assert "▼" in display_str
        # Should show status line
        assert "Showing 1-3 of 10 items" in display_str

    def test_create_scrollable_menu_display_with_scroll_middle(self):
        """Test scrollable menu display in middle of list."""
        visible_options = [
            ("Option 4", "4"),
            ("Option 5", "5"),
            ("Option 6", "6"),
        ]

        display = _create_scrollable_menu_display(
            title="Test Menu",
            visible_options=visible_options,
            selected_index=1,
            scroll_offset=3,
            total_items=10,
            max_visible=3,
        )

        display_str = str(display)

        # Should show both scroll arrows
        assert "▲" in display_str
        assert "▼" in display_str
        # Should show correct status line
        assert "Showing 4-6 of 10 items" in display_str
        # Should show selection on middle item
        assert "❯ Option 5" in display_str

    def test_create_scrollable_menu_display_with_scroll_bottom(self):
        """Test scrollable menu display at bottom of list."""
        visible_options = [
            ("Option 8", "8"),
            ("Option 9", "9"),
            ("Option 10", "10"),
        ]

        display = _create_scrollable_menu_display(
            title="Test Menu",
            visible_options=visible_options,
            selected_index=2,
            scroll_offset=7,
            total_items=10,
            max_visible=3,
        )

        display_str = str(display)

        # Should show up arrow at top
        assert "▲" in display_str
        # Should not show down arrow at bottom
        assert "▼" not in display_str
        # Should show correct status line
        assert "Showing 8-10 of 10 items" in display_str

    def test_display_menu_includes_browse_option(self):
        """Test that display_menu includes the new browse option."""
        console = Console()

        # Mock the _show_arrow_key_menu function to capture the options
        with patch("src.ui.interface._show_arrow_key_menu") as mock_menu:
            mock_menu.return_value = "b"

            result = display_menu(console, "Test Set")

            # Verify the function was called
            assert mock_menu.called
            call_args = mock_menu.call_args

            # Extract the options from the call
            options = call_args[0][2]  # Third argument is options list

            # Verify browse option is present
            option_labels = [option[0] for option in options]
            option_values = [option[1] for option in options]

            assert "👁️ Browse all flashcards" in option_labels
            assert "b" in option_values
            assert result == "b"

    def test_scrollable_menu_display_text_object(self):
        """Test that scrollable menu display returns a Rich Text object."""
        options = [("Test Option", "test")]

        display = _create_scrollable_menu_display(
            title="Test",
            visible_options=options,
            selected_index=0,
            scroll_offset=0,
            total_items=1,
            max_visible=5,
        )

        # Should return a Rich Text object
        assert isinstance(display, Text)

        # Should be convertible to string
        display_str = str(display)
        assert isinstance(display_str, str)
        assert len(display_str) > 0

    def test_scrollable_menu_display_empty_options(self):
        """Test scrollable menu display with empty options list."""
        display = _create_scrollable_menu_display(
            title="Empty Menu",
            visible_options=[],
            selected_index=0,
            scroll_offset=0,
            total_items=0,
            max_visible=5,
        )

        display_str = str(display)

        # Should still contain title
        assert "Empty Menu" in display_str
        # Should not contain scroll indicators
        assert "▲" not in display_str
        assert "▼" not in display_str

    def test_scrollable_menu_display_special_characters(self):
        """Test scrollable menu display with special characters and emojis."""
        options = [
            ("🔙 Back to menu", "back"),
            ("📚 Study all flashcards", "1"),
            ("🎲 Random study", "2"),
        ]

        display = _create_scrollable_menu_display(
            title="Test Menu with Emojis 🎓",
            visible_options=options,
            selected_index=0,
            scroll_offset=0,
            total_items=3,
            max_visible=5,
        )

        display_str = str(display)

        # Should handle emojis properly
        assert "🔙" in display_str
        assert "📚" in display_str
        assert "🎲" in display_str
        assert "🎓" in display_str
        assert "❯ 🔙 Back to menu" in display_str

    def test_scrollable_menu_display_with_search_mode(self):
        """Test scrollable menu display with search mode enabled."""
        options = [("Test Option", "test")]

        display = _create_scrollable_menu_display(
            title="Test Menu",
            visible_options=options,
            selected_index=0,
            scroll_offset=0,
            total_items=1,
            max_visible=5,
            search_query="test",
            search_mode=True,
        )

        display_str = str(display)

        # Should show search bar with cursor
        assert "🔍 Search: test█" in display_str
        assert "Test Option" in display_str

    def test_scrollable_menu_display_with_search_query(self):
        """Test scrollable menu display with search query but not in search mode."""
        options = [("Test Option", "test")]

        display = _create_scrollable_menu_display(
            title="Test Menu",
            visible_options=options,
            selected_index=0,
            scroll_offset=0,
            total_items=1,
            max_visible=5,
            search_query="test",
            search_mode=False,
        )

        display_str = str(display)

        # Should show search bar without cursor
        assert "🔍 Search: test" in display_str
        assert "🔍 Search: test█" not in display_str
        assert "Found 1 matches" in display_str
        assert "Press ESC to clear search" in display_str

    def test_filter_options_empty_query(self):
        """Test filter options with empty query returns all options."""
        options = [
            ("Option 1", "1"),
            ("Option 2", "2"),
            ("Option 3", "3"),
        ]

        result = _filter_options(options, "")
        assert result == options

    def test_filter_options_case_insensitive(self):
        """Test filter options performs case-insensitive matching."""
        options = [
            ("Python Basics", "1"),
            ("JavaScript Fundamentals", "2"),
            ("Shell Commands", "3"),
            ("PostgreSQL Advanced", "4"),
        ]

        # Test lowercase query
        result = _filter_options(options, "python")
        assert len(result) == 1
        assert result[0] == ("Python Basics", "1")

        # Test uppercase query
        result = _filter_options(options, "JAVASCRIPT")
        assert len(result) == 1
        assert result[0] == ("JavaScript Fundamentals", "2")

        # Test mixed case query
        result = _filter_options(options, "ShElL")
        assert len(result) == 1
        assert result[0] == ("Shell Commands", "3")

    def test_filter_options_partial_matches(self):
        """Test filter options with partial string matches."""
        options = [
            ("Python Basics - Variables", "1"),
            ("Python Advanced - Classes", "2"),
            ("JavaScript - Functions", "3"),
            ("Shell Basics", "4"),
        ]

        # Should match multiple items with "python"
        result = _filter_options(options, "python")
        assert len(result) == 2
        assert ("Python Basics - Variables", "1") in result
        assert ("Python Advanced - Classes", "2") in result

        # Should match single item with "advanced"
        result = _filter_options(options, "advanced")
        assert len(result) == 1
        assert result[0] == ("Python Advanced - Classes", "2")

        # Should match single item with "javascript"
        result = _filter_options(options, "javascript")
        assert len(result) == 1
        assert result[0] == ("JavaScript - Functions", "3")

    def test_filter_options_no_matches(self):
        """Test filter options with query that matches nothing."""
        options = [
            ("Python Basics", "1"),
            ("JavaScript Fundamentals", "2"),
            ("Shell Commands", "3"),
        ]

        result = _filter_options(options, "nonexistent")
        assert len(result) == 0
        assert result == []

    def test_filter_options_with_emojis_and_numbers(self):
        """Test filter options with emojis and numbers in labels."""
        options = [
            ("🔙 Back to menu", "back"),
            ("📚 Study all flashcards", "1"),
            ("1. What is Python?", "q1"),
            ("2. Variables in JavaScript", "q2"),
            ("10. Advanced Shell Commands", "q10"),
        ]

        # Should match by emoji
        result = _filter_options(options, "🔙")
        assert len(result) == 1
        assert result[0] == ("🔙 Back to menu", "back")

        # Should match by number
        result = _filter_options(options, "10")
        assert len(result) == 1
        assert result[0] == ("10. Advanced Shell Commands", "q10")

        # Should match by word
        result = _filter_options(options, "python")
        assert len(result) == 1
        assert result[0] == ("1. What is Python?", "q1")

    def test_filter_flashcard_options_empty_query(self):
        """Test filter flashcard options with empty query returns all options."""
        options = [
            ("🔙 Back to menu", "back"),
            ("1. What is Python?", "0"),
            ("2. Variables in JS", "1"),
        ]
        flashcards = [
            FlashCard(
                question="What is Python?", answer="A programming language"
            ),
            FlashCard(
                question="What are variables?", answer="Storage containers"
            ),
        ]

        result = _filter_flashcard_options(options, flashcards, "")
        assert result == options

    def test_filter_flashcard_options_by_question(self):
        """Test filter flashcard options searches through question content."""
        options = [
            ("🔙 Back to menu", "back"),
            ("1. What is Python?", "0"),
            ("2. What are variables?", "1"),
            ("3. How to use loops?", "2"),
        ]
        flashcards = [
            FlashCard(
                question="What is Python?", answer="A programming language"
            ),
            FlashCard(
                question="What are variables?",
                answer="Storage containers for data",
            ),
            FlashCard(
                question="How to use loops?", answer="Repeat code blocks"
            ),
        ]

        # Search by question content
        result = _filter_flashcard_options(options, flashcards, "python")
        assert len(result) == 2  # Back button + matching card
        assert ("🔙 Back to menu", "back") in result
        assert ("1. What is Python?", "0") in result

    def test_filter_flashcard_options_by_answer(self):
        """Test filter flashcard options searches through answer content."""
        options = [
            ("🔙 Back to menu", "back"),
            ("1. What is Python?", "0"),
            ("2. What are variables?", "1"),
        ]
        flashcards = [
            FlashCard(
                question="What is Python?", answer="A programming language"
            ),
            FlashCard(
                question="What are variables?",
                answer="Storage containers for data",
            ),
        ]

        # Search by answer content
        result = _filter_flashcard_options(options, flashcards, "programming")
        assert len(result) == 2  # Back button + matching card
        assert ("🔙 Back to menu", "back") in result
        assert ("1. What is Python?", "0") in result

    def test_filter_flashcard_options_by_code_example(self):
        """Test filter flashcard options searches through code examples."""
        options = [
            ("🔙 Back to menu", "back"),
            ("1. Variables", "0"),
            ("2. Functions", "1"),
        ]
        flashcards = [
            FlashCard(
                question="How to create variables?",
                answer="Use assignment operator",
                code_example="x = 42\nname = 'Alice'",
            ),
            FlashCard(
                question="How to define functions?",
                answer="Use def keyword",
                code_example="def greet():\n    print('Hello')",
            ),
        ]

        # Search by code content
        result = _filter_flashcard_options(options, flashcards, "alice")
        assert len(result) == 2  # Back button + matching card
        assert ("🔙 Back to menu", "back") in result
        assert ("1. Variables", "0") in result

        # Search by function keyword
        result = _filter_flashcard_options(options, flashcards, "def")
        assert len(result) == 2  # Back button + matching card
        assert ("🔙 Back to menu", "back") in result
        assert ("2. Functions", "1") in result

    def test_filter_flashcard_options_case_insensitive(self):
        """Test filter flashcard options is case-insensitive."""
        options = [
            ("🔙 Back to menu", "back"),
            ("1. Python Basics", "0"),
        ]
        flashcards = [
            FlashCard(
                question="What is Python?", answer="A Programming Language"
            ),
        ]

        # Test various cases
        for query in ["python", "PYTHON", "Python", "PyThOn"]:
            result = _filter_flashcard_options(options, flashcards, query)
            assert len(result) == 2  # Back button + matching card
            assert ("1. Python Basics", "0") in result

    def test_filter_flashcard_options_multiple_matches(self):
        """Test filter flashcard options with multiple matching cards."""
        options = [
            ("🔙 Back to menu", "back"),
            ("1. Python Variables", "0"),
            ("2. Python Functions", "1"),
            ("3. JavaScript Basics", "2"),
        ]
        flashcards = [
            FlashCard(
                question="Python variables?", answer="Storage in Python"
            ),
            FlashCard(
                question="Python functions?", answer="Reusable Python code"
            ),
            FlashCard(
                question="JavaScript basics?",
                answer="Web programming language",
            ),
        ]

        # Should match both Python cards
        result = _filter_flashcard_options(options, flashcards, "python")
        assert len(result) == 3  # Back button + 2 matching cards
        assert ("🔙 Back to menu", "back") in result
        assert ("1. Python Variables", "0") in result
        assert ("2. Python Functions", "1") in result
        assert ("3. JavaScript Basics", "2") not in result

    def test_filter_flashcard_options_no_matches(self):
        """Test filter flashcard options with no matching content."""
        options = [
            ("🔙 Back to menu", "back"),
            ("1. Python Basics", "0"),
            ("2. JavaScript Basics", "1"),
        ]
        flashcards = [
            FlashCard(
                question="What is Python?", answer="Programming language"
            ),
            FlashCard(question="What is JavaScript?", answer="Web language"),
        ]

        # Search for something that doesn't exist
        result = _filter_flashcard_options(options, flashcards, "nonexistent")
        assert len(result) == 1  # Only back button
        assert result[0] == ("🔙 Back to menu", "back")

    def test_filter_flashcard_options_always_includes_back(self):
        """Test filter flashcard options always includes the back button."""
        options = [
            ("🔙 Back to menu", "back"),
            ("1. Test Card", "0"),
        ]
        flashcards = [
            FlashCard(question="Test question", answer="Test answer"),
        ]

        # Even with no matches, back button should be included
        result = _filter_flashcard_options(options, flashcards, "nomatch")
        assert len(result) == 1
        assert result[0] == ("🔙 Back to menu", "back")


if __name__ == "__main__":
    pytest.main([__file__])
