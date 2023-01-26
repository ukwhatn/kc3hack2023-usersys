import logging
import os

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from cruds import session as session_crud
from cruds import user as user_crud

logging.basicConfig(level=logging.INFO)

router = APIRouter(
    prefix="/oauth2/github",
    tags=["GitHub OAuth2"]
)

templates = Jinja2Templates(directory="templates")


def tokenize(code: str) -> str | None | bool:
    response = httpx.post(
        "https://github.com/login/oauth/access_token",
        headers={
            "Accept": "application/json",
        },
        data={
            "client_id": os.getenv("GITHUB_CLIENT_ID"),
            "client_secret": os.getenv("GITHUB_CLIENT_SECRET"),
            "code": code,
        },
    )

    if response.status_code == 200 and "access_token" in response.json():
        return response.json()["access_token"]

    if "error" in response.json():
        if response.json()["error"] == "bad_verification_code":
            return False

    logging.warning(response.json())
    return None


def get_user_data(token: str) -> dict[str, str] | None:
    response = httpx.get(
        "https://api.github.com/user",
        headers={
            "Accept": "application/json",
            "Authorization": f"token {token}",
        },
    )

    if response.status_code == 200:
        return response.json()

    logging.warning(response.json())
    return None


@router.get("/")
def start_auth():
    return RedirectResponse(f"https://github.com/login/oauth/authorize?client_id={os.getenv('GITHUB_CLIENT_ID')}")


@router.get("/callback")
def callback(request: Request, code: str):
    # codeをtokenに変換
    token = tokenize(code)
    if token is None:
        return RedirectResponse("/?error=failed_to_get_token&location=GitHub")
    if token is False:
        return RedirectResponse("/?error=code_is_invalid&location=GitHub")

    # GitHubのユーザー情報を取得
    github_user = get_user_data(token)
    if github_user is None:
        return RedirectResponse("/?error=failed_to_get_data&location=GitHub")

    github_id = github_user["id"]
    github_name = github_user["login"]

    # sessに保存されている情報を取得
    sess_value = request.state.session.get_value(none_if_not_exist=False)

    # user_idがsessに保存されている = ログイン済み
    # ==> GitHubアカウントを更新する
    if "user_id" in sess_value:
        user = user_crud.get_user(sess_value["user_id"])

        # user_idが間違っていたらセッションを破棄
        if user is None:
            return RedirectResponse("/logout")

        user.github_user_id = int(github_id)
        user.github_user_name = github_name
        user_crud.update_user(user)
    # user_idがsessに保存されていない = これまでログインしていない
    else:
        # Discordログインに遷移
        return RedirectResponse(f"/?error=unauthorized")

    # sessを更新
    session_crud.update_session(request.state.session.id, sess_value)

    # リダイレクト
    return RedirectResponse("/?success=oauth2&location=GitHub")
