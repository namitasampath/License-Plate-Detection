import cv2
import numpy as np
import pytesseract
from typing import Tuple, Optional, Union
import os

# Path to tesseract executable (modify as needed for your system)
pytesseract.pytesseract.tesseract_cmd = r'C:Users/Priya/Downloads/tesseract-ocr-w64-setup-5.5.0.20241111.exe'

def detect_plate(image: np.ndarray) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
    """Detect license plate in the image using Haar Cascade."""
    try:
        # Load the cascade
        plate_cascade = cv2.CascadeClassifier('haarcascade_russian_plate_number.xml')
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detect plates
        plates = plate_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(plates) == 0:
            return None, None
            
        # Get the largest plate (usually the most prominent one)
        (x, y, w, h) = max(plates, key=lambda rect: rect[2] * rect[3])
        
        # Add padding
        padding = 5
        x = max(0, x - padding)
        y = max(0, y - padding)
        w = min(image.shape[1] - x, w + 2 * padding)
        h = min(image.shape[0] - y, h + 2 * padding)
        
        # Extract the plate region
        plate = gray[y:y+h, x:x+w]
        
        # Create contour for visualization
        plate_contour = np.array([[[x, y]], [[x+w, y]], [[x+w, y+h]], [[x, y+h]]])
        
        return plate, plate_contour
    except Exception as e:
        print(f"Error in plate detection: {str(e)}")
        return None, None

def process_plate(plate: np.ndarray) -> np.ndarray:
    """Process the license plate image for better OCR."""
    try:
        # Resize the image for better OCR
        plate = cv2.resize(plate, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        
        # Apply adaptive thresholding for better text extraction
        plate = cv2.adaptiveThreshold(plate, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                    cv2.THRESH_BINARY, 11, 2)
        
        # Apply morphological operations to remove noise
        kernel = np.ones((1, 1), np.uint8)
        plate = cv2.morphologyEx(plate, cv2.MORPH_CLOSE, kernel)
        
        return plate
    except Exception as e:
        print(f"Error in plate processing: {str(e)}")
        return plate

def recognize_plate(plate: np.ndarray) -> str:
    """Perform OCR on the processed license plate."""
    try:
        # Configure tesseract for license plate recognition
        custom_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        
        # Perform OCR
        text = pytesseract.image_to_string(plate, config=custom_config)
        
        # Clean the text
        text = ''.join(c for c in text if c.isalnum())
        
        return text
    except Exception as e:
        print(f"Error in plate recognition: {str(e)}")
        return ""

def main():
    try:
        # Initialize the camera (0 is usually the default webcam)
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("Error: Could not open camera!")
            return
            
        print("Press 'q' to quit")
        print("Press 's' to save the current frame")
        
        last_text = ""  # Store last detected text to avoid duplicates
        
        while True:
            # Read a frame from the camera
            ret, frame = cap.read()
            if not ret:
                print("Error: Could not read frame!")
                break
                
            # Make a copy for drawing
            result_frame = frame.copy()
            
            # Detect plate
            plate, plate_contour = detect_plate(frame)
            
            if plate is not None:
                # Draw contour of the plate on the original image
                cv2.drawContours(result_frame, [plate_contour], -1, (0, 255, 0), 3)
                
                # Process the plate for OCR
                processed_plate = process_plate(plate)
                
                # Recognize text on the plate
                plate_text = recognize_plate(processed_plate)
                
                if plate_text and plate_text != last_text:
                    print(f"Detected License Plate: {plate_text}")
                    last_text = plate_text
                
                # Display the text on the frame
                if plate_text:
                    cv2.putText(result_frame, plate_text, 
                              (plate_contour[0][0][0], plate_contour[0][0][1] - 10),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            
            # Show the frame
            cv2.imshow('License Plate Detection', result_frame)
            
            # Check for key press
            key = cv2.waitKey(1) & 0xFF
            
            # 'q' to quit
            if key == ord('q'):
                break
                
            # 's' to save the current frame
            elif key == ord('s'):
                cv2.imwrite('captured_frame.jpg', frame)
                print("Frame saved as 'captured_frame.jpg'")
        
        # Release the camera and close windows
        cap.release()
        cv2.destroyAllWindows()
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        # Make sure to release the camera if an error occurs
        try:
            cap.release()
            cv2.destroyAllWindows()
        except:
            pass

if __name__ == "__main__":
    main()