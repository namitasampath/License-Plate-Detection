import argparse
import cv2
from pathlib import Path
from datetime import datetime, timedelta
from src.detector import LicensePlateDetector
from setup_db import EntryLog
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def process_images(input_dir):
    """Process all images in the input directory"""
    detector = LicensePlateDetector()

    try:
        input_path = Path(input_dir)
        if not input_path.exists():
            print(f"Error: Directory {input_dir} does not exist")
            return

        # Create detected_images directory in data folder
        detected_path = Path('data/detected_images')
        detected_path.mkdir(parents=True, exist_ok=True)

        image_files = list(input_path.glob('*.jpg')) + list(input_path.glob('*.jpeg'))
        if not image_files:
            print(f"No images found in {input_dir}")
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

    finally:
        detector.close()

def view_recent_logs(hours=24):
    """View recent entry logs from the database"""
    engine = create_engine('sqlite:///database/parking.db')
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
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
        for entry in entries:
            print(f"Time: {entry.timestamp}")
            print(f"License Plate: {entry.license_plate}")
            print(f"Employee: {entry.employee_name}")
            print(f"Department: {entry.department}")
            print(f"Status: {entry.status.value}")
            if entry.minutes_late:
                print(f"Minutes Late: {entry.minutes_late}")
            print("-" * 80)

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

    if args.mode == 'process':
        print(f"Processing images from: {args.input}")
        process_images(args.input)
    else:
        view_recent_logs(args.hours)

if __name__ == "__main__":
    main()
