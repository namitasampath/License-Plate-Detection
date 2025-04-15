
from twilio.rest import Client
from datetime import datetime
from config import TWILIO_CONFIG

class NotificationService:
    def __init__(self):
        self.account_sid = TWILIO_CONFIG['account_sid']
        self.auth_token = TWILIO_CONFIG['auth_token']
        self.from_number = TWILIO_CONFIG['from_number']
        self.to_numbers = TWILIO_CONFIG['to_numbers']

        self.client = Client(self.account_sid, self.auth_token)

    def send_notification(self, plate_number, employee_name, status, minutes_late=None, timestamp=None):
        timestamp = timestamp or datetime.now()

        # Create message based on status
        if status == "LATE":
            message = f"""
🚨 Late Arrival Detected:
License Plate: {plate_number}
Employee: {employee_name}
Minutes Late: {minutes_late}
Time: {timestamp.strftime('%I:%M %p')}
"""
        elif status == "ON TIME":
            message = f"""
✅ On-Time Arrival:
License Plate: {plate_number}
Employee: {employee_name}
Time: {timestamp.strftime('%I:%M %p')}
"""
        else:
            message = f"""
⚠️ Unknown Vehicle Detected:
License Plate: {plate_number}
Time: {timestamp.strftime('%I:%M %p')}
"""

        # Send to all configured numbers
        for to_number in self.to_numbers:
            try:
                self.client.messages.create(
                    body=message,
                    from_=self.from_number,
                    to=to_number
                )
                print(f"Notification sent to {to_number}")
            except Exception as e:
                print(f"Failed to send notification to {to_number}: {e}")

    def send_error_notification(self, error_message):
        message = f"""
❌ System Error:
{error_message}
Time: {datetime.now().strftime('%I:%M %p')}
"""

        for to_number in self.to_numbers:
            try:
                self.client.messages.create(
                    body=message,
                    from_=self.from_number,
                    to=to_number
                )
                print(f"Error notification sent to {to_number}")
            except Exception as e:
                print(f"Failed to send error notification: {e}")
