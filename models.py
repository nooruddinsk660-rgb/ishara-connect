"""
SQLAlchemy models for Ishara-Connect's data layer.

Schema matches ishara-connect-system-design.md section 2.3 exactly, and the
full 6-table schema is built now -- even though Stage 1 only actively writes
to `sessions` and `transcript_events` -- per that doc's design principle #3:
"retrofitting multi-tenancy later is expensive; designing for it now is free."

Privacy note (system-design.md section 3): raw video frames and full
per-frame landmark coordinate arrays are never persisted here. The only
thing captured per event is the short list of stabilized single-word
predictions that produced a confirmed phrase (see `gesture_sequence` below)
plus the decoded text -- both already far more abstract than a frame or a
raw skeleton.
"""
import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def utcnow():
    """Naive UTC datetime, matching the timezone-naive DateTime columns below.
    datetime.datetime.utcnow() is deprecated as of Python 3.12 -- this is the
    non-deprecated equivalent that returns the same naive-UTC value, found
    while testing Stage 1 against a real Postgres instance."""
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)


class Institution(Base):
    __tablename__ = 'institutions'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    tier = Column(String(20), nullable=False, default='hospital')  # school | hospital | gov
    billing_status = Column(String(50), nullable=False, default='pilot')

    users = relationship('User', back_populates='institution')


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    institution_id = Column(Integer, ForeignKey('institutions.id'), nullable=False)
    role = Column(String(20), nullable=False, default='patient')  # patient | caregiver | admin
    lang_pref = Column(String(20), nullable=False, default='bengali')
    # Added Stage 2, for caregiver/admin dashboard login. Null for 'patient' rows
    # (the placeholder patient user from Stage 1 never logs in anywhere).
    name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True, unique=True)
    password_hash = Column(String(255), nullable=True)

    institution = relationship('Institution', back_populates='users')
    sessions = relationship('Session', back_populates='user')


class Session(Base):
    __tablename__ = 'sessions'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    started_at = Column(DateTime, default=utcnow, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    device_type = Column(String(50), nullable=True)  # 'browser', 'kiosk', ...

    user = relationship('User', back_populates='sessions')
    transcript_events = relationship('TranscriptEvent', back_populates='session')
    alerts = relationship('Alert', back_populates='session')


class TranscriptEvent(Base):
    __tablename__ = 'transcript_events'
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('sessions.id'), nullable=False)
    ts = Column(DateTime, default=utcnow, nullable=False)
    # JSON-encoded list of the raw single-frame predictions that stabilized
    # into decoded_phrase, e.g. '["Water","Water","Water"]' -- NOT landmark
    # coordinates and NOT a video frame. See privacy note above.
    gesture_sequence = Column(Text, nullable=True)
    decoded_phrase = Column(String(255), nullable=False)
    confidence = Column(Float, nullable=True)
    mode = Column(String(20), nullable=False, default='word')  # word | sentence

    session = relationship('Session', back_populates='transcript_events')


class Alert(Base):
    """Not written to yet -- this is Stage 3 (Emergency Detector). Table
    exists now so the schema is stable and Stage 3 doesn't need a migration."""
    __tablename__ = 'alerts'
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('sessions.id'), nullable=False)
    ts = Column(DateTime, default=utcnow, nullable=False)
    trigger_phrase = Column(String(255), nullable=False)
    severity = Column(String(20), nullable=False, default='info')
    acknowledged_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)

    session = relationship('Session', back_populates='alerts')


class ModelVersion(Base):
    __tablename__ = 'model_versions'
    id = Column(Integer, primary_key=True)
    type = Column(String(20), nullable=False, default='rf')  # rf | lstm
    version = Column(String(20), nullable=True)
    accuracy = Column(Float, nullable=True)
    trained_at = Column(DateTime, nullable=True)
    artifact_path = Column(String(255), nullable=True)