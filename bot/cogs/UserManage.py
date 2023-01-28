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

    @tasks.loop(seconds=10)
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

            correct_user_nane = f"{member.name_first} {member.name_last}"
            if member.is_admin:
                correct_user_nane += "_KC3運営"

            if member.discord_user_id is not None:
                discord_user = await self.guild.fetch_member(member.discord_user_id)
                if discord_user is not None:
                    if discord_user.nick != correct_user_nane:
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
                            await discord_user.add_roles(roles[team_name])
                            logging.info(f"Added {team_name} to {discord_user.name}")

                else:
                    await bot_config.NOTIFY_TO_OWNER(
                        self.bot,
                        f"User {member.name_first} {member.name_last} is not in the server")


def setup(bot):
    return bot.add_cog(UserManage(bot))
