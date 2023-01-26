import logging

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from cruds import session as session_crud
from cruds import user as user_crud

logging.basicConfig(level=logging.INFO)

router = APIRouter(
    tags=["root"]
)

templates = Jinja2Templates(directory="templates")


@router.get("/")
def root(
        request: Request,
        success: str = None,
        error: str = None,
        location: str = None
):
    session_value = request.state.session.get_value()
    user = None
    if session_value is not None and "user_id" in session_value:
        user = user_crud.get_user(session_value["user_id"])

    if success is not None:
        match success:
            case "oauth2":
                success = f"{location}認証に成功しました。"
            case "edit_user_info":
                success = "ユーザー情報を更新しました。"
            case _:
                success = None

    if error is not None:
        match error:
            case "unauthorized":
                error = "Discordでログインしてください。"
            case "code_is_invalid":
                error = f"{location}の認証コードが無効です。"
            case "failed_to_get_token":
                error = f"{location}のトークンの取得に失敗しました。"
            case "failed_to_get_data":
                error = f"{location}のユーザー情報の取得に失敗しました。"

    return templates.TemplateResponse("portal.html",
                                      {"request": request, "user": user, "success": success, "error": error})


@router.get("/logout")
def logout(request: Request):
    session_crud.delete_session(request.state.session.id)
    return RedirectResponse("/")
