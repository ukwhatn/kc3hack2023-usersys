# append db path
import sys

sys.path.append("/user_modules")

from db.models import Users
from db.engine import session


def get_user(user_id: int):
    return session.query(Users).filter(Users.id == user_id).first()


def get_user_by_email(email: str):
    return session.query(Users).filter(Users.email == email).first()


def get_user_by_github_user_id(github_user_id: int):
    return session.query(Users).filter(Users.github_user_id == github_user_id).first()


def get_user_by_discord_user_id(discord_user_id: int):
    return session.query(Users).filter(Users.discord_user_id == discord_user_id).first()


def create_user(user: Users):
    session.add(user)
    session.commit()
    return user


def create_user_from_discord(
        discord_user_id: int,
        discord_user_name: str,
        discord_avatar_hash: str,
        email: str
):
    return create_user(Users(
        discord_user_id=discord_user_id,
        discord_user_name=discord_user_name,
        discord_avatar_hash=discord_avatar_hash,
        email=email
    ))


def update_user(user: Users):
    session.commit()
    return user
