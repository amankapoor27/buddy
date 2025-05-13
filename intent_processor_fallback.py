import re

class IntentProcessorFallback:
    def __init__(self):
        """Initialize the intent processor with regex patterns only (no spacy dependency)"""
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
        # Try pattern matching
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
        
        # Simple keyword-based fallback
        text_lower = text.lower()
        
        # Check for verbs that might indicate intent
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
        
        for verb, intent in verb_to_intent.items():
            if verb in text_lower:
                # Very simple object extraction (words after the verb)
                words = text_lower.split()
                if verb in words and words.index(verb) < len(words) - 1:
                    potential_object = words[words.index(verb) + 1]
                    if intent in ['click', 'type', 'open']:
                        return (intent, potential_object)
                
                # Default parameters for intents that don't need objects
                if intent == 'scroll':
                    direction = 'down'  # Default
                    if 'up' in text_lower:
                        direction = 'up'
                    return (intent, {'direction': direction, 'amount': 5})
                elif intent in ['help', 'exit']:
                    return (intent, None)
        
        # If no intent could be determined
        return ('unknown', None)