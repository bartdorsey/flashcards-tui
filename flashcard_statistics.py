#!/usr/bin/env python3
"""
Pure functions for statistics calculations.
"""

from typing import Dict, List, Tuple
from flashcard_types import FlashCard, FlashcardSetStats, CardStats


def update_card_stats(card_stats: CardStats, is_correct: bool) -> CardStats:
    """Update card statistics with new attempt."""
    return CardStats(
        correct=card_stats.correct + (1 if is_correct else 0),
        total=card_stats.total + 1
    )


def update_set_stats(set_stats: FlashcardSetStats, card: FlashCard, is_correct: bool) -> FlashcardSetStats:
    """Update set statistics with new attempt."""
    # Use first 50 chars of question as card key
    card_key = card.question[:50]
    
    # Update or create card stats
    current_card_stats = set_stats.card_stats.get(card_key, CardStats())
    new_card_stats = update_card_stats(current_card_stats, is_correct)
    
    # Create new card_stats dict with updated values
    new_card_stats_dict = dict(set_stats.card_stats)
    new_card_stats_dict[card_key] = new_card_stats
    
    return FlashcardSetStats(
        correct_answers=set_stats.correct_answers + (1 if is_correct else 0),
        total_attempts=set_stats.total_attempts + 1,
        card_stats=new_card_stats_dict
    )


def get_most_challenging_cards(set_stats: FlashcardSetStats, limit: int = 3) -> List[Tuple[str, float, int]]:
    """Get the most challenging cards based on accuracy."""
    card_difficulties = []
    
    for card_key, stats in set_stats.card_stats.items():
        if stats.total > 0:
            accuracy = stats.accuracy
            card_difficulties.append((card_key, accuracy, stats.total))
    
    # Sort by accuracy (ascending) and return top N most challenging
    card_difficulties.sort(key=lambda x: x[1])
    return card_difficulties[:limit]


def calculate_overall_accuracy(set_stats: Dict[str, FlashcardSetStats]) -> Tuple[float, int]:
    """Calculate overall accuracy across all sets."""
    total_attempts = 0
    total_correct = 0
    
    for set_name, stats in set_stats.items():
        if set_name != "legacy_data" and not set_name.startswith("tmp"):
            total_attempts += stats.total_attempts
            total_correct += stats.correct_answers
    
    accuracy = (total_correct / total_attempts * 100) if total_attempts > 0 else 0.0
    return accuracy, total_attempts


def get_sets_with_attempts(set_stats: Dict[str, FlashcardSetStats]) -> List[Tuple[str, FlashcardSetStats]]:
    """Get sets that have at least one attempt."""
    return [
        (set_name, stats)
        for set_name, stats in set_stats.items()
        if (set_name != "legacy_data" and 
            not set_name.startswith("tmp") and 
            stats.total_attempts > 0)
    ]


def calculate_session_summary(cards_studied: int, set_stats: FlashcardSetStats) -> Dict[str, object]:
    """Calculate session summary statistics."""
    return {
        "cards_studied": cards_studied,
        "accuracy": set_stats.accuracy,
        "total_attempts": set_stats.total_attempts,
        "correct_answers": set_stats.correct_answers
    }