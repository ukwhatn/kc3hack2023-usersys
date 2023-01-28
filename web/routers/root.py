import logging
import os
import sys

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

sys.path.append("/user_modules")
from db.cruds import session as session_crud, user as user_crud

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
    is_supporter = False
    if session_value is not None:
        if "user_id" in session_value:
            user = user_crud.get_user(session_value["user_id"])
            if user is None:
                return RedirectResponse("/logout")
        if "is_supporter" in session_value:
            is_supporter = session_value["is_supporter"]

    if success is not None:
        match success:
            case "oauth2":
                success = f"{location}認証に成功しました。"
            case "edit_user_info":
                success = "ユーザー情報を更新しました。"
            case "edit_supporter_info":
                success = "企業情報を更新しました。"
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
            case _:
                error = None

    return templates.TemplateResponse("portal.html",
                                      {"request": request, "user": user, "success": success, "error": error,
                                       "is_supporter": is_supporter})


@router.get("/ref")
def register_ref(
        request: Request,
        ref: str | None = None
):
    if ref is None:
        return RedirectResponse("/")

    session_value = request.state.session.get_value(none_if_not_exist=False)
    session_value["registered_email"] = ref
    session_crud.update_session(request.state.session.id, session_value)

    return RedirectResponse(f"/")


@router.get("/sup")
def register_ref_for_supporter(
        request: Request,
        ref: str | None = None,
        key: str | None = None
):
    if ref is None:
        return RedirectResponse("/")

    if key is None or key != os.environ.get("SUPPORTER_KEY"):
        return RedirectResponse("/")

    session_value = request.state.session.get_value(none_if_not_exist=False)
    session_value["registered_email"] = ref
    session_value["is_supporter"] = True
    session_crud.update_session(request.state.session.id, session_value)

    return RedirectResponse(f"/")


@router.get("/logout")
def logout(request: Request):
    session_crud.delete_session(request.state.session.id)
    return RedirectResponse("/")
