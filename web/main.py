import logging
import sys

from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from cruds import session as session_util
from routers import root, oauth_github, oauth_discord, user, supporter

sys.path.append("/user_modules")

from db.engine import get_session as get_db_session, close_session as close_db_session

logging.basicConfig(level=logging.INFO)

app = FastAPI()

templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="/app/static"), name="static")

app.include_router(
    root.router
)

app.include_router(
    oauth_github.router
)

app.include_router(
    oauth_discord.router
)

app.include_router(
    user.router
)

app.include_router(
    supporter.router
)


@app.middleware("http")
async def session_handler(request: Request, call_next):
    # db session start
    get_db_session()

    # 有効期限切れのSessionを削除
    session_util.remove_expired_sessions()

    is_new = False

    # cookieからkey取得
    session_key = request.cookies.get("sess_key")

    # keyがない場合はSession新規作成
    if session_key is None:
        session = session_util.create_session()
        is_new = True
    # keyがあれば照会
    else:
        session = session_util.get_session(session_key)
        # 照会結果がなければSession新規作成
        if session is None:
            session = session_util.create_session()
            is_new = True

    # state.sessionにSessionを格納
    request.state.session = session

    # responseを取得
    response: Response = await call_next(request)

    # 新規作成していたらsess_keyをcookieに格納
    if is_new:
        response.set_cookie("sess_key", session.id, max_age=60 * 60)

    # db session close
    close_db_session()

    return response
