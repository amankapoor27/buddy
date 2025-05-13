import sys
import os
import pytest
from unittest.mock import MagicMock, patch

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import module to test
from modules.chat_interface import ChatInterface

class TestChatInterface:
    """Tests for the ChatInterface class"""
    
    @patch('wx.Panel')
    @patch('wx.BoxSizer')
    @patch('wx.TextCtrl')
    @patch('wx.Font')
    @patch('wx.ToggleButton')
    @patch('wx.Button')
    @patch('wx.StaticText')
    @patch('wx.App')
    @patch('wx.Frame')
    @patch('threading.Thread')
    def test_init(self, mock_thread, mock_frame, mock_app, mock_static_text, mock_button,
                 mock_toggle_button, mock_font, mock_text_ctrl, mock_sizer, mock_panel):
        """Test initialization"""
        # Create wx.App instance first
        app = wx.App()
        
        # Create mock callback
        mock_callback = MagicMock()
        
        # Create instance
        chat = ChatInterface(command_callback=mock_callback)
        
        # Check initialization
        assert len(chat.message_history) == 1
        assert chat.message_history[0] == ("Buddy", "Welcome to Buddy! How can I help you today?")
        assert chat.command_callback == mock_callback
        assert mock_thread.called
        assert chat.app is not None
        assert chat.frame is not None

    @patch('wx.Panel')
    @patch('wx.BoxSizer')
    @patch('wx.TextCtrl')
    @patch('wx.Font')
    @patch('wx.ToggleButton')
    @patch('wx.Button')
    @patch('wx.StaticText')
    @patch('wx.App')
    @patch('wx.Frame')
    @patch('threading.Thread')
    def test_process_command(self, mock_thread, mock_frame, mock_app, mock_static_text, mock_button,
                       mock_toggle_button, mock_font, mock_text_ctrl, mock_sizer, mock_panel):
        """Test command processing"""
        # Create mock callback
        mock_callback = MagicMock()
        
        # Create instance with the mock callback
        chat = ChatInterface(command_callback=mock_callback)
        
        # Clear the command queue from initialization
        while not chat.command_queue.empty():
            chat.command_queue.get()
        
        # Process command
        test_command = "/test command"
        chat.process_command(test_command)
        
        # Process the command directly since we're mocking the thread
        chat._process_commands()
        
        # Check callback was called with the correct command
        mock_callback.assert_called_once_with(test_command)
        
        # Check command was added to queue
        assert chat.command_queue.qsize() == 1
        assert chat.command_queue.get() == test_command

    @patch('modules.chat_interface.SpeechHandler')
    @patch('wx.Panel')
    @patch('wx.BoxSizer')
    @patch('wx.TextCtrl')
    @patch('wx.Font')
    @patch('wx.ToggleButton')
    @patch('wx.Button')
    @patch('wx.StaticText')
    @patch('wx.App')
    @patch('wx.Frame')
    def test_voice_toggle(self, mock_frame, mock_app, mock_static_text, mock_button,
                         mock_toggle_button, mock_font, mock_text_ctrl, mock_sizer, mock_panel,
                         mock_speech_handler):
        """Test voice input toggle functionality"""
        # Create mock callback
        mock_callback = MagicMock()
        
        # Create instance
        chat = ChatInterface(command_callback=mock_callback)
        
        # Mock speech handler instance
        mock_handler_instance = mock_speech_handler.return_value
        mock_handler_instance.wake_word = "hey buddy"
        
        # Test activating voice input
        mock_event = MagicMock()
        mock_event.IsChecked.return_value = True
        chat._on_voice_toggle(mock_event)
        
        # Check speech handler was created and started
        mock_speech_handler.assert_called_once()
        mock_handler_instance.start_listening.assert_called_once()
        
        # Test deactivating voice input
        mock_event.IsChecked.return_value = False
        chat._on_voice_toggle(mock_event)
        
        # Check speech handler was stopped
        mock_handler_instance.stop_listening.assert_called_once()

    @patch('wx.Panel')
    @patch('wx.BoxSizer')
    @patch('wx.TextCtrl')
    @patch('wx.Font')
    @patch('wx.ToggleButton')
    @patch('wx.Button')
    @patch('wx.StaticText')
    @patch('wx.App')
    @patch('wx.Frame')
    def test_handle_speech(self, mock_frame, mock_app, mock_static_text, mock_button,
                          mock_toggle_button, mock_font, mock_text_ctrl, mock_sizer, mock_panel):
        """Test speech handling functionality"""
        # Create mock callback
        mock_callback = MagicMock()
        
        # Create instance
        chat = ChatInterface(command_callback=mock_callback)
        
        # Mock _on_send to prevent extra SetValue calls
        chat._on_send = MagicMock()
        
        # Mock input field
        mock_input = MagicMock()
        chat.input_field = mock_input
        
        # Test handling recognized speech
        test_text = "test command"
        chat._handle_speech(test_text)
        
        # Check text was set
        mock_input.SetValue.assert_called_once_with(test_text)
        
        # Check _on_send was called
        chat._on_send.assert_called_once_with(None)
    
    @patch('wx.Panel')
    @patch('wx.BoxSizer')
    @patch('wx.TextCtrl')
    @patch('wx.App')
    @patch('wx.Frame')
    def test_thread_safety(self, mock_frame, mock_app, mock_text_ctrl, mock_sizer, mock_panel):
        """Test thread-safe operations"""
        # Create instance
        chat = ChatInterface()
        
        # Test thread-safe message display
        chat.display_message("Test message", "User")
        
        # Verify CallAfter was used
        wx.CallAfter.assert_called()
        
        # Test message history thread safety
        with chat._lock:
            assert len(chat.message_history) > 0
    
    @patch('wx.Panel')
    @patch('wx.BoxSizer')
    @patch('wx.TextCtrl')
    @patch('wx.App')
    @patch('wx.Frame')
    def test_cleanup(self, mock_frame, mock_app, mock_text_ctrl, mock_sizer, mock_panel):
        """Test resource cleanup"""
        # Create instance
        chat = ChatInterface()
        
        # Mock speech handler
        mock_speech_handler = MagicMock()
        chat.speech_handler = mock_speech_handler
        
        # Test cleanup
        chat.cleanup()
        
        # Verify resources were cleaned up
        mock_speech_handler.close.assert_called_once()
        assert chat.shutdown_event.is_set()