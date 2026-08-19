"""
Auth for the caregiver dashboard (Stage 2). Deliberately not a general-purpose
auth system: v1's patient-facing app still has no login at all (unchanged),
and there's still no self-service signup here -- institution B2B sales means
accounts get provisioned by whoever's running the pilot, via
create_caregiver.py, not an open registration form. This is real
session-cookie auth (not a stub): hashed passwords, server-verified
institution scoping, CSRF-protected forms, session expiry.
"""
import hmac
import secrets
import functools
from flask import session, redirect, url_for, request, abort
from werkzeug.security import generate_password_hash, check_password_hash

from db import SessionLocal
from models import User

# --- Password hashing ---

def hash_password(plain: str) -> str:
    return generate_password_hash(plain)


def verify_password(plain: str, password_hash: str) -> bool:
    if not password_hash:
        return False
    return check_password_hash(password_hash, plain)


# --- Session login ---

def login_user(user: User):
    """Store only the user id in the signed session cookie -- never the
    password hash, never anything else sensitive. Every request re-fetches
    the User row fresh from the DB (see current_user())."""
    session.clear()
    session.permanent = True  # honors PERMANENT_SESSION_LIFETIME set in app.py
    session['user_id'] = user.id


def logout_user():
    session.clear()


def current_user():
    """Re-fetches the user on every call rather than caching on `g` across
    the whole request -- this app's dashboard requests are few and cheap
    enough that the extra query is not worth the staleness risk (e.g. a
    deactivated account staying "logged in" for the rest of a long request)."""
    user_id = session.get('user_id')
    if not user_id:
        return None
    db = SessionLocal()
    try:
        return db.get(User, user_id)
    finally:
        db.close()


def login_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if current_user() is None:
            return redirect(url_for('dashboard.login'))
        return view(*args, **kwargs)
    return wrapped


# --- CSRF (manual, no Flask-WTF dependency) ---
# One token per session, generated on GET, checked on POST. Small and
# sufficient for this app's two forms (login, and none currently beyond it);
# not a general CSRF middleware.

def get_csrf_token() -> str:
    token = session.get('csrf_token')
    if not token:
        token = secrets.token_hex(32)
        session['csrf_token'] = token
    return token


def check_csrf(form_token: str = None):
    """Accepts the token from a form field (page POSTs) or from the
    X-CSRFToken header (JS fetch() calls, e.g. the alert-acknowledge button)
    -- same session-bound token either way, just two ways to carry it."""
    supplied = form_token or request.headers.get('X-CSRFToken')
    real_token = session.get('csrf_token')
    if not real_token or not supplied or not hmac.compare_digest(real_token, supplied):
        abort(400, description="Invalid or missing CSRF token. Please reload the page and try again.")