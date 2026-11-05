from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
import enum

# 1. BASE VE ENGINE TANIMLARI (Hatanın çözümü burası)
Base = declarative_base()

class BookingStatus(enum.Enum):
    PENDING = "PENDING"
    MATCHED = "MATCHED"
    MANUAL = "MANUAL"
    COMPLETED = "COMPLETED"

class Company(Base):
    __tablename__ = 'companies'
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    subscription_plan = Column(String, default="PRO")
    is_active = Column(Boolean, default=True)

class User(Base):
    __tablename__ = 'users'
    id = Column(String, primary_key=True)
    company_id = Column(String, ForeignKey('companies.id'), nullable=False)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default="ADMIN")

class Driver(Base):
    __tablename__ = 'drivers'
    id = Column(String, primary_key=True)
    company_id = Column(String, ForeignKey('companies.id'), nullable=False)
    full_name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    vehicle_plate = Column(String, nullable=False)
    capacity = Column(Integer, default=4)
    current_lat = Column(Float)
    current_lon = Column(Float)

class Booking(Base):
    __tablename__ = 'bookings'
    id = Column(String, primary_key=True)
    company_id = Column(String, ForeignKey('companies.id'), nullable=False)
    customer_name = Column(String, nullable=False)
    phone_number = Column(String)
    passengers = Column(Integer, default=1)
    
    pickup_address = Column(String)
    pickup_lat = Column(Float)
    pickup_lon = Column(Float)
    pickup_time = Column(DateTime, nullable=False)
    
    status = Column(Enum(BookingStatus), default=BookingStatus.PENDING)
    assigned_driver_id = Column(String, ForeignKey('drivers.id'), nullable=True)

    driver = relationship("Driver", foreign_keys=[assigned_driver_id])

engine = create_engine('sqlite:///transfer_system.db')
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)