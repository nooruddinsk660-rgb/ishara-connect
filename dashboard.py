"""
Caregiver dashboard (Stage 2), scoped to production-grade rather than the
system-design.md "minimal read-only table" baseline, per direct request.

Every query in this file filters by the LOGGED-IN caregiver's own
institution_id, server-side -- never by anything the client sends. That's
the actual data-isolation boundary business_idea.pdf section 3.1 asks for;
a dashboard that only *hides* the link to another institution's session in
the UI is not isolation.
"""
import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_socketio import join_room, disconnect
from sqlalchemy import func

from extensions import socketio
from db import SessionLocal, DB_ENABLED
from models import User, Institution, Session as DBSession, TranscriptEvent, Alert, utcnow
from emergency import EMERGENCY_TRIGGERS
from auth import (
    login_required, current_user, login_user, logout_user,
    verify_password, get_csrf_token, check_csrf,
)

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard', template_folder='templates/dashboard')


@dashboard_bp.context_processor
def inject_csrf_token():
    return dict(csrf_token=get_csrf_token())



@dashboard_bp.before_request
def _require_db():
    if not DB_ENABLED:
        return ("The caregiver dashboard needs Postgres configured (DATABASE_URL). "
                "The rest of the app works fine without it -- this page just can't "
                "load any data.", 503)


@dashboard_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user() is not None:
        return redirect(url_for('dashboard.home'))

    error = None
    if request.method == 'POST':
        check_csrf(request.form.get('csrf_token', ''))
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        db = SessionLocal()
        try:
            user = db.query(User).filter_by(email=email).first()
        finally:
            db.close()

        # Same generic message either way -- don't reveal whether the email
        # exists. verify_password() safely returns False on a None hash
        # rather than erroring, so this stays constant-shape either way.
        if user is None or user.role not in ('caregiver', 'admin') or not verify_password(password, user.password_hash):
            error = "Invalid email or password."
        else:
            login_user(user)
            return redirect(url_for('dashboard.home'))

    return render_template('dashboard/login.html', error=error, csrf_token=get_csrf_token())


@dashboard_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('dashboard.login'))


@dashboard_bp.route('/')
@login_required
def home():
    user = current_user()
    db = SessionLocal()
    try:
        institution = db.get(Institution, user.institution_id)

        active_sessions = (
            db.query(DBSession)
            .join(User, DBSession.user_id == User.id)
            .filter(User.institution_id == user.institution_id, DBSession.ended_at.is_(None))
            .order_by(DBSession.started_at.desc())
            .all()
        )

        recent_sessions = (
            db.query(DBSession)
            .join(User, DBSession.user_id == User.id)
            .filter(User.institution_id == user.institution_id, DBSession.ended_at.isnot(None))
            .order_by(DBSession.started_at.desc())
            .limit(20)
            .all()
        )

        # Event counts for every session on this page, in one grouped query
        # instead of one COUNT per session row (N+1).
        session_ids = [s.id for s in active_sessions + recent_sessions]
        event_counts = {}
        if session_ids:
            rows = (
                db.query(TranscriptEvent.session_id, func.count(TranscriptEvent.id))
                .filter(TranscriptEvent.session_id.in_(session_ids))
                .group_by(TranscriptEvent.session_id)
                .all()
            )
            event_counts = dict(rows)

        # Last 30 transcript events across the whole institution, for the
        # initial paint of the live feed (Socket.IO takes over from here).
        recent_events = (
            db.query(TranscriptEvent)
            .join(DBSession, TranscriptEvent.session_id == DBSession.id)
            .join(User, DBSession.user_id == User.id)
            .filter(User.institution_id == user.institution_id)
            .order_by(TranscriptEvent.ts.desc())
            .limit(30)
            .all()
        )
        recent_events = list(reversed(recent_events))  # oldest -> newest for the feed

        # Unacknowledged alerts for this institution, newest first -- this is
        # the banner at the top of the page, the thing a caregiver should see
        # before anything else.
        active_alerts = (
            db.query(Alert)
            .join(DBSession, Alert.session_id == DBSession.id)
            .join(User, DBSession.user_id == User.id)
            .filter(User.institution_id == user.institution_id, Alert.acknowledged_at.is_(None))
            .order_by(Alert.ts.desc())
            .all()
        )

        return render_template(
            'dashboard/home.html',
            user=user, institution=institution,
            active_sessions=active_sessions, recent_sessions=recent_sessions,
            recent_events=recent_events, event_counts=event_counts,
            active_alerts=active_alerts, csrf_token=get_csrf_token(),
            emergency_triggers=EMERGENCY_TRIGGERS,
        )
    finally:
        db.close()


@dashboard_bp.route('/sessions/<int:session_id>')
@login_required
def session_detail(session_id):
    user = current_user()
    db = SessionLocal()
    try:
        # Institution check happens IN the query, not as a follow-up "if" --
        # a session belonging to another institution simply doesn't match
        # and comes back None, same as a session_id that doesn't exist.
        db_session = (
            db.query(DBSession)
            .join(User, DBSession.user_id == User.id)
            .filter(DBSession.id == session_id, User.institution_id == user.institution_id)
            .first()
        )
        if db_session is None:
            return render_template('dashboard/not_found.html'), 404

        events = (
            db.query(TranscriptEvent)
            .filter_by(session_id=session_id)
            .order_by(TranscriptEvent.ts.asc())
            .all()
        )
        alerts = (
            db.query(Alert)
            .filter_by(session_id=session_id)
            .order_by(Alert.ts.asc())
            .all()
        )
        return render_template('dashboard/session_detail.html', user=user, db_session=db_session,
                                events=events, alerts=alerts, csrf_token=get_csrf_token(),
                                emergency_triggers=EMERGENCY_TRIGGERS)
    finally:
        db.close()


# --- Live feed: Socket.IO room join, scoped server-side to the caller's own institution ---

@socketio.on('dashboard_join', namespace='/dashboard')
def handle_dashboard_join():
    user = current_user()
    if user is None or user.role not in ('caregiver', 'admin'):
        disconnect()
        return
    # Room name is derived from the SERVER-SIDE session, never from anything
    # the client sent -- a client cannot ask to join another institution's room.
    join_room(f'institution_{user.institution_id}')


@dashboard_bp.route('/alerts/<int:alert_id>/acknowledge', methods=['POST'])
@login_required
def acknowledge_alert(alert_id):
    check_csrf()  # reads X-CSRFToken header -- see auth.py, this is a fetch() call, not a form POST
    user = current_user()
    db = SessionLocal()
    try:
        # Same institution-scoped-in-the-query pattern as session_detail(): an
        # alert belonging to another institution simply doesn't match, same
        # as one that doesn't exist -- no separate "is this mine?" check to
        # forget to write.
        alert = (
            db.query(Alert)
            .join(DBSession, Alert.session_id == DBSession.id)
            .join(User, DBSession.user_id == User.id)
            .filter(Alert.id == alert_id, User.institution_id == user.institution_id)
            .first()
        )
        if alert is None:
            return jsonify({'error': 'not found'}), 404

        if alert.acknowledged_at is None:
            alert.acknowledged_by = user.id
            alert.acknowledged_at = utcnow()
            db.commit()
            db.refresh(alert)
        # else: already acknowledged (maybe by someone else, maybe a double
        # click) -- idempotent, return the existing state rather than erroring.
        # Two caregivers racing to respond to the same alert is a real
        # scenario; the second click shouldn't look like a failure.

        acknowledger = db.get(User, alert.acknowledged_by) if alert.acknowledged_by else None
        payload = {
            'id': alert.id,
            'acknowledged_by_name': (acknowledger.name or acknowledger.email) if acknowledger else None,
            'acknowledged_at': alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
        }

        socketio.emit('alert_acknowledged', payload, to=f'institution_{user.institution_id}', namespace='/dashboard')
        return jsonify({'ok': True, **payload})
    finally:
        db.close()