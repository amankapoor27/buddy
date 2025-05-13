import sys
import os
import pytest
from unittest.mock import MagicMock, patch, call  # Added call import

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import module to test
from speech_handler import SpeechHandler

class TestSpeechHandler:
    """Tests for the SpeechHandler class"""
    
    @patch('speech_recognition.Recognizer')
    @patch('speech_recognition.Microphone')
    def test_init(self, mock_mic, mock_recognizer):
        """Test initialization"""
        # Create mock callback
        mock_callback = MagicMock()
        
        # Create instance
        handler = SpeechHandler(speech_callback=mock_callback)
        
        # Check initialization
        assert handler.speech_callback == mock_callback
        assert handler.recognizer is not None
        assert handler.listening is False
    
    @patch('speech_recognition.Recognizer')
    @patch('speech_recognition.Microphone')
    def test_start_listening(self, mock_mic, mock_recognizer):
        """Test starting speech recognition"""
        # Setup mocks
        mock_recognizer_instance = mock_recognizer.return_value
        mock_mic_instance = mock_mic.return_value
        
        # Create mock callback
        mock_callback = MagicMock()
        
        # Create instance
        handler = SpeechHandler(speech_callback=mock_callback)
        
        # Test starting listening
        result = handler.start_listening()
        
        # Check result
        assert result is True
        assert handler.listening is True
        
        # Verify thread was started
        assert handler.listen_thread is not None
    
    @patch('speech_recognition.Recognizer')
    @patch('speech_recognition.Microphone')
    def test_stop_listening(self, mock_mic, mock_recognizer):
        """Test stopping speech recognition"""
        # Create mock callback
        mock_callback = MagicMock()
        
        # Create instance
        handler = SpeechHandler(speech_callback=mock_callback)
        
        # Check initialization
        assert handler.speech_callback == mock_callback
        handler.listening = True
        
        # Test stopping listening
        handler.stop_listening()
        
        # Check result
        assert handler.listening is False
    
    @patch('speech_recognition.Recognizer')
    @patch('speech_recognition.Microphone')
    def test_wake_word_detection(self, mock_mic, mock_recognizer):
        """Test wake word detection"""
        # Create mock callback
        mock_callback = MagicMock()
        
        # Setup mock recognizer
        mock_recognizer_instance = mock_recognizer.return_value
        mock_recognizer_instance.listen.return_value = MagicMock()
        
        # First recognition - wake word
        mock_recognizer_instance.recognize_whisper.side_effect = [
            "hey buddy",  # First recognition - wake word
            "test command"  # Second recognition - actual command
        ]
        
        # Create instance
        handler = SpeechHandler(speech_callback=mock_callback)
        handler.active_listening = False
        
        # Start listening
        handler.start_listening()
        
        # Wait for recognition thread
        handler.listen_thread.join(timeout=1)
        
        # Check wake word was detected and command processed
        mock_callback.assert_has_calls([
            call("Yes, I'm listening actively now."),
            call("test command")
        ])
        assert handler.active_listening is True
    
    @patch('speech_recognition.Recognizer')
    @patch('speech_recognition.Microphone')
    def test_stop_listening_command(self, mock_mic, mock_recognizer):
        """Test stop listening command"""
        # Create mock callback
        mock_callback = MagicMock()
        
        # Setup mock recognizer
        mock_recognizer_instance = mock_recognizer.return_value
        mock_recognizer_instance.listen.return_value = MagicMock()
        mock_recognizer_instance.recognize_whisper.return_value = "stop listening"
        
        # Create instance
        handler = SpeechHandler(speech_callback=mock_callback)
        handler.active_listening = True
        
        # Start listening
        handler.start_listening()
        
        # Wait for recognition thread
        handler.listen_thread.join(timeout=1)
        
        # Check active listening was disabled
        assert handler.active_listening is False
    
    @patch('pyttsx3.init')
    @patch('speech_recognition.Recognizer')
    @patch('speech_recognition.Microphone')
    def test_speak(self, mock_mic, mock_recognizer, mock_tts):
        """Test text-to-speech functionality"""
        # Setup mock TTS engine
        mock_tts_instance = mock_tts.return_value
        
        # Create mock callback
        mock_callback = MagicMock()
        
        # Create instance
        handler = SpeechHandler(speech_callback=mock_callback)
        
        # Test speaking
        test_text = "Hello, this is a test"
        handler.speak(test_text)
        
        # Wait for TTS queue processing
        time.sleep(0.1)
        
        # Verify TTS engine was called
        mock_tts_instance.say.assert_called_with(test_text)
        mock_tts_instance.runAndWait.assert_called()

    @patch('pyttsx3.init')
    @patch('speech_recognition.Recognizer')
    def test_tts_reinitialize(self, mock_recognizer, mock_tts):
        """Test TTS engine reinitialization"""
        # Setup mock TTS engine
        mock_tts_instance = mock_tts.return_value
        mock_tts_instance.say.side_effect = [Exception("TTS Error"), None]
        
        # Create instance
        handler = SpeechHandler(speech_callback=MagicMock())
        
        # Test TTS error handling
        handler.speak("Test message")
        
        # Wait for reinitialization
        time.sleep(0.2)
        
        # Verify engine was reinitialized
        assert mock_tts.call_count >= 1
        assert mock_tts_instance.setProperty.call_count >= 2
    
    @patch('pyttsx3.init')
    @patch('speech_recognition.Recognizer')
    @patch('speech_recognition.Microphone')
    def test_handle_callback(self, mock_mic, mock_recognizer, mock_tts):
        """Test callback handling with speech"""
        # Setup mock TTS engine
        mock_tts_instance = mock_tts.return_value
        
        # Create mock callback
        mock_callback = MagicMock()
        
        # Create instance
        handler = SpeechHandler(speech_callback=mock_callback)
        
        # Test callback handling
        test_text = "Test message"
        handler._handle_callback(test_text)
        
        # Verify both callback and TTS were called
        mock_callback.assert_called_once_with(test_text)
        mock_tts_instance.say.assert_called_once_with(test_text)
        mock_tts_instance.runAndWait.assert_called_once()
    
    @patch('pyttsx3.init')
    @patch('speech_recognition.Recognizer')
    def test_cleanup(self, mock_recognizer, mock_tts):
        """Test resource cleanup"""
        # Setup mock TTS engine
        mock_tts_instance = mock_tts.return_value
        
        # Create mock callback
        mock_callback = MagicMock()
        
        # Create instance
        handler = SpeechHandler(speech_callback=mock_callback)
        
        # Start listening
        handler.start_listening()
        
        # Test cleanup
        handler.cleanup()
        
        # Verify resources were cleaned up
        assert handler.listening is False
        assert handler.tts_engine is None
        mock_tts_instance.stop.assert_called_once()
        
    @patch('pyttsx3.init')
    @patch('speech_recognition.Recognizer')
    def test_tts_reinitialize(self, mock_recognizer, mock_tts):
        """Test TTS engine reinitialization"""
        # Setup mock TTS engine
        mock_tts_instance = mock_tts.return_value
        mock_tts_instance.say.side_effect = [Exception("TTS Error"), None]
        
        # Create instance
        handler = SpeechHandler(speech_callback=MagicMock())
        
        # Test TTS error handling
        handler.speak("Test message")
        
        # Verify engine was reinitialized
        assert mock_tts.call_count == 2
        assert mock_tts_instance.setProperty.call_count == 4  # 2 calls for each initialization
    
    @patch('speech_recognition.Recognizer')
    @patch('speech_recognition.Microphone')
    def test_continuous_conversation_flow(self, mock_mic, mock_recognizer):
        """Test continuous conversation flow without wake word"""
        # Create mock callback
        mock_callback = MagicMock()
        
        # Setup mock recognizer
        mock_recognizer_instance = mock_recognizer.return_value
        mock_recognizer_instance.listen.return_value = MagicMock()
        
        # Setup recognition responses for the conversation flow
        mock_recognizer_instance.recognize_whisper.side_effect = [
            "hello",  # Initial greeting
            "what is a mango",  # Question about mango
            "5+5"  # Math question
        ]
        
        # Create instance with auto-listening enabled
        handler = SpeechHandler(speech_callback=mock_callback)
        handler.active_listening = True  # Enable active listening from start
        
        # Start listening
        handler.start_listening()
        
        # Wait for recognition thread to process all inputs
        time.sleep(0.5)  # Allow time for processing
        
        # Verify the conversation flow
        mock_callback.assert_has_calls([
            call("hello"),
            call("what is a mango"),
            call("5+5")
        ], any_order=False)
        
        # Cleanup
        handler.stop_listening()