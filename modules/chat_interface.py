import wx
import threading
import queue
from loguru import logger
from speech_handler import SpeechHandler  # Add this import

class ChatInterface:
    """Provides text-based command input and feedback using wxPython.
    
    This class implements a chat interface with both text and voice input capabilities,
    handling user commands and system responses. It includes error recovery mechanisms
    and proper resource management.
    
    Attributes:
        command_callback (callable): Function to process user commands
        config (dict): Configuration settings for the interface
        message_history (list): List of (sender, message) tuples
        speech_handler (SpeechHandler): Handles voice input/output
    """
    
    def __init__(self, command_callback=None, config=None):
        try:
            self._lock = threading.Lock()
            self.message_history = []
            self.command_queue = queue.Queue()
            self.command_callback = command_callback
            self.shutdown_event = threading.Event()
            
            # Initialize speech_handler as None
            self.speech_handler = None
            
            # Load configuration with validation
            self._load_config(config)
            
            # Initialize components with error handling
            self._setup_ui()
            
            # Start command processing thread
            self.command_thread = threading.Thread(target=self._process_commands)
            self.command_thread.daemon = True
            self.command_thread.start()
            
        except Exception as e:
            self.cleanup()
            logger.error(f"Chat interface initialization failed: {e}")
            raise RuntimeError(f"Failed to initialize chat interface: {e}")

    def cleanup(self):
        """Clean up all resources properly"""
        self.shutdown_event.set()
        
        if hasattr(self, 'speech_handler') and self.speech_handler:
            try:
                self.speech_handler.close()
            except Exception as e:
                logger.error(f"Error closing speech handler: {e}")
        
        if hasattr(self, 'command_queue'):
            try:
                self.command_queue.put(None)  # Signal shutdown
                self.command_queue.join(timeout=2)
            except Exception as e:
                logger.error(f"Error cleaning up command queue: {e}")
        
        if hasattr(self, 'command_thread') and self.command_thread.is_alive():
            try:
                self.command_thread.join(timeout=2)
            except Exception as e:
                logger.error(f"Error joining command thread: {e}")
        
        if hasattr(self, 'frame'):
            try:
                wx.CallAfter(self.frame.Destroy)
            except Exception as e:
                logger.error(f"Error destroying frame: {e}")

    def _process_commands(self):
        """Process commands in a background thread with improved error handling"""
        while not self.shutdown_event.is_set():
            try:
                command = self.command_queue.get(timeout=1)
                if command is None:  # Shutdown signal
                    break
                if self.command_callback:
                    self.command_callback(command)
                else:
                    self._handle_test_commands(command)
                self.command_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing command: {e}")
                time.sleep(1)
    
    def _handle_test_commands(self, command):
        """Handle commands in test mode when no callback is provided"""
        if command.startswith("/"):
            parts = command[1:].split(" ", 1)
            cmd_type = parts[0].lower()
            cmd_args = parts[1] if len(parts) > 1 else ""
            
            if cmd_type == "help":
                self.display_message(
                    "Available commands:\n"
                    "/click [element] - Click on a UI element\n"
                    "/type [text] - Type the specified text\n"
                    "/key [keyname] - Press a specific key\n"
                    "/find [element] - Find a UI element\n"
                    "/scroll [amount] [up/down] - Scroll the page\n"
                    "/screenshot - Take a screenshot\n"
                    "/exit or /quit - Exit the application", 
                    "Buddy"
                )
            else:
                self.display_message(f"Received command: {cmd_type} with args: {cmd_args}", "Buddy")
        else:
            self.display_message("Processing your natural language request...", "Buddy")
    
    def _load_config(self, config):
        """Load and validate configuration settings.
        
        Args:
            config (dict): Configuration dictionary
        """
        self.config = config
        self.window_width = 300
        self.window_height = 400
        self.font_size = 10
        self.max_history = 100
        
        if config:
            try:
                chat_config = config.get('chat_interface', {})
                self.window_width = max(300, chat_config.get('window_width', 300))
                self.window_height = max(400, chat_config.get('window_height', 400))
                self.font_size = max(8, chat_config.get('font_size', 10))
                self.max_history = max(50, chat_config.get('max_history', 100))
            except Exception as e:
                logger.error(f"Config loading error: {e}")
                # Use defaults if config loading fails
    
    def display_message(self, message, sender):
        """Add message to chat history and update UI with error handling.
        
        Args:
            message (str): Message content
            sender (str): Message sender
        """
        try:
            with self._lock:
                # Format and validate message
                if not isinstance(message, str):
                    message = str(message)
                formatted_message = f"{sender}: {message}\n"
                
                # Update history safely
                self.message_history.append((sender, message))
                if len(self.message_history) > self.max_history:
                    self.message_history = self.message_history[-self.max_history:]
                
                # Update UI safely
                wx.CallAfter(self._safe_append_text, formatted_message)
                
                # Handle text-to-speech
                if sender == "Buddy" and self.speech_handler:
                    try:
                        self.speech_handler.speak(message)
                    except Exception as e:
                        logger.error(f"TTS error: {e}")
                
                logger.debug(f"Message from {sender}: {message}")
                
        except Exception as e:
            logger.error(f"Error displaying message: {e}")
            # Attempt to display error message
            wx.CallAfter(self._safe_append_text, "Error displaying message\n")
    
    def _safe_append_text(self, text):
        """Safely append text to chat display."""
        try:
            self.chat_display.AppendText(text)
        except Exception as e:
            logger.error(f"Error updating chat display: {e}")

    def _setup_ui(self):
        """Set up the chat interface UI using wxPython"""
        self.app = wx.App(False)
        self.frame = wx.Frame(None, title="Buddy - Chat Interface", size=(self.window_width, self.window_height))
        
        # Set window style and position
        self.frame.SetWindowStyle(wx.DEFAULT_FRAME_STYLE | wx.STAY_ON_TOP)
        self.frame.Center()
        
        # Create a panel with modern background
        panel = wx.Panel(self.frame)
        panel.SetBackgroundColour(wx.Colour(245, 245, 245))  # Light gray background
        
        # Create a main sizer for the panel
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Chat history display area with improved styling
        self.chat_display = wx.TextCtrl(
            panel,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2 | wx.BORDER_NONE,
            size=(-1, -1)
        )
        self.chat_display.SetBackgroundColour(wx.Colour(255, 255, 255))  # White background
        font = wx.Font(self.font_size, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.chat_display.SetFont(font)
        main_sizer.Add(self.chat_display, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)
        
        # Input area with modern styling
        input_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Text input field with rounded corners
        self.input_field = wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER | wx.BORDER_SIMPLE)
        self.input_field.SetFont(font)
        self.input_field.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.input_field.Bind(wx.EVT_TEXT_ENTER, self._on_send)
        input_sizer.Add(self.input_field, proportion=1, flag=wx.EXPAND | wx.RIGHT, border=5)
        
        # Voice input toggle button with modern styling
        self.voice_button = wx.ToggleButton(panel, label="🎤")
        self.voice_button.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.voice_button.SetBackgroundColour(wx.Colour(230, 230, 230))
        self.voice_button.Bind(wx.EVT_TOGGLEBUTTON, self._on_voice_toggle)
        input_sizer.Add(self.voice_button, proportion=0, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=5)
        
        # Send button with modern styling
        self.send_button = wx.Button(panel, label="Send")
        self.send_button.SetFont(font)
        self.send_button.SetBackgroundColour(wx.Colour(70, 130, 180))  # Steel blue
        self.send_button.SetForegroundColour(wx.Colour(255, 255, 255))  # White text
        self.send_button.Bind(wx.EVT_BUTTON, self._on_send)
        input_sizer.Add(self.send_button, proportion=0, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=10)
        
        main_sizer.Add(input_sizer, proportion=0, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=10)
        
        # Help text with improved styling
        help_text = "Type commands like: /click 'button name', /type 'text', /find 'element'"
        help_label = wx.StaticText(panel, label=help_text)
        help_label.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL))
        help_label.SetForegroundColour(wx.Colour(100, 100, 100))  # Dark gray text
        main_sizer.Add(help_label, proportion=0, flag=wx.ALIGN_CENTER | wx.ALL, border=5)
        
        panel.SetSizer(main_sizer)
        
        # Show and activate the window
        self.frame.Show(True)
        self.frame.Raise()
        wx.CallAfter(self.frame.Raise)
        wx.CallAfter(self.frame.SetFocus)
        
        # Welcome message
        self.display_message("Welcome to Buddy! How can I help you today?", "Buddy")
        
        # Focus on input field
        self.input_field.SetFocus()
        
        # Start a thread to process commands in the background
        command_thread = threading.Thread(target=self._process_commands)
        command_thread.daemon = True
        command_thread.start()
        
        # Show the frame
        self.frame.Show()
    
    def _process_commands(self):
        """Process commands in a background thread"""
        while True:
            try:
                command = self.command_queue.get()
                if self.command_callback:
                    self.command_callback(command)
                self.command_queue.task_done()
            except Exception as e:
                logger.error(f"Error processing command: {e}")
    
    def run(self):
        """Run the wxPython main loop"""
        if self.app:
            self.app.MainLoop()
    
    def _on_send(self, event=None):
        """Handle send button click or Enter key press
        
        Args:
            event: Event object (not used)
        """
        user_input = self.input_field.GetValue().strip()
        if user_input:
            # Display user message
            self.display_message(user_input, "You")
            
            # Clear input field
            self.input_field.SetValue("")
            
            # Process command
            self.process_command(user_input)
    
    def display_message(self, message, sender):
        """Add message to chat history and update UI"""
        # Format message with sender
        formatted_message = f"{sender}: {message}\n"
        
        # Add to history
        self.message_history.append((sender, message))
        
        # Trim history if needed
        if len(self.message_history) > self.max_history:
            self.message_history = self.message_history[-self.max_history:]
        
        # Update UI
        self.chat_display.AppendText(formatted_message)
        
        # Speak Buddy's responses
        if sender == "Buddy" and self.speech_handler:
            self.speech_handler.speak(message)
        
        logger.debug(f"Message from {sender}: {message}")
    
    def _handle_speech(self, text):
        """Handle recognized speech"""
        if text:
            # Set the text in input field to show what was recognized
            wx.CallAfter(self.input_field.SetValue, text)
            wx.CallAfter(self.input_field.SetInsertionPointEnd)
            
            # If this is a system message (like "Yes, I'm listening"), just display it
            if text.startswith("Yes, I'm listening") or text.startswith("Stopping active listening"):
                wx.CallAfter(self.display_message, text, "System")
            else:
                # Otherwise process as a user command
                wx.CallAfter(self._on_send, None)
    
    def process_command(self, command):
        """Process user command and queue for execution
        
        Args:
            command (str): User command
        """
        # Add to command queue
        self.command_queue.put(command)
        
        # Only use this for testing when no callback is provided
        if not self.command_callback:
            # Simple command parsing for testing
            if command.startswith("/"):
                parts = command[1:].split(" ", 1)
                cmd_type = parts[0].lower()
                
                if len(parts) > 1:
                    cmd_args = parts[1]
                else:
                    cmd_args = ""
                
                # Simple response based on command type
                if cmd_type == "help":
                    self.display_message(
                        "Available commands:\n"
                        "/click [element] - Click on a UI element\n"
                        "/type [text] - Type the specified text\n"
                        "/key [keyname] - Press a specific key\n"
                        "/find [element] - Find a UI element\n"
                        "/scroll [amount] [up/down] - Scroll the page\n"
                        "/screenshot - Take a screenshot\n"
                        "/exit or /quit - Exit the application", 
                        "Buddy"
                    )
                else:
                    self.display_message(f"Received command: {cmd_type} with args: {cmd_args}", "Buddy")
            else:
                self.display_message("Processing your natural language request...", "Buddy")
    
    def get_user_input(self):
        """Get next command from queue (blocking)
        
        Returns:
            str: User command
        """
        return self.command_queue.get()
    
    def clear_history(self):
        """Clear chat history"""
        self.message_history = []
        self.chat_display.Clear()
        self.display_message("Chat history cleared", "Buddy")
        logger.info("Chat history cleared")
    
    def _on_voice_toggle(self, event):
        if event.IsChecked():
            if not self.speech_handler:
                self.speech_handler = SpeechHandler(self._handle_speech)
            self.speech_handler.start_listening()
            self.display_message(f"Voice input activated. Say '{self.speech_handler.wake_word}' to start active listening.", "System")
        else:
            if self.speech_handler:
                self.speech_handler.stop_listening()
            self.display_message("Voice input deactivated", "System")
    
    def close(self):
        """Clean up and close the interface"""
        if self.speech_handler:
            self.speech_handler.close()
        if self.frame:
            self.frame.Destroy()