# Release Notes - flashcards-tui v0.1.0

## 🎉 First Beta Release!

This is the initial beta release of **flashcards-tui**, an interactive terminal-based flashcard study application with advanced search and navigation capabilities. Ready for testing and feedback!

## ✨ Key Features

### 🚀 **Advanced Search & Navigation**
- **Press `/` to search** through all flashcard content (questions, answers, code examples)
- **Arrow key navigation** with smooth scrolling and visual indicators
- **Real-time filtering** as you type with match counts
- **Dual menu system**: Standard menus + specialized flashcard browser

### 📚 **Rich Study Experience**
- **9 pre-built flashcard sets** covering Python, JavaScript, PostgreSQL, Shell, and Data Structures
- **Syntax-highlighted code examples** with expand/collapse functionality
- **Multiple study modes**: Sequential or randomized order
- **Comprehensive statistics** with per-card and global tracking

### 🎨 **Beautiful Terminal UI**
- **Rich-based interface** with consistent 80-character panels
- **Catppuccin color theme** for easy reading
- **Terminal-adaptive design** that works on different screen sizes
- **Smooth animations** and live updates

### 🔧 **Developer-Friendly**
- **Functional programming architecture** with immutable data structures
- **45 comprehensive unit tests** with 100% passing rate
- **Type hints throughout** for better development experience
- **Modular design** with clear separation of concerns

## 🚀 **Getting Started**

### Installation
```bash
# Clone the repository
git clone https://github.com/user/flashcards-tui.git
cd flashcards-tui

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Quick Start
```bash
# Interactive mode - choose from available flashcard sets
python main.py

# Study a specific set directly
python main.py flashcard_sets/python_basic_flashcards.yaml

# View version information
python main.py --version

# Get help
python main.py --help
```

## 📖 **What's Included**

### Pre-built Flashcard Sets
- **🐍 Python Basics** (20 cards) - Variables, functions, data types
- **🚀 Python Advanced** (27 cards) - Classes, decorators, context managers  
- **⭐ JavaScript Basics** (20 cards) - Fundamentals, objects, arrays
- **🔥 JavaScript Advanced** (15 cards) - Closures, promises, async/await
- **🗄️ PostgreSQL Basics** (22 cards) - SQL fundamentals
- **🔧 PostgreSQL Advanced** (27 cards) - Complex queries, optimization
- **💻 Shell Basics** (31 cards) - Unix/Linux commands
- **📊 Data Structures Basics** (17 cards) - Arrays, lists, Big O
- **🧮 Data Structures Advanced** (15 cards) - Trees, graphs, DP

### Study Features
- **Browse Mode**: Navigate through all flashcards with full search
- **Study Modes**: Sequential or randomized card order
- **Statistics**: Track your progress and identify challenging cards
- **Custom Sets**: Create your own YAML flashcard files

## 🔍 **Search Capabilities**

The advanced search system lets you find cards by:
- **Question content**: Search through all question text
- **Answer content**: Find cards by answer keywords  
- **Code examples**: Search through all code snippets
- **Mixed content**: Search across all text simultaneously

Example searches:
- Type `"function"` → Find all cards about functions
- Type `"def"` → Find cards with function definitions in code
- Type `"variable"` → Locate cards about variables regardless of title

## 📊 **Statistics & Progress**

Track your learning with:
- **Per-set accuracy** and attempt counts
- **Individual card performance** with detailed breakdowns
- **Most challenging cards** identification
- **Global statistics** across all flashcard sets
- **Session summaries** with immediate feedback

## 🎯 **Perfect For**

- **Students** learning programming concepts
- **Developers** reviewing technical knowledge
- **Interview preparation** with coding concepts
- **Self-paced learning** with progress tracking
- **Custom study materials** creation

## 🛠 **Technical Highlights**

- **Semantic versioning** starting with v0.1.0 (beta)
- **Comprehensive testing** with pytest
- **Code formatting** with Black (79-char line length)
- **Rich terminal UI** with live updates
- **YAML-based** flashcard format
- **Cross-platform** compatibility (Unix/Linux primary, Windows fallback)

---

**Ready to start studying?** Run `python main.py` and explore the flashcard sets!

For detailed documentation, see [README.md](README.md) and [CLAUDE.md](CLAUDE.md).