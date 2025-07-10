#!/usr/bin/env python3
"""
Immutable data types for the flashcard application.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict


@dataclass(frozen=True)
class FlashCard:
    """Immutable flashcard data structure."""

    question: str
    answer: str
    code_example: Optional[str] = None


@dataclass(frozen=True)
class CardStats:
    """Immutable card statistics."""

    correct: int = 0
    total: int = 0

    @property
    def accuracy(self) -> float:
        """Calculate accuracy percentage."""
        return (self.correct / self.total * 100) if self.total > 0 else 0.0


@dataclass(frozen=True)
class FlashcardSetStats:
    """Immutable flashcard set statistics."""

    correct_answers: int = 0
    total_attempts: int = 0
    card_stats: Dict[str, CardStats] = field(default_factory=dict)

    @property
    def accuracy(self) -> float:
        """Calculate overall accuracy percentage."""
        return (
            (self.correct_answers / self.total_attempts * 100)
            if self.total_attempts > 0
            else 0.0
        )


@dataclass(frozen=True)
class FlashcardSet:
    """Immutable flashcard set containing cards and metadata."""

    cards: list[FlashCard]
    name: str
    title: str
    file_path: str


@dataclass(frozen=True)
class StudySession:
    """Immutable study session state."""

    cards: list[FlashCard]
    current_index: int = 0
    correct_count: int = 0
    randomized: bool = False

    @property
    def is_complete(self) -> bool:
        """Check if session is complete."""
        return self.current_index >= len(self.cards)

    @property
    def current_card(self) -> Optional[FlashCard]:
        """Get current card if available."""
        if self.is_complete:
            return None
        return self.cards[self.current_index]

    @property
    def progress(self) -> tuple[int, int]:
        """Get current progress as (current, total)."""
        return (self.current_index + 1, len(self.cards))


@dataclass(frozen=True)
class AppState:
    """Immutable application state."""

    flashcard_sets: Dict[str, FlashcardSetStats] = field(default_factory=dict)
    current_set: Optional[FlashcardSet] = None

