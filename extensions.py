"""
Shared extension instances.

app.py used to create `socketio = SocketIO(app, ...)` directly. Now that
dashboard.py (a Blueprint) also needs to emit/receive Socket.IO events, that
pattern would force dashboard.py to `from app import socketio`, which
circularly imports back into app.py at module load time. Standard fix:
instantiate here, uninitialized; app.py calls `socketio.init_app(app, ...)`
once it has the Flask app; every other module imports the same instance from
here.
"""
from flask_socketio import SocketIO

socketio = SocketIO()