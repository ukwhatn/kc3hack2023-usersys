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

    @commands.Cog.listener("on_ready")
    async def on_ready(self):
        self.guild = self.bot.get_guild(int(os.getenv("DISCORD_GUILD_ID")))
        self.update_users.start()

    @staticmethod
    def get_all_users_in_db() -> list[Users]:
        return user_crud.get_users()

    async def add_role(self, member: discord.Member, role: discord.Role):
        if role not in member.roles:
            await member.add_roles(role)
            self.logger.info(f"Added {member.name} to {role.name}")

    @tasks.loop(minutes=1)
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

            if member.is_supporter:
                continue

            if member.discord_user_id is not None:
                discord_user = await self.guild.fetch_member(member.discord_user_id)
                if discord_user is not None and not discord_user.bot:

                    if member.name_first is None or member.name_last is None:
                        await self.add_role(
                            discord_user,
                            self.guild.get_role(int(os.getenv("DISCORD_NOT_REGISTERED_ROLE")))
                        )
                        correct_user_nane = None

                    else:
                        correct_user_nane = f"{member.name_first} {member.name_last}"

                    if member.is_admin:
                        correct_user_nane += "_KC3運営"

                    if member.is_supporter:
                        await self.add_role(
                            discord_user,
                            self.guild.get_role(int(os.getenv("DISCORD_SUPPORTER_ROLE")))
                        )

                    if correct_user_nane is not None and discord_user.nick != correct_user_nane:
                        await discord_user.edit(nick=correct_user_nane)
                        logging.info(f"Updated {discord_user.name}'s nickname to {correct_user_nane}")

                    if member.team_id is not None:
                        team_name = f"チーム{member.team_id}"

                        is_correct_team_role_exist = False

                        for exist_role in discord_user.roles:
                            if exist_role.name in roles:
                                if exist_role.name != team_name:
                                    await discord_user.remove_roles(exist_role)
                                    logging.info(f"Removed {exist_role.name} from {discord_user.name}")
                                else:
                                    is_correct_team_role_exist = True

                        if not is_correct_team_role_exist:
                            await self.add_role(discord_user, roles[team_name])

                else:
                    await bot_config.NOTIFY_TO_OWNER(
                        self.bot,
                        f"User {member.name_first} {member.name_last} is not in the server")

        members_discord_id = [member.discord_user_id for member in members]
        for discord_user in self.guild.members:
            if discord_user.bot:
                continue
            if discord_user.id not in members_discord_id:
                if self.guild.owner.id != discord_user.id:
                    await discord_user.kick(reason="Not registered")
                    self.logger.info(f"Kicked {discord_user.name}")


def setup(bot):
    return bot.add_cog(UserManage(bot))
