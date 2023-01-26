from datetime import datetime

import marshmallow.fields as ma_fields
from marshmallow import Schema
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.schema import Column
from sqlalchemy.types import Integer, String, JSON, DateTime, BigInteger, Boolean

Base = declarative_base()


class SessionResponseSchema(Schema):
    id = ma_fields.String()
    value = ma_fields.Dict()
    created_at = ma_fields.DateTime()
    updated_at = ma_fields.DateTime()
    expired_at = ma_fields.DateTime()


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String(50), primary_key=True, autoincrement=False)

    value = Column(JSON(), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def get_value(self, none_if_not_exist: bool = True):
        if self.value is None:
            if none_if_not_exist:
                return None
            else:
                return {}
        return SessionResponseSchema().dump(self).get("value")


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)

    name_first = Column(String(50), nullable=True)
    name_last = Column(String(50), nullable=True)
    name_first_kana = Column(String(50), nullable=True)
    name_last_kana = Column(String(50), nullable=True)

    email = Column(String(50), nullable=True)

    univ_name = Column(String(50), nullable=True)
    univ_year = Column(Integer, nullable=True)

    circle_name = Column(String(50), nullable=True)

    github_user_id = Column(Integer, nullable=True)
    github_user_name = Column(String(50), nullable=True)

    discord_user_id = Column(BigInteger, nullable=True)
    discord_user_name = Column(String(50), nullable=True)
    discord_avatar_hash = Column(String(50), nullable=True)

    team_id = Column(String(5), nullable=True)

    is_admin = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
