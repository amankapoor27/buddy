# First import only the setup_logger and initialize it immediately
from utils.logger import setup_logger
import os
import sys
import time
import signal

# Initialize the global logger
logger = setup_logger()

# Ensure modules directory is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our modules
from modules.input_controller import InputController
from utils.config import Config
from modules.screen_reader import ScreenReader
from speech_handler import SpeechHandler

# Import intent processor
try:
    from ollama_intent_processor import OllamaIntentProcessor
    print("Using Ollama-based intent processor")
except ImportError:
    print("Ollama intent processor not available, trying spaCy")
    try:
        from intent_processor import IntentProcessor
        print("Using spaCy-based intent processor")
    except ImportError:
        print("spaCy not available, using fallback intent processor")
        from intent_processor_fallback import IntentProcessorFallback as IntentProcessor

class BuddyApp:
    def __init__(self):
        """Initialize Buddy application"""
        self.logger = setup_logger()
        logger.info("Initializing Buddy...")
        
        # Load configuration
        self.config = Config()
        logger.info("Configuration loaded")
        
        # Initialize input controller
        self.input_controller = InputController(self.config)
        logger.info("Input controller initialized")
        
        # Command processing flag
        self.running = True
        
        # Initialize intent processor
        try:
            self.intent_processor = OllamaIntentProcessor(self.config)
            logger.info("Ollama intent processor initialized")
        except NameError:
            try:
                self.intent_processor = IntentProcessor()
                logger.info("Fallback intent processor initialized")
            except Exception as e:
                logger.error(f"Error initializing intent processor: {e}")
                self.intent_processor = None
        
        # Initialize speech handler
        self.speech_handler = SpeechHandler(self.handle_speech)
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)
    
    def run(self):
        """Run the main application loop"""
        logger.info("Starting Buddy...")
        
        # Start listening immediately
        success = self.speech_handler.start_listening()
        if success:
            logger.info("Voice recognition activated and listening")
            print("Hello! I'm Buddy, your intelligent assistant. I'm listening and ready to help!")
        else:
            logger.error("Failed to start voice recognition")
            print("Error: Could not start voice recognition. Please check your microphone.")
            self.cleanup()
            return
        
        try:
            # Main loop
            while self.running:
                time.sleep(0.1)  # Prevent CPU hogging
                
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
        finally:
            self.cleanup()
    
    def handle_speech(self, text):
        """Handle speech recognition results
        
        Args:
            text (str): Recognized speech text
        """
        logger.info(f"Recognized speech: {text}")
        print(f"You said: {text}")
        
        # Process the text as natural language
        self._process_natural_language(text)
    
    def _process_natural_language(self, text):
        """Process natural language input and convert to commands
        
        Args:
            text (str): Natural language input
        """
        logger.debug(f"Processing natural language: {text}")
        
        if not self.intent_processor:
            print("Sorry, natural language processing is not available.")
            return
        
        # Use intent processor to determine intent and parameters
        intent, params = self.intent_processor.process_text(text)
        logger.debug(f"NLP result: intent={intent}, params={params}")
        
        # Handle conversation responses
        if intent == 'conversation':
            response = params.get('response', "I'm not sure how to answer that.")
            self.speech_handler.speak(response)
            return
        
        # Generate and speak response for commands
        if hasattr(self.intent_processor, 'generate_response'):
            response = self.intent_processor.generate_response(intent, params)
            self.speech_handler.speak(response)
        else:
            if intent == 'unknown':
                self.speech_handler.speak(
                    "I'm not sure what you want me to do. You can ask for help or use commands like: "
                    "click something, type text, scroll up or down, or open a website or app."
                )
                return
            
            self.speech_handler.speak(f"I'll {intent} for you now.")
        
        # Execute the command
        self._execute_command(intent, params)
    
    def _execute_command(self, intent, params):
        """Execute a command based on intent and parameters"""
        try:
            if intent == 'click':
                self._execute_action('click', params)
            elif intent == 'type':
                self._execute_action('type', params)
            elif intent == 'scroll':
                direction = params.get('direction', 'down') if isinstance(params, dict) else 'down'
                amount = params.get('amount', 5) if isinstance(params, dict) else 5
                self._execute_action('scroll', f"{amount} {direction}")
            elif intent == 'open':
                self._handle_open_intent(params)
            elif intent == 'help':
                self._show_help()
            elif intent == 'exit':
                self._exit_application()
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            self.speech_handler.speak("Sorry, I encountered an error executing that command.")
    
    def _execute_action(self, action_type, action_args):
        """Execute an action with the given type and arguments"""
        if action_type == "click":
            # In a real implementation, we would:
            # 1. Use screen reader to find the element
            # 2. Get coordinates
            # 3. Click at those coordinates
            # For now, just simulate with a click in the center
            screen_width, screen_height = self.input_controller.screen_width, self.input_controller.screen_height
            self.input_controller.click(screen_width//2, screen_height//2)
            
        elif action_type == "type":
            self.input_controller.type_text(action_args)
            
        elif action_type == "key":
            self.input_controller.press_key(action_args)
            
        elif action_type == "scroll":
            direction = "down"
            amount = 5
            if action_args:
                parts = str(action_args).split()
                if len(parts) >= 1:
                    try:
                        amount = int(parts[0])
                    except ValueError:
                        direction = parts[0].lower()
                if len(parts) >= 2:
                    direction = parts[1].lower()
            
            self.input_controller.scroll(amount, direction)
    
    def _handle_open_intent(self, target):
        """Handle the open intent with special processing"""
        # Check if it's a website
        if any(domain in str(target).lower() for domain in [".com", ".org", ".net", ".io"]):
            # Open browser and navigate
            self._execute_action("key", "command")
            self._execute_action("type", "space")
            self._execute_action("type", "safari")
            self._execute_action("key", "enter")
            time.sleep(1)  # Wait for browser to open
            self._execute_action("type", target)
            self._execute_action("key", "enter")
        else:
            # Open application
            self._execute_action("key", "command")
            self._execute_action("type", "space")
            self._execute_action("type", target)
            self._execute_action("key", "enter")
    
    def _show_help(self):
        """Show help information"""
        help_text = """
        I can help you with the following:
        - Click on elements ("Click the submit button")
        - Type text ("Type hello world")
        - Press keys ("Press enter")
        - Scroll the page ("Scroll down 5 lines")
        - Open websites or apps ("Open YouTube")
        - Exit the application ("Quit")
        """
        self.speech_handler.speak(help_text)
    
    def _exit_application(self):
        """Exit the application"""
        self.speech_handler.speak("Goodbye!")
        self.running = False
    
    def handle_shutdown(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received shutdown signal {signum}")
        self.running = False
    
    def cleanup(self):
        """Clean up resources"""
        logger.info("Cleaning up resources...")
        if hasattr(self, 'speech_handler'):
            self.speech_handler.cleanup()
        if hasattr(self, 'intent_processor') and hasattr(self.intent_processor, 'shutdown'):
            self.intent_processor.shutdown()
        logger.info("Cleanup complete")

def main():
    try:
        app = BuddyApp()
        app.run()
    except Exception as e:
        print(f"Application startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()


def _process_command(self, text):
        """Process voice command through intent processor"""
        logger.debug(f"Processing command: {text}")
        
        try:
            # Get intent from processor
            intent_result = self.intent_processor.process_text(text)
            logger.debug(f"Intent processing result: {intent_result}")
            
            if intent_result:
                intent, params = intent_result
                logger.info(f"Executing intent: {intent} with params: {params}")
                self._execute_intent(intent, params)
            else:
                logger.warning("No intent could be determined from text")
                self.speech_handler.speak("I'm not sure what you want me to do. Could you rephrase that?")
                
        except Exception as e:
            logger.error(f"Error processing command: {str(e)}")
            self.speech_handler.speak("Sorry, I encountered an error processing your command.")