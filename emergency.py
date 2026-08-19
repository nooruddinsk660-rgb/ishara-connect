"""
Stage 3 — Emergency Detector module for Ishara-Connect.

Provides pure keyword-trigger checking (zero DB/IO for check_emergency)
and alert record creation helper.
"""
from models import Alert, utcnow

# Emergency trigger phrases and their severity mappings
EMERGENCY_TRIGGERS = {
    'Pain': 'high',
    'Help': 'high',
    'Call Doctor': 'critical',
    'Police': 'critical',
}


def check_emergency(phrase: str):
    """
    Checks if a predicted phrase is an emergency trigger keyword.
    Returns the severity string ('high' or 'critical') if matched, else None.
    Pure function with zero I/O.
    """
    if not phrase:
        return None
    normalized = phrase.strip().lower()
    for trigger, severity in EMERGENCY_TRIGGERS.items():
        if trigger.lower() == normalized:
            return severity
    return None


def create_alert(db, session_id: int, trigger_phrase: str, severity: str):
    """
    Persists a new Alert row into the database.
    """
    alert = Alert(
        session_id=session_id,
        trigger_phrase=trigger_phrase,
        severity=severity,
        ts=utcnow()
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert
