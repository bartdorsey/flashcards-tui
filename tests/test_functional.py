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
from src.core.session import prepare_cards, create_study_session, advance_session


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
        ):  # dataclass(frozen=True) raises FrozenInstanceError or AttributeError
            card.question = "Changed"

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


if __name__ == "__main__":
    pytest.main([__file__])
