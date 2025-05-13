import pytesseract
import cv2
import numpy as np
from PIL import ImageGrab
from loguru import logger

class ScreenReader:
    """Analyzes screen content using OCR and computer vision"""
    
    def __init__(self, config=None):
        """Initialize screen reader
        
        Args:
            config (Config, optional): Configuration manager. Defaults to None.
        """
        # Set up OCR engine
        self.tesseract_cmd = r'tesseract'
        if config:
            self.tesseract_cmd = config.get('screen_reader', {}).get('tesseract_cmd', r'tesseract')
        
        # Set pytesseract command
        pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd
        
        # Configuration
        self.ocr_config = r'--oem 3 --psm 11'
        self.confidence_threshold = 0.7
        
        if config:
            self.ocr_config = config.get('screen_reader', {}).get('ocr_config', self.ocr_config)
            self.confidence_threshold = config.get('screen_reader', {}).get('confidence_threshold', 0.7)
        
        logger.info("Screen reader initialized")
    
    def preprocess_image(self, image):
        """Preprocess image for better OCR accuracy
        
        Args:
            image (numpy.ndarray): Image to process
            
        Returns:
            numpy.ndarray: Processed image
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur to reduce noise
            denoised = cv2.GaussianBlur(gray, (3, 3), 0)
            
            # Apply adaptive thresholding
            binary = cv2.adaptiveThreshold(
                denoised,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                11,
                2
            )
            
            # Perform morphological operations to remove noise
            kernel = np.ones((1, 1), np.uint8)
            processed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            
            logger.debug("Image preprocessing completed")
            return processed
        except Exception as e:
            logger.error(f"Error preprocessing image: {e}")
            return image

    def capture_screen(self, region=None):
        """Capture current screen content
        
        Args:
            region (tuple, optional): Region to capture (left, top, width, height). Defaults to None (full screen).
            
        Returns:
            numpy.ndarray: Captured image as numpy array
        """
        try:
            # Capture screen using PIL
            if region:
                left, top, width, height = region
                screenshot = ImageGrab.grab(bbox=(left, top, left+width, top+height))
            else:
                screenshot = ImageGrab.grab()
            
            # Convert to numpy array for OpenCV processing
            image = np.array(screenshot)
            # Convert RGB to BGR (OpenCV format)
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            
            logger.debug(f"Screen captured: {image.shape}")
            return image
        except Exception as e:
            logger.error(f"Error capturing screen: {e}")
            return None
    
    def extract_text(self, image):
        """Extract text from image using OCR
        
        Args:
            image (numpy.ndarray): Image to process
            
        Returns:
            dict: Dictionary with text content and positions
        """
        try:
            # Convert to grayscale for better OCR
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply threshold to get black and white image
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Get OCR data including bounding boxes
            ocr_data = pytesseract.image_to_data(thresh, config=self.ocr_config, output_type=pytesseract.Output.DICT)
            
            # Process results
            results = []
            n_boxes = len(ocr_data['text'])
            for i in range(n_boxes):
                # Filter empty results and low confidence
                if int(ocr_data['conf'][i]) > self.confidence_threshold * 100 and ocr_data['text'][i].strip() != '':
                    text = ocr_data['text'][i]
                    x = ocr_data['left'][i]
                    y = ocr_data['top'][i]
                    w = ocr_data['width'][i]
                    h = ocr_data['height'][i]
                    
                    results.append({
                        'text': text,
                        'position': (x, y, w, h),
                        'center': (x + w//2, y + h//2),
                        'confidence': int(ocr_data['conf'][i]) / 100
                    })
            
            logger.debug(f"Extracted {len(results)} text elements")
            return results
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            return []
    
    def identify_ui_elements(self, image):
        """Detect UI elements like buttons, input fields, etc.
        
        Args:
            image (numpy.ndarray): Image to process
            
        Returns:
            list: List of UI elements with positions and types
        """
        # This is a simplified implementation
        # In a real implementation, we would use more sophisticated computer vision techniques
        # For now, we'll just look for rectangular shapes that might be buttons or input fields
        
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Apply Canny edge detection
            edges = cv2.Canny(blurred, 50, 150)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Process contours to identify UI elements
            ui_elements = []
            for contour in contours:
                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(contour)
                
                # Filter out very small rectangles
                if w > 20 and h > 10:
                    # Determine element type based on shape
                    aspect_ratio = w / float(h)
                    
                    if 2.5 <= aspect_ratio <= 6.0 and h < 40:
                        element_type = 'input_field'
                    elif 1.0 <= aspect_ratio <= 3.0 and h < 50:
                        element_type = 'button'
                    else:
                        element_type = 'unknown'
                    
                    ui_elements.append({
                        'type': element_type,
                        'position': (x, y, w, h),
                        'center': (x + w//2, y + h//2)
                    })
            
            logger.debug(f"Identified {len(ui_elements)} UI elements")
            return ui_elements
        except Exception as e:
            logger.error(f"Error identifying UI elements: {e}")
            return []
    
    def find_element_by_text(self, text, case_sensitive=False):
        """Find UI element containing specific text
        
        Args:
            text (str): Text to find
            case_sensitive (bool, optional): Whether search is case sensitive. Defaults to False.
            
        Returns:
            dict: Element position and properties, or None if not found
        """
        try:
            # Capture screen
            image = self.capture_screen()
            if image is None:
                return None
            
            # Extract text from screen
            text_elements = self.extract_text(image)
            
            # Search for matching text
            for element in text_elements:
                element_text = element['text']
                if not case_sensitive:
                    if text.lower() in element_text.lower():
                        logger.info(f"Found text '{text}' at {element['center']}")
                        return element
                else:
                    if text in element_text:
                        logger.info(f"Found text '{text}' at {element['center']}")
                        return element
            
            logger.warning(f"Text '{text}' not found on screen")
            return None
        except Exception as e:
            logger.error(f"Error finding element by text: {e}")
            return None