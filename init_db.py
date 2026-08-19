"""
One-off convenience script: create all Postgres tables from models.py without
starting the full Flask app. app.py also calls init_db() on its own startup,
so this is optional -- useful if you want the schema in place before your
first `python app.py` run, or want to inspect it separately.

Usage:
    DATABASE_URL=postgresql://user:pass@host:5432/ishara_connect python init_db.py
(or just set DATABASE_URL in .env and run: python init_db.py)
"""
from db import init_db, DB_ENABLED

if __name__ == "__main__":
    if not DB_ENABLED:
        print("DATABASE_URL is not set -- nothing to do. Set it in .env first.")
    else:
        init_db()
