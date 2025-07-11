# Changelog

All notable changes to the flashcards-tui project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2025-07-11

### Added
- **GitHub CI/CD Pipeline** with automated testing on Python 3.10, 3.11, and 3.12
- **MyPy static type checking** with comprehensive type hint validation
- **Black code formatter** integration for consistent code style
- **Automated quality gates** running Black formatting checks, MyPy type checking, and pytest tests

### Changed  
- **Development dependencies** added mypy and black to requirements.txt
- **Code formatting** applied Black formatter across entire codebase with 79-character line length
- **CI testing matrix** updated to test on Python 3.10+ (was previously >= 3.7)

### Fixed
- **Type hint improvements** throughout codebase for better static analysis
- **Code style consistency** with automated Black formatting

## [0.1.0] - 2025-01-10

### Added

#### Core Application Features
- **Interactive terminal flashcard application** with Rich-based UI and 80-character panel width
- **Functional programming architecture** with immutable data structures using `@dataclass(frozen=True)`
- **Multiple study modes**: Sequential and randomized flashcard ordering
- **YAML-based flashcard format** with automatic discovery in `flashcard_sets/` directory
- **Command-line interface** with support for direct file study or interactive set selection
- **Statistics tracking** with per-set and global performance metrics
- **Custom flashcard sets** with optional titles and emoji icons

#### Advanced UI Features
- **Flashcard Browser** with full navigation through all cards in a set
- **Advanced Search System** with `/` key to search through questions, answers, and code examples
- **Scrollable Menu System** with terminal height-aware viewport calculations
- **Arrow Key Navigation** with live Rich rendering and visual scroll indicators (▲▼)
- **Dual Menu Architecture**: Standard menus and specialized searchable flashcard browser
- **Search Functionality**:
  - Real-time filtering as you type
  - Case-insensitive substring matching
  - Deep content search through all flashcard text
  - Visual feedback with match counts
  - ESC to clear search and return to full list

#### Code Example Features
- **Syntax-highlighted code examples** using Pygments with Catppuccin theme
- **Expandable/collapsible code blocks** with terminal height adaptation
- **Interactive code viewing** with 'e' to expand and 'c' to collapse
- **Automatic code truncation** for long examples with visual indicators

#### Statistics and Progress Tracking
- **Comprehensive statistics system** with JSON persistence
- **Legacy format migration** for backward compatibility
- **Card-level performance tracking** with accuracy calculations
- **Most challenging cards identification** with detailed breakdowns
- **Session summaries** with immediate feedback
- **Statistics reset functionality** with confirmation prompts
- **Global statistics view** across all flashcard sets

#### Pre-built Flashcard Content
- **🐍 Python Basics** (20 cards) - Variables, data types, functions, loops
- **🚀 Python Advanced** (27 cards) - Classes, decorators, context managers
- **⭐ JavaScript Basics** (20 cards) - Fundamentals, hoisting, objects, arrays
- **🔥 JavaScript Advanced** (15 cards) - Closures, promises, async/await
- **🗄️ PostgreSQL Basics** (22 cards) - Database fundamentals and basic SQL
- **🔧 PostgreSQL Advanced** (27 cards) - Complex queries, indexing, optimization
- **💻 Shell Basics** (31 cards) - Unix/Linux commands and terminology
- **📊 Data Structures & Algorithms Basics** (17 cards) - Arrays, lists, Big O
- **🧮 Data Structures & Algorithms Advanced** (15 cards) - Trees, graphs, dynamic programming

#### Developer Experience
- **Comprehensive test suite** with 45 unit tests covering all functionality
- **Type hints throughout codebase** for better development experience
- **Black code formatting** with 79-character line length
- **Modular architecture** with clear separation of concerns
- **Pure functions** for business logic without side effects
- **Rich styling patterns** with proper `Text.append(style=...)` syntax

### Technical Implementation

#### Architecture
- **src/core/types.py**: Immutable data classes (FlashCard, FlashcardSet, StudySession, etc.)
- **src/io/operations.py**: Pure I/O functions for YAML/JSON handling
- **src/core/session.py**: Study session management with immutable state
- **src/core/statistics.py**: Statistics calculations and performance tracking
- **src/ui/interface.py**: Rich-based terminal UI (956 lines, largest module)
- **main.py**: Application orchestration and argument parsing

#### Key Dependencies
- **Rich 14.0.0**: Terminal UI framework with panels and live updates
- **PyYAML 6.0.2**: YAML file parsing for flashcard sets
- **Pytest 8.4.1**: Testing framework with comprehensive coverage
- **Catppuccin theme**: Consistent color scheme throughout
- **Pygments**: Syntax highlighting for code examples

#### Search Implementation
- **Two-tier filtering system**:
  - `_filter_options()`: Basic menu label search
  - `_filter_flashcard_options()`: Deep content search through questions, answers, and code
- **Terminal-adaptive UI**: Dynamic viewport sizing based on terminal height
- **Keyboard handling**: Raw terminal input for arrow keys, search, backspace, escape

### Configuration
- **Version tracking**: Semantic versioning with `src/__version__.py`
- **Flexible statistics storage**: `flashcard_stats.json` with custom file support
- **Schema validation**: Complete YAML schema for flashcard format validation
- **Black formatting**: 79-character line length configured in `pyproject.toml`

### User Experience
- **Intuitive navigation**: Arrow keys throughout with visual feedback
- **Immediate feedback**: Real-time search filtering and progress indicators
- **Accessible design**: Clear instructions and help text
- **Error handling**: Graceful fallbacks and informative error messages
- **Cross-platform**: Works on Unix/Linux systems with termios fallback for Windows

### Performance
- **Viewport optimization**: Only renders visible menu items for large lists
- **Efficient search**: Fast substring matching across all flashcard content
- **Memory management**: Immutable data structures prevent accidental mutations
- **Terminal adaptation**: Responsive UI that adapts to different terminal sizes

---

**Initial Release**: This represents the first beta release of flashcards-tui with core functionality for interactive terminal-based flashcard study with advanced search and navigation capabilities. Ready for testing and feedback.