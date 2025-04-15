import cv2
import easyocr
import numpy as np
from datetime import datetime
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from pathlib import Path
from enum import Enum
from notification_service import NotificationService

# Import our database models from setup_db.py
import sys
sys.path.append('..')
from setup_db import Employee, EntryLog, Base, EntryStatus

class LicensePlateDetector:
    def __init__(self):
        # Initialize EasyOCR
        self.reader = easyocr.Reader(['en'])

        # Load the cascade classifier
        cascade_path = Path('models/haarcascade_russian_plate_number.xml')
        self.plate_cascade = cv2.CascadeClassifier(str(cascade_path))

        if self.plate_cascade.empty():
            raise ValueError("Error: Cascade classifier not loaded properly")

        # Initialize database connection
        self.engine = create_engine('sqlite:///database/parking.db')
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        # Initialize notification service
        self.notification_service = NotificationService()

    def detect_plate(self, image):
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Detect plates
        plates = self.plate_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(20,20),
            maxSize=(300,100)
        )

        if len(plates) == 0:
            return None, None

        # Get the first plate detected
        (x, y, w, h) = plates[0]

        # Add padding to the detection
        padding = 5
        x = max(0, x - padding)
        y = max(0, y - padding)
        w = min(image.shape[1] - x, w + 2*padding)
        h = min(image.shape[0] - y, h + 2*padding)

        # Extract the plate region
        plate_region = gray[y:y+h, x:x+w]

        # Apply some image processing to improve OCR
        plate_region = cv2.equalizeHist(plate_region)
        plate_region = cv2.GaussianBlur(plate_region, (5,5), 0)

        return plate_region, (x, y, x+w, y+h)

    def read_plate(self, plate_image):
        try:
            # Improve image quality for OCR
            plate_image = cv2.resize(plate_image, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

            results = self.reader.readtext(plate_image)
            if results:
                # Get the text with highest confidence
                text = max(results, key=lambda x: x[2])[1]
                # Clean the text (keep only alphanumeric characters)
                plate_number = ''.join(c for c in text if c.isalnum()).upper()
                return plate_number if len(plate_number) >= 4 else None
        except Exception as e:
            print(f"Error reading plate: {e}")
            self.notification_service.send_error_notification(f"Error reading plate: {e}")
            return None

    def find_employee(self, plate_number):
        return self.session.query(Employee).filter_by(license_plate=plate_number).first()

    def check_arrival_status(self, employee, entry_time):
        """
        Check arrival status compared to expected time
        Returns: (status, minutes_late)
        """
        if not employee:
            return EntryStatus.INVALID, None

        entry_time = entry_time.time()
        expected_time = employee.expected_arrival

        # Convert times to minutes since midnight for comparison
        entry_minutes = entry_time.hour * 60 + entry_time.minute
        expected_minutes = expected_time.hour * 60 + expected_time.minute

        # Calculate difference
        minutes_late = entry_minutes - expected_minutes

        # Grace period of 15 minutes
        if minutes_late <= 15:
            return EntryStatus.ON_TIME, 0
        else:
            return EntryStatus.LATE, minutes_late

    def log_entry(self, plate_number, employee=None):
        entry_time = datetime.now()
        status, minutes_late = self.check_arrival_status(employee, entry_time)

        entry = EntryLog(
            license_plate=plate_number,
            timestamp=entry_time,
            employee_name=employee.name if employee else "Unknown",
            department=employee.department if employee else "Unknown",
            status=status,
            minutes_late=minutes_late
        )

        self.session.add(entry)
        self.session.commit()

        # Send notification
        try:
            self.notification_service.send_notification(
                plate_number=plate_number,
                employee_name=entry.employee_name,
                status=status.value,
                minutes_late=minutes_late,
                timestamp=entry_time
            )
        except Exception as e:
            print(f"Failed to send notification: {e}")
            self.notification_service.send_error_notification(str(e))

        return entry

    def process_image(self, image_path):
        try:
            # Read image
            image = cv2.imread(str(image_path))
            if image is None:
                error_msg = f"Could not read image: {image_path}"
                self.notification_service.send_error_notification(error_msg)
                raise ValueError(error_msg)

            # Make a copy for drawing
            result_image = image.copy()

            # Detect plate region
            plate_region, coords = self.detect_plate(image)
            if plate_region is None:
                print(f"No plate detected in {image_path}")
                return None

            # Read plate number
            plate_number = self.read_plate(plate_region)
            if not plate_number:
                print(f"Could not read plate number in {image_path}")
                return None

            # Process detection results
            if coords:
                x1, y1, x2, y2 = coords

                # Find employee and log entry
                employee = self.find_employee(plate_number)
                entry = self.log_entry(plate_number, employee)

                # Set color based on status
                color_map = {
                    EntryStatus.ON_TIME: (0, 255, 0),    # Green
                    EntryStatus.LATE: (0, 165, 255),     # Orange
                    EntryStatus.INVALID: (0, 0, 255)     # Red
                }
                color = color_map[entry.status]

                # Draw rectangle
                cv2.rectangle(result_image, (x1, y1), (x2, y2), color, 2)

                # Add text above rectangle
                if entry.status == EntryStatus.LATE:
                    text = f"{plate_number} - {entry.employee_name} - {entry.status.value} ({entry.minutes_late} mins)"
                else:
                    text = f"{plate_number} - {entry.employee_name} - {entry.status.value}"

                cv2.putText(result_image, text, (x1, y1-10),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

                # Print results
                print(f"\nEntry logged:")
                print(f"Employee: {entry.employee_name}")
                print(f"Plate: {plate_number}")
                print(f"Time: {entry.timestamp}")
                print(f"Status: {entry.status.value}")
                if entry.minutes_late:
                    print(f"Minutes Late: {entry.minutes_late}")

            return result_image

        except Exception as e:
            print(f"Error processing {image_path}: {str(e)}")
            self.notification_service.send_error_notification(f"Error processing {image_path}: {str(e)}")
            return None

    def close(self):
        self.session.close()

def process_directory(input_dir):
    detector = LicensePlateDetector()
    input_path = Path(input_dir)

    try:
        # Create detected_images directory in data folder
        detected_path = Path('data/detected_images')
        detected_path.mkdir(parents=True, exist_ok=True)

        for image_path in input_path.glob('*.jpg'):
            print(f"\nProcessing {image_path.name}...")
            result_image = detector.process_image(image_path)

            if result_image is not None:
                # Create output filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = detected_path / f"detected_{timestamp}_{image_path.name}"
                cv2.imwrite(str(output_path), result_image)

    finally:
        detector.close()

if __name__ == "__main__":
    # For testing the detector directly
    input_dir = "../data/images"
    process_directory(input_dir)
