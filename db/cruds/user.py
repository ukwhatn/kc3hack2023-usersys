# append db path
import sys
from typing import Any

sys.path.append("/user_modules")

from db.models import Users
from db.engine import get_session as get_db_session


def get_users():
    with get_db_session() as session:
        return session.query(Users).all()


def get_user(user_id: int):
    with get_db_session() as session:
        return session.query(Users).filter(Users.id == user_id).first()


def get_user_by_email(email: str):
    with get_db_session() as session:
        return session.query(Users).filter(Users.email == email).first()


def get_user_by_github_user_id(github_user_id: int):
    with get_db_session() as session:
        return session.query(Users).filter(Users.github_user_id == github_user_id).first()


def get_user_by_discord_user_id(discord_user_id: int):
    with get_db_session() as session:
        return session.query(Users).filter(Users.discord_user_id == discord_user_id).first()


def create_user(user: Users):
    with get_db_session() as session:
        session.add(user)
        session.commit()
        return user


def create_user_from_discord(
        discord_user_id: int,
        discord_user_name: str,
        discord_avatar_hash: str,
        email: str,
        registered_email: str | None = None,
        is_supporter: bool = False
):
    return create_user(Users(
        discord_user_id=discord_user_id,
        discord_user_name=discord_user_name,
        discord_avatar_hash=discord_avatar_hash,
        email=email,
        registered_email=registered_email,
        is_supporter=is_supporter
    ))


def update_user(
        user: Users,
        parameters: dict[str, Any]
):
    with get_db_session() as session:
        session.query(Users).filter(Users.id == user.id).update(parameters)
        session.commit()
        return user
