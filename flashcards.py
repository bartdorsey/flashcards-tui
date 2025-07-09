#!/usr/bin/env python3
import argparse
import json
import os
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
        self.set_stats: dict[str, dict[str, any]] = {}  # Stats organized by flashcard set
        self.current_set_name: str = ""  # Name of current flashcard set
        self.load_statistics()

    def load_flashcards(self) -> None:
        try:
            with open(self.file_path, "r") as f:
                if self.file_path.endswith(('.yaml', '.yml')):
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)
                
                # Extract set name from file path
                self.current_set_name = os.path.basename(self.file_path).replace('.yaml', '').replace('.yml', '').replace('.json', '')
                
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
                
                # Check if this is the old format (needs migration)
                if "correct_answers" in stats and "flashcard_sets" not in stats:
                    # Migrate old format to new per-set format
                    self.set_stats = {
                        "legacy_data": {
                            "correct_answers": stats.get("correct_answers", 0),
                            "total_attempts": stats.get("total_attempts", 0),
                            "card_stats": stats.get("card_stats", {})
                        }
                    }
                else:
                    # Load new format
                    self.set_stats = stats.get("flashcard_sets", {})
                    
        except FileNotFoundError:
            # First time running, stats file doesn't exist yet
            self.set_stats = {}
        except json.JSONDecodeError:
            # Corrupted stats file, reset to defaults
            self.set_stats = {}
    
    def get_current_set_stats(self) -> dict:
        """Get statistics for the current flashcard set."""
        if self.current_set_name not in self.set_stats:
            self.set_stats[self.current_set_name] = {
                "correct_answers": 0,
                "total_attempts": 0,
                "card_stats": {}
            }
        return self.set_stats[self.current_set_name]

    def save_statistics(self) -> None:
        stats = {
            "flashcard_sets": self.set_stats
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
        # Get current set stats
        current_stats = self.get_current_set_stats()
        current_stats["total_attempts"] += 1

        # Track per-card statistics
        card_key = card.question[:50]  # Use first 50 chars as key
        if card_key not in current_stats["card_stats"]:
            current_stats["card_stats"][card_key] = {"correct": 0, "total": 0}
        
        current_stats["card_stats"][card_key]["total"] += 1

        if response == "y":
            current_stats["correct_answers"] += 1
            current_stats["card_stats"][card_key]["correct"] += 1
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
        current_stats = self.get_current_set_stats()
        if current_stats["total_attempts"] > 0:
            accuracy = (current_stats["correct_answers"] / current_stats["total_attempts"]) * 100
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

        # Show statistics for the current set
        current_stats = self.get_current_set_stats()
        set_name = self.current_set_name.replace('_', ' ').title()
        
        table = Table(
            title=f"📊 {set_name} Statistics",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total Flashcards", str(len(self.flashcards)))
        table.add_row("Total Attempts", str(current_stats["total_attempts"]))
        table.add_row("Correct Answers", str(current_stats["correct_answers"]))

        if current_stats["total_attempts"] > 0:
            accuracy = (current_stats["correct_answers"] / current_stats["total_attempts"]) * 100
            table.add_row("Overall Accuracy", f"{accuracy:.1f}%")
        else:
            table.add_row("Overall Accuracy", "No attempts yet")

        # Show most challenging cards for this set
        if current_stats["card_stats"]:
            table.add_row("", "")  # Empty row for spacing
            table.add_row("Most Challenging Cards", "")
            
            # Calculate accuracy for each card and sort by difficulty
            card_difficulties = []
            for card_key, stats in current_stats["card_stats"].items():
                if stats["total"] > 0:
                    accuracy = (stats["correct"] / stats["total"]) * 100
                    card_difficulties.append((card_key, accuracy, stats["total"]))
            
            # Sort by accuracy (ascending) and show top 3 most challenging
            card_difficulties.sort(key=lambda x: x[1])
            for i, (card_key, accuracy, total) in enumerate(card_difficulties[:3]):
                table.add_row(f"  {i+1}. {card_key}...", f"{accuracy:.1f}% ({total} attempts)")

        # Show overall statistics across all sets
        if len(self.set_stats) > 1:
            table.add_row("", "")  # Empty row for spacing
            table.add_row("[bold]All Flashcard Sets", "")
            
            total_attempts_all = 0
            total_correct_all = 0
            
            for set_name_key, stats in self.set_stats.items():
                if set_name_key != "legacy_data":  # Skip legacy data in display
                    display_name = set_name_key.replace('_', ' ').title()
                    set_attempts = stats.get("total_attempts", 0)
                    set_correct = stats.get("correct_answers", 0)
                    total_attempts_all += set_attempts
                    total_correct_all += set_correct
                    
                    if set_attempts > 0:
                        set_accuracy = (set_correct / set_attempts) * 100
                        table.add_row(f"  {display_name}", f"{set_accuracy:.1f}% ({set_attempts} attempts)")
                    else:
                        table.add_row(f"  {display_name}", "No attempts yet")
            
            if total_attempts_all > 0:
                overall_accuracy = (total_correct_all / total_attempts_all) * 100
                table.add_row("  [bold]Overall Accuracy", f"[bold]{overall_accuracy:.1f}% ({total_attempts_all} total)")

        self.console.print(table)
        Prompt.ask("\n[dim]Press Enter to return to menu[/dim]", default="")

    def discover_flashcard_sets(self, directory: str = "flashcard_sets") -> list[tuple[str, str]]:
        """Discover all flashcard files in the specified directory.
        
        Returns:
            List of tuples (display_name, file_path) for each flashcard set found
        """
        flashcard_sets = []
        
        if not os.path.exists(directory):
            return flashcard_sets
        
        for filename in os.listdir(directory):
            if filename.endswith(('.yaml', '.yml', '.json')) and not filename.startswith('.'):
                file_path = os.path.join(directory, filename)
                
                # Create a display name from filename
                display_name = filename.replace('.yaml', '').replace('.yml', '').replace('.json', '')
                display_name = display_name.replace('_', ' ').title()
                
                flashcard_sets.append((display_name, file_path))
        
        # Sort by display name
        flashcard_sets.sort(key=lambda x: x[0])
        return flashcard_sets

    def display_flashcard_set_menu(self, flashcard_sets: list[tuple[str, str]]) -> str:
        """Display menu to select flashcard set and return chosen file path."""
        self.console.clear()
        title = Text("🎓 Choose Your Flashcard Set", style="bold blue")
        self.console.print(Align.center(title))
        self.console.print()
        
        if not flashcard_sets:
            self.console.print("[red]No flashcard sets found in flashcard_sets directory![/red]")
            self.console.print("[yellow]Please add some .yaml or .json files to the flashcard_sets directory.[/yellow]")
            sys.exit(1)
        
        # Display available sets
        choices = []
        for i, (display_name, file_path) in enumerate(flashcard_sets, 1):
            choices.append(str(i))
            
            # Try to get card count
            try:
                with open(file_path, 'r') as f:
                    if file_path.endswith(('.yaml', '.yml')):
                        data = yaml.safe_load(f)
                    else:
                        data = json.load(f)
                    card_count = len(data.get('flashcards', []))
                    self.console.print(f"  {i}. {display_name} ([dim]{card_count} cards[/dim])")
            except Exception:
                self.console.print(f"  {i}. {display_name} ([dim]? cards[/dim])")
        
        choices.append("q")
        self.console.print("  q. Quit")
        self.console.print()
        
        choice = Prompt.ask(
            "[yellow]Select a flashcard set[/yellow]",
            choices=choices,
            default="1" if flashcard_sets else "q"
        )
        
        if choice == "q":
            sys.exit(0)
        
        selected_index = int(choice) - 1
        return flashcard_sets[selected_index][1]

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


def main():
    parser = argparse.ArgumentParser(
        description="Interactive flashcard application for studying Python concepts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python flashcards.py                                    # Show flashcard set selection menu
  python flashcards.py flashcard_sets/math_flashcards.yaml  # Use specific flashcard set directly
  python flashcards.py flashcard_sets/science_flashcards.json  # Use science flashcards (JSON)
  python flashcards.py --help                             # Show this help message
        """
    )
    parser.add_argument(
        "file",
        nargs="?",
        default=None,
        help="Path to the flashcard file (YAML or JSON format). If not specified, shows set selection menu."
    )
    parser.add_argument(
        "--stats",
        default="flashcard_stats.json",
        help="Path to the statistics file (default: flashcard_stats.json)"
    )
    
    args = parser.parse_args()
    
    # If no file specified, show set selection menu
    if args.file is None:
        # Create a temporary app just for set selection (no file loading)
        temp_app = FlashcardApp(file_path="dummy.yaml", stats_file=args.stats)
        flashcard_sets = temp_app.discover_flashcard_sets()
        selected_file = temp_app.display_flashcard_set_menu(flashcard_sets)
        
        # Create the actual app with selected file
        app = FlashcardApp(file_path=selected_file, stats_file=args.stats)
        app.run()
    else:
        # Validate file exists
        if not os.path.exists(args.file):
            print(f"Error: Flashcard file '{args.file}' not found.")
            print("Please make sure the file exists or use --help for usage information.")
            sys.exit(1)
        
        app = FlashcardApp(file_path=args.file, stats_file=args.stats)
        app.run()


if __name__ == "__main__":
    main()
