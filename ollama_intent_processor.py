import os
import json
import requests
import threading
import time
from loguru import logger
from utils.logger import setup_logger

# Initialize logger
logger = setup_logger()

class OllamaIntentProcessor:
    def __init__(self, config=None):
        """Initialize the Ollama-based intent processor
        
        Args:
            config (Config, optional): Configuration manager. Defaults to None.
        """
        self.config = config
        self.model = "llama3" if config is None else config.get('llm', {}).get('model', "llama3")
        self.endpoint = "http://localhost:11434/api/generate"
        
        # Define supported intents and their parameters
        self.supported_intents = {
            'click': ['target'],
            'type': ['content'],
            'scroll': ['direction', 'amount'],
            'open': ['target'],
            'help': [],
            'exit': []
        }
        
        # Connection status
        self.server_available = False
        self.connection_check_interval = 10  # seconds
        
        # Check if Ollama is available and select the best model
        self._check_ollama_availability()
        
        # Start background thread to periodically check connection
        self.should_continue_checking = True
        self.connection_thread = threading.Thread(target=self._connection_monitor)
        self.connection_thread.daemon = True
        self.connection_thread.start()
        logger.info("Started Ollama connection monitoring thread")
    
    def _connection_monitor(self):
        """Background thread to monitor Ollama server connection"""
        while self.should_continue_checking:
            if not self.server_available:
                logger.info("Attempting to connect to Ollama server...")
                self._check_ollama_availability()
            time.sleep(self.connection_check_interval)
    
    def _check_ollama_availability(self):
        def check_server(self):
            """Check if Ollama server is available"""
            try:
                response = requests.get("http://localhost:11434/api/tags", timeout=5)
                return response.status_code == 200
            except Exception:
                return False
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                self.server_available = True
                available_models = response.json().get("models", [])
                if not available_models:
                    logger.warning("No models found in Ollama")
                    return
                
                # Extract model names and details
                model_details = []
                for model in available_models:
                    model_name = model.get("name")
                    if model_name:
                        model_details.append({
                            "name": model_name,
                            "size": model.get("size", 0),
                            "modified_at": model.get("modified_at", 0),
                            "details": model.get("details", {})
                        })
                
                # Check if user-configured model is available
                model_names = [model["name"] for model in model_details]
                logger.info(f"Available Ollama models: {', '.join(model_names)}")
                
                if self.model in model_names:
                    logger.info(f"Using configured Ollama model: {self.model}")
                    return
                
                # If exact match not found, try without version tags
                base_model = self.model.split(":")[0]
                for model_name in model_names:
                    if model_name.startswith(base_model):
                        self.model = base_model
                        logger.info(f"Using base model: {self.model}")
                        return
                
                # If still not found, use first available model
                if model_names:
                    self.model = model_names[0]
                    logger.info(f"Using available model: {self.model}")
            else:
                self.server_available = False
                logger.warning("Could not retrieve Ollama models list. Server returned status code: {}".format(response.status_code))
        except requests.exceptions.ConnectionError:
            self.server_available = False
            logger.warning("Connection to Ollama server failed. Will retry later.")
        except requests.exceptions.Timeout:
            self.server_available = False
            logger.warning("Connection to Ollama server timed out. Will retry later.")
        except Exception as e:
            self.server_available = False
            logger.error(f"Error checking Ollama availability: {e}")
            logger.warning("Ollama may not be running. Will retry connection later.")
    
    def process_text(self, text):
        """Process text through Ollama to determine intent"""
        logger.debug(f"Processing text with Ollama: {text}")
        
        if not self.server_available:
            logger.info("Ollama server not available, attempting to reconnect...")
            self._check_ollama_availability()
            
            if not self.server_available:
                logger.warning("Cannot process text: Ollama server is not available")
                return ('unknown', None)
        
        # Create a more conversational prompt
        system_prompt = f"""You are Buddy, an AI assistant that helps control the computer and answer questions.
        For computer control commands, extract the intent and parameters from user input.
        For general questions, provide direct, concise answers.
        
        When controlling the computer, use these intents:
        {', '.join(self.supported_intents.keys())}
        
        For questions and conversation:
        - Provide direct, concise answers
        - Keep responses under 50 words
        - Be friendly but efficient
        
        Response format:
        For commands: {{
            "intent": "<intent_name>",
            "parameters": {{}},
            "response": "<confirmation_message>"  // New field for verbal response
        }}
        
        For questions: {{
            "intent": "conversation",
            "response": "<your_answer>"  // Direct answer to the question
        }}
        """
        
        # Prepare the API payload
        payload = {
            "model": self.model,
            "prompt": f"{system_prompt}\n\nUser: {text}\n\nAssistant:",
            "stream": False,
            "format": "json",
            "temperature": 0.7,
            "context_window": 4096,
            "max_tokens": 150
        }
        
        try:
            logger.debug(f"Sending request to Ollama with payload: {payload}")
            response = requests.post(self.endpoint, json=payload, timeout=30)  # Increased timeout
            logger.debug(f"Ollama response status: {response.status_code}")
            logger.debug(f"Ollama raw response: {response.text}")
            
            if response.status_code != 200:
                logger.error(f"Ollama server error: {response.status_code}")
                return ('unknown', None)
                
            result = response.json()
            content = result.get('response', '{}')
            
            try:
                parsed = json.loads(content)
                intent = parsed.get('intent', 'unknown')
                parameters = parsed.get('parameters', {})
                response_text = parsed.get('response', '')
                
                if not response_text and intent != 'unknown':
                    response_text = f"I'll {intent} for you now."
                
                logger.debug(f"Parsed intent: {intent}")
                logger.debug(f"Parsed parameters: {parameters}")
                logger.debug(f"Response text: {response_text}")
                
                if intent == 'conversation':
                    return ('conversation', {'response': response_text})
                
                return (intent, parameters)
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Ollama response: {e}")
                return ('unknown', None)
                
        except requests.exceptions.Timeout:
            logger.error("Ollama request timed out")
            return ('unknown', None)
        except Exception as e:
            logger.error(f"Error processing text with Ollama: {e}")
            return ('unknown', None)

    def generate_response(self, intent, parameters):
        # Check LLM rules first
        if self.config and 'llm_rules' in self.config:
            rules = self.config.get('llm_rules', {}).get('response_rules', [])
            for rule in rules:
                if rule.get('rule') == 'initial_greeting' and intent == 'greeting':
                    return rule.get('response', "Yes, I am here.")
        
        # Continue with existing response generation logic
        # If server is not available, try to reconnect first
        if not self.server_available:
            logger.info("Ollama server not available, attempting to reconnect...")
            self._check_ollama_availability()
            
            # If still not available, return fallback response
            if not self.server_available:
                logger.warning("Cannot generate response: Ollama server is not available")
                if intent == 'unknown':
                    return "I'm not sure what you want me to do. Also, I'm having trouble connecting to my language model. Please check if Ollama is running."
                return f"I'll {intent} for you now. Note that I'm having trouble connecting to my language model for more detailed responses."
        
        # Create a prompt for Ollama with more personality
        system_prompt = """You are Buddy, a helpful, friendly computer control assistant with a distinct personality. 
        Generate a natural, conversational response to the user based on the intent and parameters that were recognized.
        
        Be personable, engaging, and show some personality in your responses. Use varied language and phrasing.
        Avoid robotic or template-like responses. Each response should feel unique and tailored to the situation.
        
        For example:
        - Instead of "I'll click for you now" try "I'll click on that button for you right away!"
        - Instead of "I'll open for you now" try "Opening that for you now. Just a moment!"
        - For unknown intents, be helpful and suggest what the user might want to do
        
        Keep responses concise but friendly.
        """
        
        # Format the parameters for the prompt
        if isinstance(parameters, dict):
            param_str = ", ".join([f"{k}: {v}" for k, v in parameters.items()])
        elif parameters:
            param_str = str(parameters)
        else:
            param_str = "none"
        
        user_prompt = f"Intent: {intent}\nParameters: {param_str}"
        
        try:
            # Call the Ollama API
            payload = {
                "model": self.model,
                "prompt": f"{system_prompt}\n\n{user_prompt}\n\nResponse:",
                "stream": False,
                "max_tokens": 150  # Allow for slightly longer responses
            }
            
            response = requests.post(self.endpoint, json=payload, timeout=10)
            response.raise_for_status()
            self.server_available = True  # Update connection status on successful request
            
            # Parse the response
            result = response.json()
            content = result.get('response', '')
            
            return content.strip()
            
        except requests.exceptions.ConnectionError:
            self.server_available = False
            logger.error("Connection to Ollama server failed during response generation")
            if intent == 'unknown':
                return "I'm not sure what you want me to do. Also, I'm having trouble connecting to my language model. Please check if Ollama is running."
            return f"I'll {intent} for you now. Note that I'm having trouble connecting to my language model for more detailed responses."
        except requests.exceptions.Timeout:
            logger.error("Request to Ollama server timed out during response generation")
            if intent == 'unknown':
                return "I'm not sure what you want me to do. The request to my language model timed out."
            return f"I'll {intent} for you now. Note that the request to my language model timed out."
        except Exception as e:
            logger.error(f"Error generating response with Ollama: {e}")
            if intent == 'unknown':
                return "I'm not sure what you want me to do. Could you try phrasing that differently?"
            return f"I'll {intent} for you now."
    
    def shutdown(self):
        """Clean shutdown of the intent processor"""
        self.should_continue_checking = False
        if hasattr(self, 'connection_thread') and self.connection_thread.is_alive():
            self.connection_thread.join(timeout=1.0)
            logger.info("Ollama connection monitoring thread stopped")