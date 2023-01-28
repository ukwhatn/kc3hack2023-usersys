import logging
import re
import sys

from fastapi import APIRouter, Request, Form, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

sys.path.append("/user_modules")
from db.cruds import session as session_crud, user as user_crud

logging.basicConfig(level=logging.INFO)

router = APIRouter(
    prefix="/supporter",
    tags=["Supporter"]
)

templates = Jinja2Templates(directory="templates")


@router.get("/info")
def edit_user_data(
        request: Request,
        error: str = None
):
    # セッションバリュー取得
    sess_value = request.state.session.get_value()

    # 未ログインならポータルにリダイレクト
    if sess_value is None or "user_id" not in sess_value:
        return RedirectResponse(url="/?error=unauthorized")

    # ユーザー取得
    user = user_crud.get_user(sess_value["user_id"])

    # ユーザーが存在しないならセッションを破棄してリダイレクト
    if user is None:
        return RedirectResponse(url="/logout")

    # is_supporterがFalseならポータルにリダイレクト
    if user.is_supporter is False:
        return RedirectResponse(url="/")

    errors = None
    if error is not None:
        errors = ["CSRFトークンチェックに失敗しました。再試行してください。"]

    # CORSトークン生成・セッションに保存
    csrf_token = session_crud.create_csrf_token()
    sess_value["csrf_token"] = csrf_token
    session_crud.update_session(request.state.session.id, sess_value)

    return templates.TemplateResponse("edit_supporter_info.html",
                                      {"request": request, "user": user, "csrf_token": csrf_token, "errors": errors})


@router.post("/info")
def post_user_info(
        request: Request,
        _csrf_token: str = Form(None),
        name_first: str = Form(None),
        name_last: str = Form(None),
        email: str = Form(None)
):
    # CSRFチェック
    sess_value = request.state.session.get_value()
    if sess_value is None or "csrf_token" not in sess_value \
            or sess_value["csrf_token"] != _csrf_token or _csrf_token is None:
        return RedirectResponse(url="/supporter/info?error=csrf_invalid", status_code=status.HTTP_303_SEE_OTHER)

    # 未ログインならポータルにリダイレクト
    if sess_value is None or "user_id" not in sess_value:
        return RedirectResponse(url="/?error=unauthorized")

    # ユーザー取得
    user = user_crud.get_user(sess_value["user_id"])

    # ユーザーが存在しないならセッションを破棄してリダイレクト
    if user is None:
        return RedirectResponse(url="/logout", status_code=status.HTTP_303_SEE_OTHER)

    # is_supporterがFalseならポータルにリダイレクト
    if user.is_supporter is False:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

    # バリデーションチェック
    is_valid = True
    errors = []

    regex_email = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

    if name_first is None or len(name_first) == 0:
        is_valid = False
        errors.append("企業名を入力してください")

    if name_last is None or len(name_last) == 0:
        is_valid = False
        errors.append("ご担当者氏名を入力してください")

    if email is None or len(email) == 0:
        is_valid = False
        errors.append("メールアドレスを入力してください")
    elif not regex_email.fullmatch(email):
        is_valid = False
        errors.append("メールアドレスの形式が正しくありません")

    if not is_valid:
        _csrf_token = session_crud.create_csrf_token()
        sess_value["csrf_token"] = _csrf_token
        session_crud.update_session(request.state.session.id, sess_value)

        user.name_first = name_first
        user.name_last = name_last
        user.email = email
        # updateしないまま渡す

        return templates.TemplateResponse("edit_supporter_info.html",
                                          {"request": request, "user": user, "errors": errors,
                                           "csrf_token": _csrf_token})

    # ユーザー更新
    user_crud.update_user(
        user,
        {
            "name_first": name_first,
            "name_last": name_last,
            "email": email,
        }
    )
    return RedirectResponse(url="/?success=edit_supporter_info", status_code=status.HTTP_303_SEE_OTHER)
