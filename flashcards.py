#!/usr/bin/env python3
import json
import random
import sys
from dataclasses import dataclass
from typing import Optional
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text
from rich.table import Table
from rich.align import Align
from rich.syntax import Syntax


@dataclass
class FlashCard:
    question: str
    answer: str
    code_example: Optional[str] = None


class FlashcardApp:
    def __init__(self, file_path: str = "flashcards.yaml", stats_file: str = "flashcard_stats.json") -> None:
        self.console: Console = Console()
        self.file_path: str = file_path
        self.stats_file: str = stats_file
        self.flashcards: list[FlashCard] = []
        self.correct_answers: int = 0
        self.total_attempts: int = 0
        self.card_stats: dict[str, dict[str, int]] = {}  # Track per-card performance
        self.load_statistics()

    def load_flashcards(self) -> None:
        try:
            with open(self.file_path, "r") as f:
                if self.file_path.endswith(('.yaml', '.yml')):
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)
                
                self.flashcards = [
                    FlashCard(
                        question=card["question"],
                        answer=card["answer"],
                        code_example=card.get("code_example")
                    )
                    for card in data["flashcards"]
                ]
                self.console.print(
                    (
                        f"[green]Loaded {len(self.flashcards)} flashcards "
                        "successfully![/green]"
                    )
                )
        except FileNotFoundError:
            self.console.print(
                f"[red]Error: Could not find {self.file_path}[/red]"
            )
            sys.exit(1)
        except (json.JSONDecodeError, yaml.YAMLError) as e:
            self.console.print(
                f"[red]Error: Invalid format in {self.file_path}: {e}[/red]"
            )
            sys.exit(1)

    def load_statistics(self) -> None:
        try:
            with open(self.stats_file, "r") as f:
                stats = json.load(f)
                self.correct_answers = stats.get("correct_answers", 0)
                self.total_attempts = stats.get("total_attempts", 0)
                self.card_stats = stats.get("card_stats", {})
        except FileNotFoundError:
            # First time running, stats file doesn't exist yet
            self.correct_answers = 0
            self.total_attempts = 0
            self.card_stats = {}
        except json.JSONDecodeError:
            # Corrupted stats file, reset to defaults
            self.correct_answers = 0
            self.total_attempts = 0
            self.card_stats = {}

    def save_statistics(self) -> None:
        stats = {
            "correct_answers": self.correct_answers,
            "total_attempts": self.total_attempts,
            "card_stats": self.card_stats
        }
        try:
            with open(self.stats_file, "w") as f:
                json.dump(stats, f, indent=2)
        except Exception as e:
            # Don't crash if we can't save stats, just warn
            self.console.print(f"[yellow]Warning: Could not save statistics: {e}[/yellow]")

    def display_menu(self) -> None:
        self.console.clear()
        title = Text("🎓 Python Flashcards", style="bold blue")
        self.console.print(Align.center(title))
        self.console.print()

        menu_options = [
            "1. Study all flashcards",
            "2. Study random flashcards",
            "3. View statistics",
            "4. Exit",
        ]

        for option in menu_options:
            self.console.print(f"  {option}")

        self.console.print()

    def _prepare_cards(self, randomize: bool) -> list[FlashCard]:
        cards_to_study = self.flashcards.copy()
        if randomize:
            random.shuffle(cards_to_study)
        return cards_to_study

    def _display_progress(self, current: int, total: int) -> None:
        progress = f"Card {current}/{total}"
        self.console.print(f"[dim]{progress}[/dim]")
        self.console.print()

    def _display_question(self, card: FlashCard) -> None:
        question_panel = Panel(
            card.question,
            title="❓ Question",
            border_style="blue",
            padding=(1, 2),
        )
        self.console.print(question_panel)

    def _wait_for_user_thinking(self) -> None:
        Prompt.ask(
            (
                "\n[yellow]Think about it, then press Enter to reveal the "
                "answer[/yellow]"
            ),
            default="",
        )

    def _display_answer(self, card: FlashCard) -> None:
        answer_panel = Panel(
            card.answer,
            title="✅ Answer",
            border_style="green",
            padding=(1, 2),
        )
        self.console.print(answer_panel)

    def _display_code_example(self, card: FlashCard) -> None:
        if card.code_example:
            self.console.print()
            syntax = Syntax(
                card.code_example,
                "python",
                theme="monokai",
                line_numbers=True,
                background_color="default",
            )
            code_panel = Panel(
                syntax,
                title="💻 Code Example",
                border_style="cyan",
                padding=(1, 2),
            )
            self.console.print(code_panel)

    def _get_user_response(self) -> str:
        self.console.print()
        return Prompt.ask(
            "[yellow]Did you get it right?[/yellow]",
            choices=["y", "n", "s", "q"],
            default="y",
        )

    def _handle_user_response(self, response: str, card: FlashCard) -> None:
        self.total_attempts += 1

        # Track per-card statistics
        card_key = card.question[:50]  # Use first 50 chars as key
        if card_key not in self.card_stats:
            self.card_stats[card_key] = {"correct": 0, "total": 0}
        
        self.card_stats[card_key]["total"] += 1

        if response == "y":
            self.correct_answers += 1
            self.card_stats[card_key]["correct"] += 1
            self.console.print("[green]Great job! 🎉[/green]")
        elif response == "n":
            self.console.print("[yellow]Keep practicing! 💪[/yellow]")
        
        # Save statistics after each attempt
        self.save_statistics()

    def _continue_to_next_card(
        self, current: int, total: int, response: str
    ) -> None:
        if current < total and response not in ["s", "q"]:
            Prompt.ask(
                "\n[dim]Press Enter to continue to the next card[/dim]",
                default="",
            )

    def _show_session_summary(self, cards_studied: int) -> None:
        if self.total_attempts > 0:
            accuracy = (self.correct_answers / self.total_attempts) * 100
            self.console.print("\n[bold]Session Summary:[/bold]")
            self.console.print(f"Cards studied: {cards_studied}")
            self.console.print(f"Accuracy: {accuracy:.1f}%")
            Prompt.ask(
                "\n[dim]Press Enter to return to menu[/dim]", default=""
            )

    def study_flashcards(self, randomize: bool = False) -> None:
        if not self.flashcards:
            self.console.print("[red]No flashcards available![/red]")
            return

        cards_to_study = self._prepare_cards(randomize)

        i = 0
        for i, card in enumerate(cards_to_study, 1):
            self.console.clear()

            self._display_progress(i, len(cards_to_study))
            self._display_question(card)
            self._wait_for_user_thinking()
            self._display_answer(card)
            self._display_code_example(card)

            response = self._get_user_response()
            self._handle_user_response(response, card)

            if response in ["s", "q"]:
                if response == "q":
                    return
                break

            self._continue_to_next_card(i, len(cards_to_study), response)

        self._show_session_summary(i)

    def show_statistics(self) -> None:
        self.console.clear()

        table = Table(
            title="📊 Study Statistics",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Total Flashcards", str(len(self.flashcards)))
        table.add_row("Total Attempts", str(self.total_attempts))
        table.add_row("Correct Answers", str(self.correct_answers))

        if self.total_attempts > 0:
            accuracy = (self.correct_answers / self.total_attempts) * 100
            table.add_row("Overall Accuracy", f"{accuracy:.1f}%")
        else:
            table.add_row("Overall Accuracy", "No attempts yet")

        # Show most challenging cards
        if self.card_stats:
            table.add_row("", "")  # Empty row for spacing
            table.add_row("Most Challenging Cards", "")
            
            # Calculate accuracy for each card and sort by difficulty
            card_difficulties = []
            for card_key, stats in self.card_stats.items():
                if stats["total"] > 0:
                    accuracy = (stats["correct"] / stats["total"]) * 100
                    card_difficulties.append((card_key, accuracy, stats["total"]))
            
            # Sort by accuracy (ascending) and show top 3 most challenging
            card_difficulties.sort(key=lambda x: x[1])
            for i, (card_key, accuracy, total) in enumerate(card_difficulties[:3]):
                table.add_row(f"  {i+1}. {card_key}...", f"{accuracy:.1f}% ({total} attempts)")

        self.console.print(table)
        Prompt.ask("\n[dim]Press Enter to return to menu[/dim]", default="")

    def run(self) -> None:
        self.load_flashcards()

        while True:
            self.display_menu()
            choice = Prompt.ask(
                "[yellow]Choose an option[/yellow]",
                choices=["1", "2", "3", "4"],
                default="1",
            )

            if choice == "1":
                self.study_flashcards(randomize=False)
            elif choice == "2":
                self.study_flashcards(randomize=True)
            elif choice == "3":
                self.show_statistics()
            elif choice == "4":
                self.console.print(
                    "[green]Thanks for studying! Keep coding! 👨‍💻[/green]"
                )
                break


if __name__ == "__main__":
    app = FlashcardApp()
    app.run()
