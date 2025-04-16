from sqlalchemy import create_engine, Column, Integer, String, DateTime, Time, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import time
import enum

Base = declarative_base()

class EntryStatus(enum.Enum):
    ON_TIME = "ON TIME"
    LATE = "LATE"
    INVALID = "INVALID"

class Employee(Base):
    __tablename__ = 'employees'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    license_plate = Column(String(20), unique=True, nullable=False)
    department = Column(String(50))
    expected_arrival = Column(Time, nullable=False)  # Expected arrival time

class EntryLog(Base):
    __tablename__ = 'entry_logs'

    id = Column(Integer, primary_key=True)
    license_plate = Column(String(20))
    timestamp = Column(DateTime)
    employee_name = Column(String(100))
    department = Column(String(50))
    status = Column(Enum(EntryStatus))
    minutes_late = Column(Integer, nullable=True)

def init_database():
    # Create database engine (SQLite)
    engine = create_engine('sqlite:///database/parking.db', echo=True)

    # Create all tables
    Base.metadata.create_all(engine)

    # Create session
    Session = sessionmaker(bind=engine)
    session = Session()

    # Add sample employees
    sample_employees = [
        Employee(
            name="Rishita Chaudary",
            license_plate="HR26DK8337",
            department="IT",
            expected_arrival=time(9, 0)   
        ),
        Employee(
            name="Namita Sampath",
            license_plate="KA03MG9267",
            department="HR",
            expected_arrival=time(9, 00)   
        ),
        Employee(
            name="Hareetha Loganathan",
            license_plate="KA5GP8497",
            department="Finance",
            expected_arrival=time(9, 0)   
        ),
        Employee(
            name="Mahika Singh",
            license_plate="MH20DV236E",
            department="Finance",
            expected_arrival=time(9, 0)  
        ),Employee(
            name="Geethika Sudasvini",
            license_plate="IT20BOM",
            department="IT",
            expected_arrival=time(9, 0)   
        ),Employee(
            name="Anthra Prabhu",
            license_plate="KA19P8488",
            department="IT",
            expected_arrival=time(9, 0)
        ),
    ]

    # Add employees to database
    for employee in sample_employees:
        # Check if employee already exists
        existing = session.query(Employee).filter_by(license_plate=employee.license_plate).first()
        if not existing:
            session.add(employee)

    # Commit changes
    session.commit()
    session.close()

if __name__ == "__main__":
    print("Initializing database...")
    try:
        init_database()
        print("Database initialized successfully!")
    except Exception as e:
        print(f"Error initializing database: {e}")
