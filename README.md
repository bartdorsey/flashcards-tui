# 🎓 Flashcard Study App

An interactive command-line flashcard application built with Python and Rich for studying programming concepts, with support for custom flashcard sets and progress tracking.

## Features

- 📚 Multiple flashcard sets with custom titles and emojis
- 🎯 Study modes: sequential or randomized
- 📊 Comprehensive statistics tracking per set and globally
- 💻 Syntax-highlighted code examples
- 🎨 Beautiful Rich-based terminal UI with 80-character width panels
- 📝 Support for YAML flashcard format
- 🔄 Automatic flashcard set discovery

## Installation

1. **Clone or download** this repository
2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Quick Start

Run the application without arguments to see all available flashcard sets:

```bash
python main.py
```

This will show a menu where you can:

- Select a flashcard set by number
- Press `s` to view statistics for all sets
- Press `q` to quit

### Study a Specific Set

You can also run a specific flashcard set directly:

```bash
python main.py flashcard_sets/python_basic_flashcards.yaml
python main.py flashcard_sets/git_basics_flashcards.yaml
```

### Study Modes

Once you select a flashcard set, you can choose:

- **Study all flashcards** - Go through cards in order
- **Study random flashcards** - Randomized order
- **View statistics** - See your progress on this set
- **Exit** - Return to main menu

### During Study

- Read the question and think about the answer
- Press **Enter** to reveal the answer
- Indicate if you got it right: `y` (yes) or `n` (no)
- Press `s` to skip to session summary
- Press `q` to quit back to menu

## Available Flashcard Sets

The application comes with several pre-made flashcard sets:

- **🐍 Python Basics** - Fundamental Python concepts
- **🚀 Python Advanced** - Advanced Python topics
- **⭐ JavaScript Basics** - Essential JavaScript concepts
- **🔥 JavaScript Advanced** - Complex JavaScript topics
- **🗄️ PostgreSQL Basics** - SQL and database fundamentals
- **🔧 Git Basics** - Version control with Git
- **📚 Programming Terminology** - General programming concepts

## Creating Custom Flashcard Sets

### File Format

Create YAML files in the `flashcard_sets/` directory:

```yaml
title: "My Custom Set"
icon: "🎯"
flashcards:
  - question: "What is your question?"
    answer: "This is the answer explanation."
    code_example: |
      # Optional code example
      print("Hello, World!")

  - question: "Another question?"
    answer: "Another answer."
    # code_example is optional
```

### File Naming

- Place files in `flashcard_sets/` directory
- Use `.yaml` or `.yml` extensions
- Files are automatically discovered and displayed in the menu

### Custom Titles and Icons

- Add a `title` field with descriptive text for your flashcard set
- Add an optional `icon` field with an emoji to display alongside the title
- If no title is provided, the filename will be used (formatted)
- Icons help visually distinguish different subject areas

### Schema Validation

A YAML schema is provided in `flashcard_schema.yaml` that defines the structure and validation rules for flashcard files. You can use tools like `yamllint` to check your flashcard files against this schema.

## Statistics

The app tracks detailed statistics including:

- **Per-set statistics**: Accuracy, total attempts, challenging cards
- **Global statistics**: Performance across all flashcard sets
- **Card-level tracking**: Individual question performance
- **Progress over time**: Cumulative learning metrics

Statistics are automatically saved to `flashcard_stats.json`.

## Command Line Options

```bash
# Show flashcard set selection menu
python main.py

# Study specific flashcard set
python main.py path/to/flashcards.yaml

# Use custom statistics file
python main.py --stats my_stats.json

# Show help
python main.py --help
```

## Examples

```bash
# Interactive mode - choose from available sets
python main.py

# Study Python basics directly
python main.py flashcard_sets/python_basic_flashcards.yaml

# Study Git with custom stats file
python main.py flashcard_sets/git_basics_flashcards.yaml --stats git_progress.json
```

## Requirements

- Python 3.7+
- Dependencies listed in `requirements.txt`:
  - `rich` - Beautiful terminal UI
  - `PyYAML` - YAML file support
  - `pytest` - Testing framework

## Testing

Run the test suite:

```bash
python -m pytest test_flashcards.py -v
```

## Tips for Effective Study

1. **Regular practice** - Study a little bit each day
2. **Mixed practice** - Rotate between different flashcard sets
3. **Focus on mistakes** - Pay attention to cards you get wrong
4. **Use statistics** - Review your progress and identify weak areas
5. **Create custom sets** - Add your own flashcards for specific topics

---

Happy studying! 🚀
