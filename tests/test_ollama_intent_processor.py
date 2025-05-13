import sys
import os
import pytest
import json
from unittest.mock import MagicMock, patch

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import module to test
from ollama_intent_processor import OllamaIntentProcessor

class TestOllamaIntentProcessor:
    """Tests for the OllamaIntentProcessor class"""
    
    @patch('requests.get')
    def test_init_and_model_selection(self, mock_get):
        """Test initialization and model selection"""
        # Mock the Ollama API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "llama3", "size": 1000000, "modified_at": 1000, "details": {}},
                {"name": "mistral", "size": 2000000, "modified_at": 2000, "details": {}}
            ]
        }
        mock_get.return_value = mock_response
        
        # Create instance with default config
        processor = OllamaIntentProcessor()
        
        # Check initialization
        assert processor.model == "llama3"  # Should use llama3 as it's first in preference list
        assert processor.endpoint == "http://localhost:11434/api/generate"
        assert 'click' in processor.supported_intents
        assert 'type' in processor.supported_intents
        
        # Test with custom config
        mock_config = MagicMock()
        mock_config.get.return_value = {"model": "mistral"}
        processor = OllamaIntentProcessor(config=mock_config)
        assert processor.model == "mistral"
    
    @patch('requests.post')
    def test_process_text(self, mock_post):
        """Test text processing"""
        # Mock the Ollama API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": '{"intent": "click", "parameters": {"target": "submit button"}}'
        }
        mock_post.return_value = mock_response
        
        # Create instance
        processor = OllamaIntentProcessor()
        
        # Test processing text
        intent, params = processor.process_text("Click on the submit button")
        
        # Check results
        assert intent == "click"
        assert params == "submit button"  # Should extract just the value for simplicity
        
        # Verify API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args[1]['json']
        assert call_args['model'] == "llama3"
        assert "Click on the submit button" in call_args['prompt']
    
    @patch('requests.post')
    def test_process_text_unknown_intent(self, mock_post):
        """Test processing text with unknown intent"""
        # Mock the Ollama API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": '{"intent": "unknown", "parameters": {}}'
        }
        mock_post.return_value = mock_response
        
        # Create instance
        processor = OllamaIntentProcessor()
        
        # Test processing text
        intent, params = processor.process_text("Do something I don't understand")
        
        # Check results
        assert intent == "unknown"
        assert params == {}
    
    @patch('requests.post')
    def test_process_text_error(self, mock_post):
        """Test processing text with API error"""
        # Mock the Ollama API error
        mock_post.side_effect = Exception("API Error")
        
        # Create instance
        processor = OllamaIntentProcessor()
        
        # Test processing text
        intent, params = processor.process_text("Click on the submit button")
        
        # Check results (should default to unknown)
        assert intent == "unknown"
        assert params is None
    
    @patch('requests.post')
    def test_generate_response(self, mock_post):
        """Test response generation"""
        # Mock the Ollama API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "I'll click on that button for you right away!"
        }
        mock_post.return_value = mock_response
        
        # Create instance
        processor = OllamaIntentProcessor()
        
        # Test generating response
        response = processor.generate_response("click", "submit button")
        
        # Check results
        assert response == "I'll click on that button for you right away!"
        
        # Verify API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args[1]['json']
        assert call_args['model'] == "llama3"
        assert "Intent: click" in call_args['prompt']
        assert "Parameters: submit button" in call_args['prompt']
    
    @patch('requests.post')
    def test_generate_response_error(self, mock_post):
        """Test response generation with API error"""
        # Mock the Ollama API error
        mock_post.side_effect = Exception("API Error")
        
        # Create instance
        processor = OllamaIntentProcessor()
        
        # Test generating response
        response = processor.generate_response("click", "submit button")
        
        # Check results (should default to fallback)
        assert response == "I'll click for you now."
        
        # Test unknown intent fallback
        response = processor.generate_response("unknown", None)
        assert "I'm not sure what you want me to do" in response
    
    @patch('requests.post')
    def test_llm_rules(self, mock_post):
        """Test LLM rules integration"""
        # Mock the Ollama API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "Yes, I am here."
        }
        mock_post.return_value = mock_response
        
        # Create instance with config
        config = {
            "llm_rules": {
                "response_rules": [
                    {
                        "rule": "initial_greeting",
                        "response": "Yes, I am here."
                    }
                ]
            }
        }
        processor = OllamaIntentProcessor(config=config)
        
        # Test initial greeting
        response = processor.generate_response("greeting", None)
        assert response == "Yes, I am here."
    
    @patch('requests.get')
    def test_server_connection(self, mock_get):
        """Test Ollama server connection monitoring"""
        # Mock successful connection
        mock_get.return_value.status_code = 200
        processor = OllamaIntentProcessor()
        assert processor.check_server() is True
        
        # Mock failed connection
        mock_get.side_effect = Exception("Connection failed")
        assert processor.check_server() is False