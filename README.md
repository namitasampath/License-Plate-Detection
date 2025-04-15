
# License Plate Detection & Attendance System 📸

A Python-based computer vision project that detects license plates in real-time using OpenCV and EasyOCR, matches them to employees, logs attendance, and sends SMS notifications for late arrivals via Twilio.

---

## 🚀 Features

- Real-time license plate detection using Haar cascades
- OCR with EasyOCR
- Attendance logging with timestamps
- Late arrival detection and notifications
- SMS alerts via Twilio
- Image storage and retrieval
- SQLite database support

---

## 🛠 Setup Process

### 1. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate
```

### 2. Install Requirements

Create a `requirements.txt` with the following contents:

```txt
easyocr
opencv-python
numpy
sqlalchemy
twilio
torch  # EasyOCR dependency
pillow
```

Then install them:

```bash
pip install -r requirements.txt
```

### 3. Project Structure

```
LicensePlate_System/
├── src/
│   └── detector.py
├── models/
│   └── haarcascade_russian_plate_number.xml
├── database/
│   └── parking.db
├── data/
│   ├── images/
│   └── detected_images/
├── config.py
├── setup_db.py
├── notification_service.py
├── requirements.txt
└── main.py
```

### 4. Database Setup

```bash
python setup_db.py
```

---

## ⚙️ Configuration

In `config.py`, add your Twilio credentials:

```python
TWILIO_CONFIG = {
    'account_sid': 'your_sid',
    'auth_token': 'your_token',
    'from_number': 'your_twilio_number',
    'to_numbers': ['recipient_number']
}
```

---

## 📄 File Descriptions

### Core Files

- `main.py`: Entry point of the application
- `src/detector.py`: License plate detection and OCR
- `setup_db.py`: Initializes the SQLite database
- `notification_service.py`: Manages Twilio SMS notifications
- `config.py`: Configuration settings

### Support Files

- `models/haarcascade_russian_plate_number.xml`: Pre-trained model for license plate detection
- `database/parking.db`: SQLite database file
- `data/images/`: Input images
- `data/detected_images/`: Processed image outputs

---

## 🚀 Usage

### Process Images

```bash
python main.py -m process -i data/images
```

### View Logs (last 24 hours)

```bash
python main.py -m view --hours 24
```

---

## 💾 Database Schema

### Employees Table

```sql
CREATE TABLE employees (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100),
    license_plate VARCHAR(20),
    department VARCHAR(50),
    expected_arrival TIME
);
```

### Entry Logs Table

```sql
CREATE TABLE entry_logs (
    id INTEGER PRIMARY KEY,
    license_plate VARCHAR(20),
    timestamp DATETIME,
    employee_name VARCHAR(100),
    department VARCHAR(50),
    status VARCHAR(20),
    minutes_late INTEGER
);
```

---

## 📱 Output Examples

### ✅ On-Time Arrival

```
License Plate: ABC123  
Employee: John Doe  
Time: 09:00 AM
```

### 🚨 Late Arrival

```
License Plate: XYZ789  
Employee: Jane Smith  
Minutes Late: 20  
Time: 09:50 AM
```

---

## 💻 System Requirements

- Python 3.8+
- OpenCV
- EasyOCR
- SQLite
- Twilio Account

---

## 🔧 Error Handling

Handles common issues like:

- Unrecognized license plates
- Database errors
- Image processing failures
- Notification failures

(PS: Still a work in progress)

## 📄 License

MIT License
