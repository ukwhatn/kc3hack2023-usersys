import logging
import re

from fastapi import APIRouter, Request, Form, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from cruds import session as session_crud
from cruds import user as user_crud

logging.basicConfig(level=logging.INFO)

router = APIRouter(
    prefix="/user",
    tags=["User"]
)

templates = Jinja2Templates(directory="templates")


@router.get("/info")
def edit_user_data(request: Request):
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

    # CORSトークン生成・セッションに保存
    csrf_token = session_crud.create_csrf_token()
    sess_value["csrf_token"] = csrf_token
    session_crud.update_session(request.state.session.id, sess_value)

    return templates.TemplateResponse("edit_user_info.html",
                                      {"request": request, "user": user, "csrf_token": csrf_token, "errors": None})


@router.post("/info")
def post_user_info(
        request: Request,
        _csrf_token: str = Form(None),
        name_first: str = Form(None),
        name_last: str = Form(None),
        name_first_kana: str = Form(None),
        name_last_kana: str = Form(None),
        email: str = Form(None),
        univ_name: str = Form(None),
        univ_year: int = Form(None),
        circle_name: str = Form(None)
):
    # CSRFチェック
    sess_value = request.state.session.get_value()
    if sess_value is None or "csrf_token" not in sess_value \
            or sess_value["csrf_token"] != _csrf_token or _csrf_token is None:
        return RedirectResponse(url="/user/info", status_code=status.HTTP_303_SEE_OTHER)

    # 未ログインならポータルにリダイレクト
    if sess_value is None or "user_id" not in sess_value:
        return RedirectResponse(url="/?error=unauthorized")

    # ユーザー取得
    user = user_crud.get_user(sess_value["user_id"])

    # ユーザーが存在しないならセッションを破棄してリダイレクト
    if user is None:
        return RedirectResponse(url="/logout", status_code=status.HTTP_303_SEE_OTHER)

    # バリデーションチェック
    is_valid = True
    errors = []

    regex_katakana = re.compile(r"[\u30A0-\u30FF]+")
    regex_email = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

    if name_first is None or len(name_first) == 0 or name_last is None or len(name_last) == 0:
        is_valid = False
        errors.append("氏名を入力してください")

    if name_first_kana is None or len(name_first_kana) == 0 or name_last_kana is None or len(name_last_kana) == 0:
        is_valid = False
        errors.append("氏名(フリガナ)を入力してください")
    elif not regex_katakana.fullmatch(name_first_kana) or not regex_katakana.fullmatch(name_last_kana):
        is_valid = False
        errors.append("氏名(フリガナ)はカタカナで入力してください")

    if email is None or len(email) == 0:
        is_valid = False
        errors.append("メールアドレスを入力してください")
    elif not regex_email.fullmatch(email):
        is_valid = False
        errors.append("メールアドレスの形式が正しくありません")

    if univ_name is None or len(univ_name) == 0:
        is_valid = False
        errors.append("大学名を入力してください")

    if univ_year is None or univ_year < 1 or univ_year > 4:
        is_valid = False
        errors.append("学年を選択してください")

    if circle_name is None or len(circle_name) == 0:
        is_valid = False
        errors.append("サークル名を入力してください")

    if not is_valid:
        _csrf_token = session_crud.create_csrf_token()
        sess_value["csrf_token"] = _csrf_token
        session_crud.update_session(request.state.session.id, sess_value)

        user.name_first = name_first
        user.name_last = name_last
        user.name_first_kana = name_first_kana
        user.name_last_kana = name_last_kana
        user.email = email
        user.univ_name = univ_name
        user.univ_year = univ_year
        user.circle_name = circle_name
        # updateしないまま渡す

        return templates.TemplateResponse("edit_user_info.html",
                                          {"request": request, "user": user, "errors": errors,
                                           "csrf_token": _csrf_token})

    # ユーザー更新
    user_crud.update_user(
        user,
        {
            "name_first": name_first,
            "name_last": name_last,
            "name_first_kana": name_first_kana,
            "name_last_kana": name_last_kana,
            "email": email,
            "univ_name": univ_name,
            "univ_year": univ_year,
            "circle_name": circle_name
        }
    )
    return RedirectResponse(url="/?success=edit_user_info", status_code=status.HTTP_303_SEE_OTHER)
