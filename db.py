"""
Database engine/session setup for Stage 1 (system-design.md section 2.4).

This is entirely optional and additive: if DATABASE_URL isn't set, DB_ENABLED
is False and the app runs exactly as it did before this file existed -- no
crash, no behavior change, just no transcript logging. This keeps local dev
without Postgres installed working unmodified, and matches design principle
#5 ("no architecture astronautics") -- you shouldn't need a database running
just to test the camera/prediction path.
"""
import os
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Institution, User

DATABASE_URL = os.environ.get('DATABASE_URL')


engine = None
SessionLocal = None
DB_ENABLED = False

if DATABASE_URL:
    try:
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        # expire_on_commit=False: every DB session in this app is short-lived
        # (open, do one thing, commit, close) and the caller often wants to
        # read an attribute like .id right after commit. Without this, that
        # read is fine as long as the session isn't closed yet, but it's an
        # easy trap for a later contributor to hit a DetachedInstanceError
        # the first time they refactor -- found exactly this while testing
        # Stage 1. Cheap to avoid outright given the usage pattern here.
        SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
        DB_ENABLED = True
    except Exception as e:
        print(f"WARNING: DATABASE_URL is set but engine creation failed ({e}). "
              f"Running without transcript logging.")
else:
    print("INFO: No DATABASE_URL set -- running without Postgres transcript "
          "logging (fine for local dev; set it in .env to enable Stage 1 logging).")


def init_db():
    """Create all tables if they don't exist yet. Safe to call on every startup."""
    global DB_ENABLED
    if not DB_ENABLED:
        return
    try:
        Base.metadata.create_all(engine)
        print("Postgres tables ready: institutions, users, sessions, "
              "transcript_events, alerts, model_versions.")
    except Exception as e:
        print(f"⚠️ Warning: Could not connect to Postgres database ({e}). "
              f"Running without transcript logging.")
        DB_ENABLED = False


DEFAULT_INSTITUTION_NAME = "Demo Institution (v1 placeholder)"


def get_or_create_default_patient_user(db):
    """
    v1 has no login/auth yet (that's Stage 5), so every session is attached
    to one placeholder institution + patient user for now. This gets the
    multi-tenant boundary in place (design principle #3) without blocking on
    auth work that isn't in scope for Stage 1. Swap this out once real
    institution/user creation exists.
    """
    institution = db.query(Institution).filter_by(name=DEFAULT_INSTITUTION_NAME).first()
    if institution is None:
        institution = Institution(name=DEFAULT_INSTITUTION_NAME, tier='hospital', billing_status='pilot')
        db.add(institution)
        db.flush()

    user = db.query(User).filter_by(institution_id=institution.id, role='patient').first()
    if user is None:
        user = User(institution_id=institution.id, role='patient', lang_pref='bengali')
        db.add(user)
        db.flush()

    return user