# Flashcard Sets

This directory contains various flashcard collections for different programming languages and topics.

## Available Flashcard Sets

### 🐍 Python Programming (`python_flashcards.yaml`)
- **Cards:** 7 flashcards
- **Topics:** List comprehensions, decorators, GIL, context managers, generators, args/kwargs
- **Format:** YAML
- **Usage:** `python flashcards.py flashcard_sets/python_flashcards.yaml`

### 🌟 JavaScript Programming (`javascript_flashcards.yaml`)
- **Cards:** 8 flashcards
- **Topics:** Variable declarations, closures, equality operators, event bubbling, functions, this keyword, promises, destructuring
- **Format:** YAML
- **Usage:** `python flashcards.py flashcard_sets/javascript_flashcards.yaml`

## Creating New Flashcard Sets

You can create new flashcard sets by adding YAML or JSON files to this directory.

### YAML Format Example:
```yaml
flashcards:
  - question: "Your question here"
    answer: "Your answer here"
    code_example: |
      # Optional code example
      print("Hello, World!")
```

### JSON Format Example:
```json
{
  "flashcards": [
    {
      "question": "Your question here",
      "answer": "Your answer here", 
      "code_example": "print('Hello, World!')"
    }
  ]
}
```

## Statistics

Each flashcard set maintains separate statistics in the main directory:
- Default stats: `flashcard_stats.json`
- Custom stats: Use `--stats custom_stats.json` option