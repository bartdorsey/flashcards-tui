#!/usr/bin/env python3
import pytest
import json
import yaml
import tempfile
import os
from unittest.mock import patch, MagicMock
from flashcards import FlashcardApp, FlashCard, FlashcardSetStats, CardStats

class TestFlashcardApp:
    
    @pytest.fixture
    def sample_flashcards_data(self):
        return {
            "flashcards": [
                {
                    "question": "What is a Python list?",
                    "answer": "A mutable sequence type that can hold multiple items",
                    "code_example": "my_list = [1, 2, 3]"
                },
                {
                    "question": "What is a Python dictionary?",
                    "answer": "A mutable mapping type that stores key-value pairs",
                    "code_example": "my_dict = {'key': 'value'}"
                }
            ]
        }
    
    @pytest.fixture
    def temp_json_file(self, sample_flashcards_data):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_flashcards_data, f)
            temp_file = f.name
        yield temp_file
        os.unlink(temp_file)
    
    @pytest.fixture
    def temp_yaml_file(self, sample_flashcards_data):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(sample_flashcards_data, f)
            temp_file = f.name
        yield temp_file
        os.unlink(temp_file)
    
    def test_init_default_values(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as stats_file:
            app = FlashcardApp(stats_file=stats_file.name)
            assert app.file_path == "flashcards.yaml"
            assert app.flashcards == []
            assert app.set_stats == {}
            assert app.console is not None
        os.unlink(stats_file.name)
    
    def test_init_custom_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as stats_file:
            app = FlashcardApp("custom.yaml", stats_file=stats_file.name)
            assert app.file_path == "custom.yaml"
        os.unlink(stats_file.name)
    
    def test_load_flashcards_success(self, temp_json_file):
        app = FlashcardApp(temp_json_file)
        app.load_flashcards()
        assert len(app.flashcards) == 2
        assert app.flashcards[0].question == "What is a Python list?"
        assert app.flashcards[1].question == "What is a Python dictionary?"
    
    def test_load_flashcards_file_not_found(self):
        app = FlashcardApp("nonexistent.yaml")
        with pytest.raises(SystemExit):
            app.load_flashcards()
    
    def test_load_flashcards_invalid_format(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            temp_file = f.name
        
        app = FlashcardApp(temp_file)
        try:
            with pytest.raises(SystemExit):
                app.load_flashcards()
        finally:
            os.unlink(temp_file)
    
    def test_study_flashcards_no_cards(self):
        app = FlashcardApp()
        app.flashcards = []
        with patch.object(app.console, 'print') as mock_print:
            app.study_flashcards()
            mock_print.assert_called_with("[red]No flashcards available![/red]")
    
    @patch('flashcards.Prompt.ask')
    def test_study_flashcards_correct_answer(self, mock_prompt, temp_json_file):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as stats_file:
            app = FlashcardApp(temp_json_file, stats_file=stats_file.name)
            app.load_flashcards()
            
            mock_prompt.side_effect = ["", "y", "", "", "y", "", ""]
            
            with patch.object(app.console, 'clear'), \
                 patch.object(app.console, 'print'):
                app.study_flashcards()
            
            current_stats = app.get_current_set_stats()
            assert current_stats.correct_answers == 2
            assert current_stats.total_attempts == 2
        os.unlink(stats_file.name)
    
    @patch('flashcards.Prompt.ask')
    def test_study_flashcards_incorrect_answer(self, mock_prompt, temp_json_file):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as stats_file:
            app = FlashcardApp(temp_json_file, stats_file=stats_file.name)
            app.load_flashcards()
            
            mock_prompt.side_effect = ["", "n", "", "", "n", "", ""]
            
            with patch.object(app.console, 'clear'), \
                 patch.object(app.console, 'print'):
                app.study_flashcards()
            
            current_stats = app.get_current_set_stats()
            assert current_stats.correct_answers == 0
            assert current_stats.total_attempts == 2
        os.unlink(stats_file.name)
    
    @patch('flashcards.Prompt.ask')
    def test_study_flashcards_skip(self, mock_prompt, temp_json_file):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as stats_file:
            app = FlashcardApp(temp_json_file, stats_file=stats_file.name)
            app.load_flashcards()
            
            mock_prompt.side_effect = ["", "s", ""]
            
            with patch.object(app.console, 'clear'), \
                 patch.object(app.console, 'print'):
                app.study_flashcards()
            
            current_stats = app.get_current_set_stats()
            assert current_stats.total_attempts == 1
        os.unlink(stats_file.name)
    
    @patch('flashcards.random.shuffle')
    def test_study_flashcards_randomize(self, mock_shuffle, temp_json_file):
        app = FlashcardApp(temp_json_file)
        app.load_flashcards()
        
        with patch('flashcards.Prompt.ask', side_effect=["", "q"]), \
             patch.object(app.console, 'clear'), \
             patch.object(app.console, 'print'):
            app.study_flashcards(randomize=True)
        
        mock_shuffle.assert_called_once()
    
    def test_show_statistics_no_attempts(self, temp_json_file):
        app = FlashcardApp(temp_json_file)
        app.load_flashcards()
        
        with patch.object(app.console, 'clear'), \
             patch.object(app.console, 'print') as mock_print, \
             patch('flashcards.Prompt.ask'):
            app.show_statistics()
        
        mock_print.assert_called()
    
    def test_show_statistics_with_attempts(self, temp_json_file):
        app = FlashcardApp(temp_json_file)
        app.load_flashcards()
        current_stats = app.get_current_set_stats()
        current_stats.total_attempts = 5
        current_stats.correct_answers = 3
        
        with patch.object(app.console, 'clear'), \
             patch.object(app.console, 'print') as mock_print, \
             patch('flashcards.Prompt.ask'):
            app.show_statistics()
        
        mock_print.assert_called()
    
    @patch('flashcards.Prompt.ask')
    def test_run_study_all_then_exit(self, mock_prompt, temp_json_file):
        app = FlashcardApp(temp_json_file)
        
        mock_prompt.side_effect = ["1", "", "q", "4"]
        
        with patch.object(app, 'display_menu'), \
             patch.object(app.console, 'clear'), \
             patch.object(app.console, 'print'):
            app.run()
        
        assert len(app.flashcards) == 2
    
    @patch('flashcards.Prompt.ask')
    def test_run_study_random_then_exit(self, mock_prompt, temp_json_file):
        app = FlashcardApp(temp_json_file)
        
        mock_prompt.side_effect = ["2", "", "q", "4"]
        
        with patch.object(app, 'display_menu'), \
             patch.object(app.console, 'clear'), \
             patch.object(app.console, 'print'), \
             patch('flashcards.random.shuffle'):
            app.run()
        
        assert len(app.flashcards) == 2
    
    def test_load_flashcards_yaml_success(self, temp_yaml_file):
        app = FlashcardApp(temp_yaml_file)
        app.load_flashcards()
        assert len(app.flashcards) == 2
        assert app.flashcards[0].question == "What is a Python list?"
        assert app.flashcards[1].question == "What is a Python dictionary?"
        assert isinstance(app.flashcards[0], FlashCard)
        assert isinstance(app.flashcards[1], FlashCard)
    
    @patch('flashcards.Prompt.ask')
    def test_run_show_statistics_then_exit(self, mock_prompt, temp_json_file):
        app = FlashcardApp(temp_json_file)
        
        mock_prompt.side_effect = ["3", "", "4"]
        
        with patch.object(app, 'display_menu'), \
             patch.object(app.console, 'clear'), \
             patch.object(app.console, 'print'):
            app.run()
        
        assert len(app.flashcards) == 2