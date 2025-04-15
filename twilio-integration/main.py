import argparse
import cv2
from pathlib import Path
from datetime import datetime, timedelta
from src.detector import LicensePlateDetector
from setup_db import EntryLog, EntryStatus
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from notification_service import NotificationService

def process_images(input_dir):
    """Process all images in the input directory"""
    detector = LicensePlateDetector()
    notification_service = NotificationService()

    try:
        input_path = Path(input_dir)
        if not input_path.exists():
            error_msg = f"Error: Directory {input_dir} does not exist"
            notification_service.send_error_notification(error_msg)
            print(error_msg)
            return

        # Create detected_images directory in data folder
        detected_path = Path('data/detected_images')
        detected_path.mkdir(parents=True, exist_ok=True)

        image_files = list(input_path.glob('*.jpg')) + list(input_path.glob('*.jpeg'))
        if not image_files:
            msg = f"No images found in {input_dir}"
            notification_service.send_error_notification(msg)
            print(msg)
            return

        print(f"Found {len(image_files)} images to process")

        for image_path in image_files:
            print(f"\nProcessing {image_path.name}...")
            result_image = detector.process_image(image_path)

            if result_image is not None:
                # Save result image with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = detected_path / f"detected_{timestamp}_{image_path.name}"
                cv2.imwrite(str(output_path), result_image)

    except Exception as e:
        error_msg = f"Error in process_images: {str(e)}"
        notification_service.send_error_notification(error_msg)
        print(error_msg)
    finally:
        detector.close()

def view_recent_logs(hours=24):
    """View recent entry logs from the database"""
    engine = create_engine('sqlite:///database/parking.db')
    Session = sessionmaker(bind=engine)
    session = Session()
    notification_service = NotificationService()

    try:
        # Get entries from last 24 hours
        time_threshold = datetime.now() - timedelta(hours=hours)
        entries = session.query(EntryLog)\
            .filter(EntryLog.timestamp >= time_threshold)\
            .order_by(EntryLog.timestamp.desc())\
            .all()

        if not entries:
            print(f"No entries found in the last {hours} hours")
            return

        print(f"\nRecent entries (last {hours} hours):")
        print("-" * 80)

        # Count statistics
        total = len(entries)
        on_time = sum(1 for e in entries if e.status == EntryStatus.ON_TIME)
        late = sum(1 for e in entries if e.status == EntryStatus.LATE)
        invalid = sum(1 for e in entries if e.status == EntryStatus.INVALID)

        # Print each entry
        for entry in entries:
            print(f"Time: {entry.timestamp}")
            print(f"License Plate: {entry.license_plate}")
            print(f"Employee: {entry.employee_name}")
            print(f"Department: {entry.department}")
            print(f"Status: {entry.status.value}")
            if entry.minutes_late:
                print(f"Minutes Late: {entry.minutes_late}")
            print("-" * 80)

        # Print summary
        summary = f"""
Summary Report:
Total Entries: {total}
On Time: {on_time}
Late: {late}
Invalid/Unknown: {invalid}
"""
        print(summary)

        # Send summary notification
        notification_service.send_notification(
            plate_number="SUMMARY",
            employee_name="System Report",
            status="REPORT",
            timestamp=datetime.now(),
            custom_message=summary
        )

    except Exception as e:
        error_msg = f"Error viewing logs: {str(e)}"
        notification_service.send_error_notification(error_msg)
        print(error_msg)
    finally:
        session.close()

def main():
    parser = argparse.ArgumentParser(description='License Plate Detection System')
    parser.add_argument('--mode', '-m',
                       choices=['process', 'view'],
                       default='process',
                       help='Mode: process images or view recent logs')
    parser.add_argument('--input', '-i',
                       default='data/images',
                       help='Input directory containing images')
    parser.add_argument('--hours', '-hr',
                       type=int,
                       default=24,
                       help='Hours of logs to view')

    args = parser.parse_args()

    try:
        if args.mode == 'process':
            print(f"Processing images from: {args.input}")
            process_images(args.input)
        else:
            view_recent_logs(args.hours)
    except Exception as e:
        notification_service = NotificationService()
        error_msg = f"System Error: {str(e)}"
        notification_service.send_error_notification(error_msg)
        print(error_msg)

if __name__ == "__main__":
    main()
