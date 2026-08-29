"""
Emergency Detector (Stage 3).

Deliberately its own module rather than inline logic in app.py's prediction
handler, per system-design.md section 2.2: "Emergency detection needs to
short-circuit and alert even if [other processing] is mid-buffer... 
safety-critical path can't wait behind the conversational path." This still
runs in-process today -- no actual separate service, per the same doc's own
"no architecture astronautics" principle -- but the boundary is real: this
file has one job, and app.py's hook into it is two lines.

Hardcoded keyword trigger, exactly as scoped for Stage 3 ("keyword-trigger
(Pain+Call Doctor+Police)", ~1 day effort) -- not sequence/pattern detection,
which system-design.md's target architecture explicitly calls out as a later
capability. Severity is a static mapping, easy to extend without touching
the detection logic itself.
"""
from models import Alert, utcnow

# Police / Call Doctor: calling for outside intervention -> critical.
# Pain / Help: distress signals that need a caregiver's attention, not
# necessarily emergency services -> high. Both classes already exist in the
# 29-word vocabulary (see app.py's CLASSES) -- nothing new to train.
EMERGENCY_TRIGGERS = {
    "Pain": "high",
    "Help": "high",
    "Call Doctor": "critical",
    "Police": "critical",
}


def check_emergency(decoded_phrase):
    """Returns the severity string ('high' | 'critical') if decoded_phrase is
    a trigger phrase, else None. Pure function, no DB/IO -- kept trivially
    testable on its own."""
    return EMERGENCY_TRIGGERS.get(decoded_phrase)


def create_alert(db, session_id, decoded_phrase, severity):
    """Caller owns the db session (open/commit/close) -- same convention as
    every other DB-touching function in this codebase since Stage 1."""
    alert = Alert(
        session_id=session_id,
        ts=utcnow(),
        trigger_phrase=decoded_phrase,
        severity=severity,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert