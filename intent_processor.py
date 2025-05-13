import spacy
import re

class IntentProcessor:
    def __init__(self):
        """Initialize the intent processor with spaCy"""
        # Load the English NLP model
        self.nlp = spacy.load('en_core_web_sm')
        
        # Define intent patterns
        self.intent_patterns = {
            'click': [
                r'click\s+(?:on\s+)?(.+)',
                r'press\s+(?:on\s+)?(.+)',
                r'select\s+(.+)',
                r'choose\s+(.+)',
                r'tap\s+(?:on\s+)?(.+)'
            ],
            'type': [
                r'type\s+(.+)',
                r'enter\s+(.+)',
                r'input\s+(.+)',
                r'write\s+(.+)'
            ],
            'scroll': [
                r'scroll\s+(up|down)(?:\s+(\d+))?',
                r'move\s+(up|down)(?:\s+(\d+))?'
            ],
            'open': [
                r'open\s+(.+)',
                r'launch\s+(.+)',
                r'start\s+(.+)',
                r'go\s+to\s+(.+)',
                r'navigate\s+to\s+(.+)'
            ],
            'help': [
                r'help',
                r'assist',
                r'guide',
                r'what\s+can\s+you\s+do'
            ],
            'exit': [
                r'exit',
                r'quit',
                r'close',
                r'bye',
                r'goodbye'
            ]
        }
        
        # Compile regex patterns
        self.compiled_patterns = {}
        for intent, patterns in self.intent_patterns.items():
            self.compiled_patterns[intent] = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    
    def process_text(self, text):
        """Process text to determine intent and extract parameters
        
        Args:
            text (str): The text to process
            
        Returns:
            tuple: (intent, parameters)
        """
        # Process with spaCy
        doc = self.nlp(text)
        
        # Try pattern matching first (faster)
        for intent, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                match = pattern.search(text)
                if match:
                    # Extract parameters based on intent
                    if intent == 'click':
                        target = match.group(1).strip()
                        return ('click', target)
                    elif intent == 'type':
                        content = match.group(1).strip()
                        return ('type', content)
                    elif intent == 'scroll':
                        direction = match.group(1).lower()
                        amount = 5  # Default
                        if match.lastindex > 1 and match.group(2):
                            try:
                                amount = int(match.group(2))
                            except ValueError:
                                pass
                        return ('scroll', {'direction': direction, 'amount': amount})
                    elif intent == 'open':
                        target = match.group(1).strip()
                        return ('open', target)
                    elif intent == 'help':
                        return ('help', None)
                    elif intent == 'exit':
                        return ('exit', None)
        
        # Fall back to NLP-based intent recognition
        return self._nlp_based_intent(doc)
    
    def _nlp_based_intent(self, doc):
        """Use NLP to determine intent when pattern matching fails
        
        Args:
            doc: spaCy document
            
        Returns:
            tuple: (intent, parameters)
        """
        # Extract verbs and objects
        verbs = [token.lemma_ for token in doc if token.pos_ == 'VERB']
        objects = [token.text for token in doc if token.dep_ in ('dobj', 'pobj')]
        
        # Map common verbs to intents
        verb_to_intent = {
            'click': 'click',
            'press': 'click',
            'select': 'click',
            'choose': 'click',
            'tap': 'click',
            'type': 'type',
            'enter': 'type',
            'input': 'type',
            'write': 'type',
            'scroll': 'scroll',
            'move': 'scroll',
            'open': 'open',
            'launch': 'open',
            'start': 'open',
            'go': 'open',
            'navigate': 'open',
            'help': 'help',
            'exit': 'exit',
            'quit': 'exit',
            'close': 'exit'
        }
        
        # Try to determine intent from verbs
        for verb in verbs:
            if verb in verb_to_intent:
                intent = verb_to_intent[verb]
                
                # Extract parameters based on intent
                if intent in ['click', 'type', 'open'] and objects:
                    return (intent, objects[0])
                elif intent == 'scroll':
                    direction = 'down'  # Default
                    amount = 5  # Default
                    
                    # Check for direction words
                    for token in doc:
                        if token.text.lower() in ['up', 'down']:
                            direction = token.text.lower()
                        elif token.pos_ == 'NUM':
                            try:
                                amount = int(token.text)
                            except ValueError:
                                pass
                    
                    return (intent, {'direction': direction, 'amount': amount})
                elif intent in ['help', 'exit']:
                    return (intent, None)
        
        # If no intent could be determined
        return ('unknown', None)