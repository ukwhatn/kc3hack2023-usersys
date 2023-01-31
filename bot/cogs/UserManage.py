import logging
import os
import sys

import discord
from discord.ext import commands, tasks

sys.path.append("/user_modules")
from db.cruds import user as user_crud
from db.models import Users

from config import bot_config


class UserManage(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

        self.guild = None

        self.notified_not_found_users = []

        self.kick_targets = {}

    @commands.Cog.listener("on_ready")
    async def on_ready(self):
        self.guild = self.bot.get_guild(int(os.getenv("DISCORD_GUILD_ID")))
        self.update_users.start()

    @commands.Cog.listener("on_member_join")
    async def on_member_join(self, member: discord.Member):
        if member.bot:
            return

        dm = await member.create_dm()
        try:
            await dm.send(
                content="",
                embed=discord.Embed(
                    title="KC3Hack 2023へようこそ！",
                    description="まずは、「はじめに」チャンネルを確認してください。"
                )
            )
        except discord.Forbidden:
            self.logger.warning(f"Failed to send DM to {member.name}")

    @staticmethod
    def get_all_users_in_db() -> list[Users]:
        return user_crud.get_users()

    async def add_role(self, member: discord.Member, role: discord.Role):
        if role not in member.roles:
            await member.add_roles(role)
            self.logger.info(f"Added {member.name} to {role.name}")

    async def remove_role(self, member: discord.Member, role: discord.Role):
        if role in member.roles:
            await member.remove_roles(role)
            self.logger.info(f"Removed {member.name} from {role.name}")

    @tasks.loop(seconds=15)
    async def update_users(self):

        if self.guild is None:
            return

        members = self.get_all_users_in_db()

        # ロールストア
        roles = {}
        for role in self.guild.roles:
            if "チーム" in role.name:
                roles.update({role.name: role})

        for member in members:

            if member.discord_user_id is not None:
                try:
                    discord_user = await self.guild.fetch_member(member.discord_user_id)
                except discord.NotFound:
                    discord_user = None

                if discord_user is not None and not discord_user.bot:

                    # check manage
                    is_manage = False
                    manage_role = self.guild.get_role(int(os.getenv("DISCORD_MANAGE_ROLE")))
                    if member.is_admin:
                        is_manage = True
                        await self.add_role(
                            discord_user,
                            manage_role
                        )
                    else:
                        await self.remove_role(
                            discord_user,
                            manage_role
                        )

                    # check supporter
                    supporter_role = self.guild.get_role(int(os.getenv("DISCORD_SUPPORTER_ROLE")))
                    member_role = self.guild.get_role(int(os.getenv("DISCORD_MEMBER_ROLE")))
                    is_supporter = False
                    if member.is_supporter:
                        is_supporter = True
                        await self.add_role(
                            discord_user,
                            supporter_role
                        )
                        await self.remove_role(
                            discord_user,
                            member_role
                        )
                    else:
                        await self.remove_role(
                            discord_user,
                            supporter_role
                        )
                        if not is_manage:
                            await self.add_role(
                                discord_user,
                                member_role
                            )
                        else:
                            await self.remove_role(
                                discord_user,
                                member_role
                            )

                    # 詳細情報登録チェック
                    has_detailed_info = True
                    has_not_detailed_role = self.guild.get_role(int(os.getenv("DISCORD_NOT_REGISTERED_ROLE")))
                    if (member.name_first is None or member.name_last is None) and not member.is_supporter:
                        has_detailed_info = False
                        await self.add_role(
                            discord_user,
                            has_not_detailed_role
                        )
                    else:
                        await self.remove_role(
                            discord_user,
                            has_not_detailed_role
                        )

                    # GitHub登録チェック
                    is_not_github_registered_role = self.guild.get_role(
                        int(os.getenv("DISCORD_NOT_GITHUB_REGISTERED_ROLE")))
                    if member.github_user_id is None and not member.is_supporter:
                        await self.add_role(
                            discord_user,
                            is_not_github_registered_role
                        )
                    else:
                        await self.remove_role(
                            discord_user,
                            is_not_github_registered_role
                        )

                    # チームIDチェック
                    has_team_id = False
                    if member.team_id is not None:
                        has_team_id = True

                    # nickname構築
                    nickname = ""

                    if not is_supporter:
                        if has_detailed_info:
                            nickname += f"{member.name_first} {member.name_last}"
                        else:
                            nickname += f"{discord_user.name}_未登録"

                        if is_manage:
                            nickname += "_KC3運営"

                        if has_team_id:
                            nickname += f"_チーム{member.team_id}"

                        if discord_user.nick != nickname:
                            await discord_user.edit(nick=nickname)
                            logging.info(f"Updated {discord_user.name}'s nickname to {nickname}")

                    # チームロール付与処理
                    if member.team_id is not None:
                        team_role_name = f"チーム{member.team_id}"
                        is_correct_team_role_exist = False

                        for exist_role in discord_user.roles:
                            if exist_role.name in roles:
                                if exist_role.name != team_role_name:
                                    await discord_user.remove_roles(exist_role)
                                    logging.info(f"Removed {exist_role.name} from {discord_user.name}")
                                else:
                                    is_correct_team_role_exist = True

                        if not is_correct_team_role_exist:
                            await self.add_role(discord_user, roles[team_role_name])

                    else:
                        for exist_role in discord_user.roles:
                            if exist_role.name in roles:
                                await discord_user.remove_roles(exist_role)
                                logging.info(f"Removed {exist_role.name} from {discord_user.name}")

                else:
                    if member.id not in self.notified_not_found_users:
                        # ユーザーがサーバーにいない場合は通知
                        await bot_config.NOTIFY_TO_OWNER(
                            self.bot,
                            f"User {member.name_first} {member.name_last} "
                            f"({member.discord_user_name}) is not in the server")
                        self.notified_not_found_users.append(member.id)

        # サーバーにいるがDBに登録されていないユーザーをキック
        members_discord_id = [member.discord_user_id for member in members]
        for discord_user in self.guild.members:
            if discord_user.bot:
                continue
            if discord_user.id not in members_discord_id:
                if self.guild.owner.id != discord_user.id:
                    if discord_user.id not in self.kick_targets:
                        self.kick_targets[discord_user.id] = 1
                    else:
                        self.kick_targets[discord_user.id] += 1

                    if self.kick_targets[discord_user.id] >= 4:
                        await discord_user.kick(reason="Not registered")
                        self.logger.info(f"Kicked {discord_user.name}")
                        self.kick_targets.pop(discord_user.id)
                    else:
                        self.logger.info(
                            f"Will kick {discord_user.name} in {4 - self.kick_targets[discord_user.id]} times")


def setup(bot):
    return bot.add_cog(UserManage(bot))
