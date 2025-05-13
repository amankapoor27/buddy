import sys
import os
import pytest
from unittest.mock import MagicMock, patch
import numpy as np

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import module to test
from modules.screen_reader import ScreenReader

class TestScreenReader:
    """Tests for the ScreenReader class"""
    
    @patch('pytesseract.pytesseract')
    @patch('PIL.ImageGrab.grab')
    def test_capture_screen(self, mock_grab, mock_pytesseract):
        """Test screen capture functionality"""
        # Create mock image
        mock_image = MagicMock()
        mock_grab.return_value = mock_image
        mock_image.size = (800, 600)
        
        # Create numpy array from mock image
        mock_array = np.zeros((600, 800, 3), dtype=np.uint8)
        mock_image.convert.return_value = mock_array
        
        # Create instance
        screen_reader = ScreenReader()
        
        # Test full screen capture
        result = screen_reader.capture_screen()
        assert mock_grab.called
        assert result is not None
        assert result.shape == (600, 800, 3)
        
        # Test region capture
        region = (100, 100, 200, 200)
        screen_reader.capture_screen(region)
        mock_grab.assert_called_with(bbox=(100, 100, 300, 300))

    @patch('pytesseract.image_to_data')
    def test_text_confidence(self, mock_image_to_data):
        """Test text confidence filtering"""
        # Create mock OCR data with varying confidence
        mock_ocr_data = {
            'text': ['High', 'Medium', 'Low', ''],
            'conf': [95, 75, 30, 0],
            'left': [10, 100, 200, 300],
            'top': [20, 50, 100, 150],
            'width': [50, 60, 40, 30],
            'height': [30, 25, 20, 15]
        }
        mock_image_to_data.return_value = mock_ocr_data
        
        # Create instance with config
        config = {'screen_reader': {'confidence_threshold': 0.9}}
        screen_reader = ScreenReader(config=config)
        test_image = np.zeros((100, 200, 3), dtype=np.uint8)
        
        # Test high confidence filtering
        results = screen_reader.extract_text(test_image)
        assert len(results) == 1
        assert results[0]['text'] == 'High'
        
        # Test lower confidence threshold
        screen_reader.confidence_threshold = 0.7
        results = screen_reader.extract_text(test_image)
        assert len(results) == 2
        assert results[1]['text'] == 'Medium'
    
    def test_image_preprocessing(self):
        """Test image preprocessing"""
        # Create test image with noise
        noisy_image = np.random.randint(0, 255, (100, 200, 3), dtype=np.uint8)
        
        # Create instance
        screen_reader = ScreenReader()
        
        # Test preprocessing
        processed = screen_reader.preprocess_image(noisy_image)
        
        # Verify noise reduction
        assert processed.std() < noisy_image.std()
        assert processed.shape == noisy_image.shape