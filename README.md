# Buddy - AI Assistant

## Project Overview
Buddy is a voice-controlled AI assistant that helps users control their computer and answer questions using natural language processing. The application features a modern GUI, voice interaction, and integration with the Ollama LLM for intent processing.

## Core Features
- Voice interaction with wake word detection ("hey buddy")
- Text-to-speech with optimized speech rate (1.5x)
- Thread-safe message handling and resource management
- Robust error recovery and cleanup mechanisms
- Modern GUI with wxPython
- Configurable settings through YAML files
- Ollama LLM integration for intent processing
- Screen reader capabilities for accessibility

## Technical Architecture

### Components
1. **Speech Handler**
   - Manages voice recognition and TTS
   - Implements wake word detection
   - Handles continuous listening loop with error recovery
   - Uses macOS native 'say' command for TTS
   - Implements thread-safe message queue
   - Provides robust cleanup on shutdown

2. **Intent Processor**
   - Integrates with Ollama LLM
   - Processes user commands and queries
   - Supports intents: click, type, scroll, open, help, exit
   - Handles conversation mode for general questions
   - Implements fallback mechanisms
   - Monitors LLM server availability

3. **Chat Interface**
   - Modern wxPython-based GUI
   - Thread-safe message handling
   - Visual feedback for voice interaction
   - Keyboard shortcuts for accessibility
   - Progress indicators for long operations

4. **Input Controller**
   - Executes computer control commands
   - Manages mouse and keyboard actions
   - Implements safety checks
   - Provides command validation

5. **Screen Reader**
   - Provides accessibility features
   - Reads screen content for visually impaired users
   - Supports different reading modes
   - Integrates with system accessibility

### Configuration

#### Main Config (config.yaml)
```yaml
llm:
  model: "llama3"
  endpoint: "http://localhost:11434/api/generate"

voice:
  wake_word: "hey buddy"
  speech_rate: 225  # 1.5x normal speed

logging:
  level: "INFO"
  file: "logs/buddy.log"
```

#### LLM Rules (config/llm_rules.yaml)
```yaml
response_rules:
  - rule: "initial_greeting"
    response: "Yes, I am here."
    description: "Simple acknowledgment without follow-up stories"
  
  - rule: "speech_rate"
    value: 225
    description: "Speech rate set to 1.5x normal speed"
```