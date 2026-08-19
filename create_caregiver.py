"""
Create (or update) a caregiver/admin login for the dashboard. There's no
self-signup flow -- B2B institution sales means accounts get provisioned by
whoever's running the pilot, not by open registration.

Usage:
    python create_caregiver.py --email dr.sharma@hospital.org --password "..." --name "Dr. Sharma"
    python create_caregiver.py --email admin@hospital.org --password "..." --role admin
    python create_caregiver.py --email x@y.org --password "..." --institution "City General Hospital"

If --institution isn't given, the account is attached to the same "Demo
Institution (v1 placeholder)" that Stage 1's patient sessions use -- so a
caregiver account created with no arguments beyond email/password/name will
immediately see the demo patient's live sessions. Pass --institution once
you're provisioning a real pilot institution instead of the placeholder.
"""
import argparse
import getpass
import sys

from db import DB_ENABLED, SessionLocal, init_db, DEFAULT_INSTITUTION_NAME
from models import Institution, User
from auth import hash_password


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--email', required=True)
    parser.add_argument('--password', help="If omitted, you'll be prompted (safer -- doesn't end up in shell history).")
    parser.add_argument('--name', default=None)
    parser.add_argument('--role', choices=['caregiver', 'admin'], default='caregiver')
    parser.add_argument('--institution', default=DEFAULT_INSTITUTION_NAME,
                         help=f"Institution name. Default: '{DEFAULT_INSTITUTION_NAME}' (Stage 1's placeholder).")
    parser.add_argument('--lang', default='english', help="Dashboard display language preference (not used yet).")
    args = parser.parse_args()

    if not DB_ENABLED:
        print("DATABASE_URL is not set -- nothing to do. Set it in .env first.")
        sys.exit(1)

    password = args.password or getpass.getpass("Password: ")
    if len(password) < 8:
        print("Password must be at least 8 characters.")
        sys.exit(1)

    init_db()
    db = SessionLocal()
    try:
        institution = db.query(Institution).filter_by(name=args.institution).first()
        if institution is None:
            institution = Institution(name=args.institution, tier='hospital', billing_status='pilot')
            db.add(institution)
            db.flush()
            print(f"Created institution '{args.institution}' (id={institution.id}).")

        email = args.email.strip().lower()
        user = db.query(User).filter_by(email=email).first()
        if user is None:
            user = User(institution_id=institution.id, role=args.role, lang_pref=args.lang,
                        name=args.name, email=email, password_hash=hash_password(password))
            db.add(user)
            db.commit()
            print(f"Created {args.role} '{email}' under '{institution.name}' (user id={user.id}).")
        else:
            user.institution_id = institution.id
            user.role = args.role
            user.name = args.name or user.name
            user.password_hash = hash_password(password)
            db.commit()
            print(f"Updated existing user '{email}' (now {args.role} under '{institution.name}').")
    finally:
        db.close()


if __name__ == "__main__":
    main()