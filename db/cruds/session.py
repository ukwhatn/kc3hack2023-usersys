# append db path
import sys
from datetime import datetime, timedelta

sys.path.append("/user_modules")

from db.models import Session
from db.engine import get_session as get_db_session

import secrets


def remove_expired_sessions():
    with get_db_session() as session:
        session.query(Session).filter(Session.created_at < datetime.utcnow() - timedelta(hours=1)).delete()
        session.commit()


def get_session(session_key: str):
    with get_db_session() as session:
        return session.query(Session).filter_by(id=session_key).first()


def create_session():
    with get_db_session() as session:
        session_instance = Session(id=secrets.token_urlsafe(), value=None)

        session.add(session_instance)
        session.commit()

        return session_instance


def update_session(session_key: str, value: dict | None = None):
    with get_db_session() as session:
        if get_session(session_key) is None:
            return False

        session.query(Session).filter_by(id=session_key).update({"value": value})
        session.commit()

        return True


def delete_session(session_key: str):
    with get_db_session() as session:
        if get_session(session_key) is None:
            return False

        session.query(Session).filter_by(id=session_key).delete()
        session.commit()

        return True


def create_csrf_token():
    return secrets.token_urlsafe()
