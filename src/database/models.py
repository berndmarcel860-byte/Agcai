"""
Database models using SQLAlchemy ORM
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


class LeadStatus(enum.Enum):
    NEW = "new"
    CONTACTED = "contacted"
    INTERESTED = "interested"
    NOT_INTERESTED = "not_interested"
    APPOINTMENT_SCHEDULED = "appointment_scheduled"
    CALLBACK_REQUESTED = "callback_requested"
    DO_NOT_CALL = "do_not_call"


class CampaignStatus(enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class CallStatus(enum.Enum):
    INITIATED = "initiated"
    RINGING = "ringing"
    ANSWERED = "answered"
    COMPLETED = "completed"
    FAILED = "failed"
    BUSY = "busy"
    NO_ANSWER = "no_answer"


class AppointmentStatus(enum.Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class Lead(Base):
    __tablename__ = 'leads'

    id = Column(Integer, primary_key=True, autoincrement=True)
    phone_number = Column(String(20), nullable=False, unique=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    email = Column(String(255))
    company = Column(String(255))
    status = Column(Enum(LeadStatus), default=LeadStatus.NEW)
    notes = Column(Text)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    call_records = relationship("CallRecord", back_populates="lead")
    appointments = relationship("Appointment", back_populates="lead")


class Campaign(Base):
    __tablename__ = 'campaigns'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(Enum(CampaignStatus), default=CampaignStatus.ACTIVE)
    max_concurrent_calls = Column(Integer, default=5)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    call_records = relationship("CallRecord", back_populates="campaign")


class CallRecord(Base):
    __tablename__ = 'call_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    campaign_id = Column(Integer, ForeignKey('campaigns.id'))
    lead_id = Column(Integer, ForeignKey('leads.id'))
    phone_number = Column(String(20), nullable=False)
    channel_id = Column(String(255))
    call_status = Column(Enum(CallStatus), default=CallStatus.INITIATED)
    duration = Column(Integer, default=0)
    started_at = Column(TIMESTAMP, default=datetime.utcnow)
    answered_at = Column(TIMESTAMP, nullable=True)
    ended_at = Column(TIMESTAMP, nullable=True)

    campaign = relationship("Campaign", back_populates="call_records")
    lead = relationship("Lead", back_populates="call_records")
    conversation_logs = relationship("ConversationLog", back_populates="call_record")
    appointments = relationship("Appointment", back_populates="call_record")


class ConversationLog(Base):
    __tablename__ = 'conversation_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    call_record_id = Column(Integer, ForeignKey('call_records.id'))
    speaker = Column(Enum('agent', 'customer', name='speaker_type'), nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(TIMESTAMP, default=datetime.utcnow)

    call_record = relationship("CallRecord", back_populates="conversation_logs")


class Appointment(Base):
    __tablename__ = 'appointments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    lead_id = Column(Integer, ForeignKey('leads.id'))
    call_record_id = Column(Integer, ForeignKey('call_records.id'))
    appointment_date = Column(DateTime, nullable=False)
    appointment_type = Column(String(100))
    notes = Column(Text)
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.SCHEDULED)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    lead = relationship("Lead", back_populates="appointments")
    call_record = relationship("CallRecord", back_populates="appointments")
