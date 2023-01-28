import logging
import os
import sys

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

sys.path.append("/user_modules")
from db.cruds import session as session_crud, user as user_crud

logging.basicConfig(level=logging.INFO)

router = APIRouter(
    prefix="/oauth2/discord",
    tags=["Discord OAuth2"]
)


def tokenize(code: str) -> str | None | bool:
    response = httpx.post(
        "https://discord.com/api/oauth2/token",
        data={
            "client_id": os.getenv("DISCORD_CLIENT_ID"),
            "client_secret": os.getenv("DISCORD_CLIENT_SECRET"),
            "redirect_uri": os.getenv("DISCORD_REDIRECT_URI"),
            "grant_type": "authorization_code",
            "code": code
        },
    )

    if response.status_code == 200 and "access_token" in response.json():
        return response.json()["access_token"]

    if "error" in response.json():
        if response.json()["error"] == "invalid_grant":
            return False

    logging.warning(response.json())
    return None


def get_user_data(token: str) -> dict[str, str] | None:
    response = httpx.get(
        "https://discord.com/api/users/@me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    return response.json()


def join_guild(
        token: str,
        user_id: str,
        guild_id: str = os.getenv("DISCORD_GUILD_ID"),
        nick: str = None,
        roles: list[str] | None = None
):
    response = httpx.put(
        f"https://discord.com/api/guilds/{guild_id}/members/{user_id}",
        json={
            "nick": nick,
            "roles": roles,
            "access_token": token
        },
        headers={
            "Authorization": f"Bot {os.getenv('DISCORD_BOT_TOKEN')}",
            "Content-Type": "application/json",
        }
    )

    if response.status_code in (201, 204):
        logging.info("Added user to guild.")
        return True
    else:
        return False


@router.get("/")
def start_auth():
    return RedirectResponse(
        f"https://discord.com/api/oauth2/authorize?client_id={os.getenv('DISCORD_CLIENT_ID')}"
        f"&redirect_uri={os.getenv('DISCORD_REDIRECT_URI')}&response_type=code&scope=identify email guilds.join"
    )


@router.get("/callback")
def callback(request: Request, code: str):
    # codeをtokenに変換
    token = tokenize(code)
    if token is None:
        return RedirectResponse("/?error=failed_to_get_token&location=Discord")
    if token is False:
        return RedirectResponse("/?error=code_is_invalid&location=Discord")

    # Discordのユーザー情報を取得
    discord_user = get_user_data(token)
    if discord_user is None:
        return RedirectResponse("/?error=failed_to_get_data&location=Discord")
    discord_id = discord_user["id"]
    discord_name = discord_user["username"] + "#" + discord_user["discriminator"]
    email = discord_user["email"]
    avatar_hash = discord_user["avatar"]

    # sessに保存されている情報を取得
    sess_value = request.state.session.get_value(none_if_not_exist=False)

    # user_idがsessに保存されている = 一度は連携済みDiscordでログイン済み
    # ==> Discordアカウントを更新する
    if "user_id" in sess_value:
        user = user_crud.get_user(sess_value["user_id"])

        # user_idが間違っていたらセッションを破棄
        if user is None:
            return RedirectResponse("/logout")

        user_crud.update_user(
            user,
            {
                "discord_user_id": discord_id,
                "discord_user_name": discord_name,
                "discord_avatar_hash": avatar_hash,
            }
        )

        # 新しいアカウントをDiscordに参加
        join_guild(
            token=token,
            user_id=discord_id,
            roles=[os.getenv("DISCORD_SUPPORTER_ROLE")] if user.is_supporter else [os.getenv("DISCORD_MEMBER_ROLE")]
        )

    # user_idがsessに保存されていない = これまでログインしていない
    else:
        # Discordアカウントが既に登録済み = 既存アカウントを取得してsessに保存
        user = user_crud.get_user_by_discord_user_id(int(discord_id))
        if user is not None:
            sess_value["user_id"] = user.id
        # Discordアカウントが未登録 = 新しくアカウントを作成してidをsessに保存
        else:
            registered_email = None
            is_supporter = False
            if sess_value is not None:
                if "registered_email" in sess_value:
                    registered_email = sess_value["registered_email"]
                    email = registered_email
                if "is_supporter" in sess_value:
                    is_supporter = sess_value["is_supporter"]

            user = user_crud.create_user_from_discord(
                discord_user_id=int(discord_id),
                discord_user_name=discord_name,
                discord_avatar_hash=avatar_hash,
                email=email,
                registered_email=registered_email,
                is_supporter=is_supporter
            )
            sess_value["user_id"] = user.id

            # Discordに参加
            join_guild(
                token=token,
                user_id=discord_id,
                roles=[os.getenv("DISCORD_SUPPORTER_ROLE")] if is_supporter else [os.getenv("DISCORD_MEMBER_ROLE")]
            )

    # sessを更新
    session_crud.update_session(request.state.session.id, sess_value)

    # リダイレクト
    return RedirectResponse("/?success=oauth2&location=Discord")
