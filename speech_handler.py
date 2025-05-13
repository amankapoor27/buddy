import speech_recognition as sr
import time
import threading
import queue
import subprocess
from loguru import logger

class SpeechHandler:
    def __init__(self, speech_callback):
        try:
            self.recognizer = sr.Recognizer()
            self.speech_callback = speech_callback
            self.listening = False
            self.listen_thread = None
            self.wake_word = "hey buddy"  # Default wake word
            self.active_listening = True  # Changed to True for immediate listening
            self.error_count = 0  # Initialize error counter
            self.max_errors = 5  # Maximum consecutive errors before reset
            
            # TTS related initialization
            self.tts_lock = threading.Lock()
            self.tts_queue = queue.Queue()
            self.shutdown_event = threading.Event()
            self.current_process = None
            self.engine_ready = threading.Event()
            
            # Start TTS processing thread
            self.tts_thread = threading.Thread(target=self._process_tts_queue, daemon=True)
            self.tts_thread.start()
            
            # TTS is ready immediately since we're using native command
            self.engine_ready.set()
            
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.energy_threshold = 4000
            
        except Exception as e:
            self.cleanup()
            logger.error(f"Speech handler initialization failed: {e}")
            raise RuntimeError(f"Failed to initialize speech handler: {e}")

    def _listen_loop(self):
        """Continuous listening loop with improved error handling"""
        with sr.Microphone() as source:
            logger.info("Calibrating for ambient noise...")
            try:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                logger.info("Ready! Listening for commands...")
                
                while self.listening and not self.shutdown_event.is_set():
                    try:
                        # Reset error count on successful iteration
                        self.error_count = 0
                        logger.debug("Listening for audio input...")
                        
                        # Listen for audio with timeout
                        audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                        logger.debug("Audio captured, processing with Whisper...")
                        
                        try:
                            # Process audio
                            text = self.recognizer.recognize_whisper(audio, model="base").lower()
                            
                            if text:  # Process all recognized text
                                logger.debug(f"Whisper recognition successful: {text}")
                                self._handle_callback(text)
                                
                        except sr.UnknownValueError:
                            logger.debug("No speech detected in audio")
                            continue
                    except sr.RequestError as e:
                        logger.error(f"Speech recognition request error: {e}")
                        if not self._handle_recognition_error(e):
                            # Reset recognition if needed
                            self._reset_recognition()
                            continue
                        
                    except sr.WaitTimeoutError:
                        # Normal timeout, continue listening
                        continue
                    except Exception as e:
                        logger.error(f"Error in speech recognition loop: {e}")
                        if not self._handle_recognition_error(e):
                            break
                        time.sleep(0.1)  # Brief pause before retry
                        
            except Exception as e:
                logger.error(f"Critical error in listening loop: {e}")
                self.listening = False
                self._reset_recognition()

    def _reset_recognition(self):
        """Reset recognition state after errors"""
        try:
            logger.info("Resetting speech recognition...")
            self.error_count = 0
            
            # Reinitialize recognizer with default settings
            self.recognizer = sr.Recognizer()
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.energy_threshold = 4000
            
            # Notify user
            if self.speech_callback:
                self.speech_callback("Recognition reset complete. Please try speaking again.")
                
            logger.info("Speech recognition reset complete")
            
        except Exception as e:
            logger.error(f"Failed to reset recognition: {e}")
            # Continue with existing recognizer

    def _process_tts_queue(self):
        """Process TTS messages using macOS say command"""
        while not self.shutdown_event.is_set():
            try:
                # Get text from queue with timeout
                text = self.tts_queue.get(timeout=1)
                if text is None:  # Shutdown signal
                    break
                
                with self.tts_lock:
                    try:
                        # Stop any current speech
                        self._stop_current_speech()
                        
                        # Use say command with system voice
                        cmd = ['say', '-r', '225', '-v', 'Alex', text]
                        self.current_process = subprocess.Popen(
                            cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE
                        )
                        
                        # Wait for speech to complete
                        self.current_process.wait()
                        if self.current_process.returncode != 0:
                            stderr = self.current_process.stderr.read().decode().strip()
                            logger.error(f"TTS error: {stderr}")
                    except Exception as e:
                        logger.error(f"TTS error: {e}")
                    finally:
                        self.current_process = None
                
                self.tts_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"TTS queue processing error: {e}")
                time.sleep(0.1)
    
    def _stop_current_speech(self):
        """Stop current speech process if running"""
        if self.current_process:
            try:
                self.current_process.terminate()
                self.current_process.wait(timeout=1)
            except Exception as e:
                logger.error(f"Error stopping speech process: {e}")
                try:
                    self.current_process.kill()
                except:
                    pass
            self.current_process = None
    
    def speak(self, text):
        """Add text to TTS queue
        
        Args:
            text (str): Text to be spoken
        """
        if text and self.tts_queue and not self.shutdown_event.is_set():
            self.tts_queue.put(text)
    
    def cleanup(self):
        """Clean up all resources properly"""
        logger.info("Cleaning up speech handler resources...")
        self.shutdown_event.set()
        self.stop_listening()
        
        # Stop current speech
        self._stop_current_speech()
        
        # Clean up TTS resources
        if self.tts_queue:
            try:
                self.tts_queue.put(None)  # Signal shutdown
                if self.tts_thread and self.tts_thread.is_alive():
                    self.tts_thread.join(timeout=2)
            except Exception as e:
                logger.error(f"Error cleaning up TTS queue: {e}")
            finally:
                # Clear the queue
                while not self.tts_queue.empty():
                    try:
                        self.tts_queue.get_nowait()
                        self.tts_queue.task_done()
                    except queue.Empty:
                        break

    def start_listening(self):
        """Start listening for speech in a separate thread
        
        Returns:
            bool: True if listening started successfully, False otherwise
        """
        if not self.listening:
            try:
                self.listening = True
                self.listen_thread = threading.Thread(target=self._listen_loop)
                self.listen_thread.daemon = True
                self.listen_thread.start()
                logger.info("Speech recognition started successfully")
                return True
            except Exception as e:
                logger.error(f"Failed to start listening: {e}")
                self.listening = False
                self.listen_thread = None
                return False
        return False
    
    def stop_listening(self):
        """Stop the listening thread"""
        if self.listening:
            self.listening = False
            if self.listen_thread and self.listen_thread.is_alive():
                try:
                    self.listen_thread.join(timeout=2)
                except Exception as e:
                    logger.error(f"Error stopping listen thread: {e}")
                finally:
                    self.listen_thread = None
            self.active_listening = False
    
    def _handle_callback(self, text):
        """Handle speech recognition callback safely
        
        Args:
            text (str): The recognized text to process
        """
        logger.debug(f"Speech recognition received text: {text}")
        if self.speech_callback:
            try:
                logger.debug(f"Sending text to callback handler: {text}")
                self.speech_callback(text)
                logger.debug("Callback handler processed text successfully")
            except Exception as e:
                logger.error(f"Error in speech callback: {str(e)}")
                logger.error(f"Exception type: {type(e).__name__}")
        else:
            logger.warning("No speech callback handler registered")
    
    def _handle_recognition_error(self, error):
        """Handle speech recognition errors with recovery logic.
        
        Args:
            error: The exception that occurred
        
        Returns:
            bool: True if should continue, False if should stop
        """
        self.error_count += 1
        if self.error_count >= self.max_errors:
            logger.error(f"Too many recognition errors ({self.error_count}), resetting...")
            self._reset_recognition()
            return False
        logger.warning(f"Recognition error (attempt {self.error_count}): {error}")
        return True

    def close(self):
        """Public method to clean up resources"""
        self.cleanup()