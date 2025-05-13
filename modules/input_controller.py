import pyautogui
import time
from loguru import logger

class InputController:
    """Controls mouse and keyboard actions"""
    
    def __init__(self, config=None):
        """Initialize input controller
        
        Args:
            config (Config, optional): Configuration manager. Defaults to None.
        """
        # Set PyAutoGUI settings
        pyautogui.FAILSAFE = True  # Move mouse to corner to abort
        
        # Get screen dimensions
        self.screen_width, self.screen_height = pyautogui.size()
        logger.info(f"Screen resolution: {self.screen_width}x{self.screen_height}")
        
        # Load configuration
        self.config = config
        self.move_duration = 0.5
        self.click_delay = 0.1
        self.type_interval = 0.01
        
        if config:
            self.move_duration = config.get('input_controller', {}).get('move_duration', 0.5)
            self.click_delay = config.get('input_controller', {}).get('click_delay', 0.1)
            self.type_interval = config.get('input_controller', {}).get('type_interval', 0.01)
    
    def move_mouse(self, x, y, duration=None):
        """Move mouse cursor to specified coordinates
        
        Args:
            x (int): X coordinate
            y (int): Y coordinate
            duration (float, optional): Movement duration in seconds. Defaults to None.
            
        Returns:
            bool: Success status
        """
        try:
            # Use default duration if not specified
            if duration is None:
                duration = self.move_duration
                
            # Ensure coordinates are within screen bounds
            x = max(0, min(x, self.screen_width))
            y = max(0, min(y, self.screen_height))
            
            # Smooth movement to coordinates
            pyautogui.moveTo(x, y, duration=duration)
            logger.debug(f"Moved mouse to ({x}, {y})")
            return True
        except Exception as e:
            logger.error(f"Error moving mouse: {e}")
            return False
    
    def click(self, x=None, y=None, button="left", double=False, duration=None):
        """Perform mouse click at current position or specified coordinates
        
        Args:
            x (int, optional): X coordinate. Defaults to None (current position).
            y (int, optional): Y coordinate. Defaults to None (current position).
            button (str, optional): Mouse button. Defaults to "left".
            double (bool, optional): Double click. Defaults to False.
            duration (float, optional): Movement duration if coordinates provided. Defaults to None.
            
        Returns:
            bool: Success status
        """
        try:
            # If coordinates provided, move mouse there first
            if x is not None and y is not None:
                self.move_mouse(x, y, duration)
                time.sleep(self.click_delay)  # Small delay before clicking
            
            # Perform click action
            if double:
                pyautogui.doubleClick(button=button)
                logger.debug(f"Double-clicked {button} button")
            else:
                pyautogui.click(button=button)
                logger.debug(f"Clicked {button} button")
            return True
        except Exception as e:
            logger.error(f"Error clicking: {e}")
            return False
    
    def type_text(self, text, interval=None):
        """Type the specified text with a natural typing rhythm
        
        Args:
            text (str): Text to type
            interval (float, optional): Delay between keystrokes. Defaults to None.
            
        Returns:
            bool: Success status
        """
        try:
            # Use default interval if not specified
            if interval is None:
                interval = self.type_interval
                
            pyautogui.typewrite(text, interval=interval)
            logger.debug(f"Typed text: {text}")
            return True
        except Exception as e:
            logger.error(f"Error typing text: {e}")
            return False
    
    def press_key(self, key):
        """Press a specific keyboard key
        
        Args:
            key (str): Key to press
            
        Returns:
            bool: Success status
        """
        try:
            pyautogui.press(key)
            logger.debug(f"Pressed key: {key}")
            return True
        except Exception as e:
            logger.error(f"Error pressing key: {e}")
            return False
    
    def key_combination(self, keys):
        """Press a combination of keys (e.g., Cmd+C)
        
        Args:
            keys (list): List of keys to press simultaneously
            
        Returns:
            bool: Success status
        """
        try:
            # For Mac, 'command' is used instead of 'ctrl' for many shortcuts
            pyautogui.hotkey(*keys)
            logger.debug(f"Pressed key combination: {keys}")
            return True
        except Exception as e:
            logger.error(f"Error with key combination: {e}")
            return False
    
    def scroll(self, clicks, direction="down"):
        """Scroll the page up or down
        
        Args:
            clicks (int): Number of scroll clicks
            direction (str, optional): Scroll direction. Defaults to "down".
            
        Returns:
            bool: Success status
        """
        try:
            if direction.lower() == "up":
                pyautogui.scroll(clicks)  # Positive for up
                logger.debug(f"Scrolled up {clicks} clicks")
            else:
                pyautogui.scroll(-clicks)  # Negative for down
                logger.debug(f"Scrolled down {clicks} clicks")
            return True
        except Exception as e:
            logger.error(f"Error scrolling: {e}")
            return False