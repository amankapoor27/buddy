import os
import yaml
from loguru import logger

class Config:
    """Configuration manager for Buddy application"""
    
    def __init__(self, config_path=None):
        """Initialize configuration manager
        
        Args:
            config_path (str, optional): Path to config file. Defaults to None.
        """
        self.config = {}
        self.config_path = config_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'config.yaml'
        )
        self.load_config()
    
    def load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self.config = yaml.safe_load(f) or {}
                logger.info(f"Loaded configuration from {self.config_path}")
            else:
                logger.warning(f"Config file not found at {self.config_path}, using defaults")
                self.config = self._get_default_config()
                self.save_config()
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            self.config = self._get_default_config()
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False)
            logger.info(f"Saved configuration to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def get(self, key, default=None):
        """Get configuration value
        
        Args:
            key (str): Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        return self.config.get(key, default)
    
    def set(self, key, value):
        """Set configuration value
        
        Args:
            key (str): Configuration key
            value: Configuration value
        """
        self.config[key] = value
        self.save_config()
    
    def _get_default_config(self):
        """Get default configuration
        
        Returns:
            dict: Default configuration
        """
        return {
            'screen_reader': {
                'ocr_engine': 'tesseract',
                'confidence_threshold': 0.7,
            },
            'input_controller': {
                'move_duration': 0.5,
                'click_delay': 0.1,
                'type_interval': 0.01,
            },
            'voice_module': {
                'enabled': True,
                'wake_word': 'buddy',
                'voice_rate': 150,
                'voice_volume': 1.0,
            },
            'chat_interface': {
                'window_width': 600,
                'window_height': 800,
                'font_size': 10,
                'max_history': 100,
            },
        }
    
    def __iter__(self):
        """Make Config object iterable"""
        return iter(self.config)
    
    def __getitem__(self, key):
        """Allow dictionary-style access to config values"""
        return self.config[key]
    
    def items(self):
        """Return config items"""
        return self.config.items()