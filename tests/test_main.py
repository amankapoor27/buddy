import sys
import os
import pytest
from unittest.mock import MagicMock, patch

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import module to test
from main import BuddyApp

class TestBuddyApp:
    """Tests for the BuddyApp class"""
    
    @patch('modules.chat_interface.ChatInterface')
    @patch('modules.input_controller.InputController')
    @patch('ollama_intent_processor.OllamaIntentProcessor')
    def test_init(self, mock_processor, mock_controller, mock_chat):
        """Test initialization"""
        # Create instance
        app = BuddyApp()
        
        # Check initialization
        assert app.intent_processor is not None
        assert app.input_controller is not None
        assert app.chat_interface is not None
        assert app.speech_active is False
    
    @patch('modules.chat_interface.ChatInterface')
    @patch('modules.input_controller.InputController')
    @patch('ollama_intent_processor.OllamaIntentProcessor')
    def test_handle_command(self, mock_processor, mock_controller, mock_chat):
        """Test command handling"""
        # Create instance
        app = BuddyApp()
        
        # Mock the _process_natural_language method
        app._process_natural_language = MagicMock()
        
        # Test regular command
        app.handle_command("open youtube")
        app._process_natural_language.assert_called_once_with("open youtube")
        
        # Test listen command
        app._toggle_speech_recognition = MagicMock()
        app.handle_command("/listen")
        app._toggle_speech_recognition.assert_called_once()
    
    @patch('modules.chat_interface.ChatInterface')
    @patch('modules.input_controller.InputController')
    @patch('ollama_intent_processor.OllamaIntentProcessor')
    def test_process_natural_language(self, mock_processor, mock_controller, mock_chat):
        """Test natural language processing"""
        # Setup mocks
        mock_processor_instance = mock_processor.return_value
        mock_processor_instance.process_text.return_value = ("click", "submit button")
        mock_processor_instance.generate_response.return_value = "I'll click on that button for you!"
        
        mock_chat_instance = mock_chat.return_value
        
        # Create instance
        app = BuddyApp()
        app._execute_action = MagicMock()  # Mock the action execution
        
        # Test processing
        app._process_natural_language("Click on the submit button")
        
        # Verify intent processing
        mock_processor_instance.process_text.assert_called_once_with("Click on the submit button")
        
        # Verify response generation
        mock_processor_instance.generate_response.assert_called_once_with("click", "submit button")
        
        # Verify message display
        mock_chat_instance.display_message.assert_called_once_with("I'll click on that button for you!", "Buddy")
        
        # Verify action execution
        app._execute_action.assert_called_once_with("click", "submit button")