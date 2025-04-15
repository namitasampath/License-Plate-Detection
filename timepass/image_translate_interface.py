import cv2
import numpy as np
import argparse

def enhance_image(image):
    # Apply some preprocessing to improve detection
    # Adjust brightness and contrast
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    cl = clahe.apply(l)
    enhanced = cv2.merge((cl,a,b))
    enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
    return enhanced

def detect_license_plates(image_path, save_plates=False, show_result=True):
    # Load the cascade classifier
    plate_cascade = cv2.CascadeClassifier('haarcascade_russian_plate_number.xml')

    if plate_cascade.empty():
        raise Exception("Error: Cascade classifier not loaded properly")

    # Read the image
    img = cv2.imread(image_path)
    if img is None:
        raise Exception("Error: Image not loaded properly")

    # Keep original for display
    original = img.copy()

    # Enhance image
    img = enhance_image(img)

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Detect plates
    plates = plate_cascade.detectMultiScale(gray,
                                          scaleFactor=1.1,
                                          minNeighbors=5,
                                          minSize=(20,20),
                                          maxSize=(300,100))

    detected_plates = []

    # Process each detected plate
    for i, (x,y,w,h) in enumerate(plates):
        # Draw rectangle on original image
        cv2.rectangle(original, (x,y), (x+w,y+h), (0,255,0), 2)

        # Extract the plate region
        plate = img[y:y+h, x:x+w]
        detected_plates.append(plate)

        # Add text label
        cv2.putText(original, f'Plate {i+1}', (x, y-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,0), 2)

        # Save individual plates if requested
        if save_plates:
            cv2.imwrite(f'plate_{i+1}.jpg', plate)

    # Print results
    print(f"Found {len(plates)} license plates")

    # Show the image if requested
    if show_result:
        # Resize if image is too large
        height, width = original.shape[:2]
        max_height = 800
        if height > max_height:
            ratio = max_height / height
            original = cv2.resize(original, (int(width * ratio), max_height))

        cv2.imshow('Detected License Plates', original)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    return detected_plates

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='License Plate Detection')
    parser.add_argument('image_path', help='Path to the image file')
    parser.add_argument('--save', action='store_true', help='Save detected plates')
    parser.add_argument('--no-display', action='store_true', help='Do not display result')

    args = parser.parse_args()

    try:
        # Run detection
        plates = detect_license_plates(args.image_path,
                                     save_plates=args.save,
                                     show_result=not args.no_display)

        # Return number of plates found
        return len(plates)

    except Exception as e:
        print(f"Error: {e}")
        return -1

if __name__ == "__main__":
    main()
