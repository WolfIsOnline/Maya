import re
import asyncio
import json
import discord
from discord.ext import commands

from maya.core.api import API
from maya.core.logs import log


class ColorSelect(discord.ui.View):
    """Color view selector"""

    def __init__(self, color_roles: dict):
        super().__init__(timeout=None)
        self.color_roles = color_roles
        self.custom_id = "color_select_view"
        self.add_item(self.select_menu())

    def select_menu(self):
        """The select menu

        Returns:
            discord.ui.Select: select object (discord component)
        """
        select = discord.ui.Select(
            custom_id="color_select_dropdown",
            placeholder="Choose a color role",
            options=[
                discord.SelectOption(label=name) for name in self.color_roles.keys()
            ],
            min_values=1,
            max_values=1,
        )
        select.callback = self.select_callback
        return select

    async def select_callback(self, interaction: discord.Interaction):
        """Triggered when an option is selected

        Args:
            interaction (discord.Interaction): Interaction object
        """
        selected_color = interaction.data["values"][0]
        new_role = self.color_roles[selected_color]
        member = interaction.user

        current_color_roles = [
            role for role in member.roles if role in self.color_roles.values()
        ]
        if current_color_roles:
            await member.remove_roles(
                *current_color_roles, reason="Updating color role"
            )

        await member.add_roles(new_role, reason="Assigned color role")
        await interaction.response.send_message(
            f"Assigned {selected_color} role!", ephemeral=True
        )


class ColorsModal(discord.ui.Modal):
    """Color setup modal

    Args:
        discord.ui.Modal: modal object (discord component)
    """

    def __init__(self, api: API, channel: discord.TextChannel):
        super().__init__(title="Create Color Roles")
        self.api = api
        self.channel = channel

        self.add_item(
            discord.ui.InputText(
                label="Colors (name: hex, one per line)",
                placeholder="Red: #FF0000\nBlue: #0000FF\nGreen: #00FF00",
                style=discord.InputTextStyle.paragraph,
                required=True,
                max_length=1000,
            )
        )

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        colors_input = self.children[0].value
        channel = self.channel

        color_lines = [
            line.strip() for line in colors_input.split("\n") if line.strip()
        ]
        if len(color_lines) < 1:
            await interaction.response.send_message(
                "Error: At least one color must be provided!", ephemeral=True
            )
            return
        if len(color_lines) > 25:
            await interaction.response.send_message(
                "Error: Cannot have more than 25 colors!", ephemeral=True
            )
            return

        color_roles = {}
        for line in color_lines:
            match = re.match(r"^(.+?)\s*:\s*#?([0-9A-Fa-f]{6})$", line)
            if not match:
                await interaction.response.send_message(
                    f"Error: Invalid format for '{line}'. Use 'Name: #RRGGBB'!",
                    ephemeral=True,
                )
                return
            name, hex_code = match.groups()
            name = name.strip()
            if len(name) > 100:
                await interaction.response.send_message(
                    f"Error: Color name '{name}' exceeds 100 characters!",
                    ephemeral=True,
                )
                return
            if name in color_roles:
                await interaction.response.send_message(
                    f"Error: Duplicate color name '{name}'!", ephemeral=True
                )
                return

            try:
                hex_value = int(hex_code, 16)
            except ValueError:
                await interaction.response.send_message(
                    f"Error: Invalid hex code '#{hex_code}' for '{name}'!",
                    ephemeral=True,
                )
                return

            role_name = name
            role = discord.utils.get(guild.roles, name=role_name)
            if not role:
                role = await guild.create_role(
                    name=role_name,
                    color=discord.Color(hex_value),
                    permissions=discord.Permissions.none(),
                    reason="Created for color role system",
                )
            color_roles[name] = role

        color_roles_data = {name: role.id for name, role in color_roles.items()}
        color_data = {
            "color_channel_id": channel.id,
            "color_roles": color_roles_data,
        }

        embed = discord.Embed(
            title="Choose Your Color Role",
            description="Select a color from the dropdown to get a colored role!",
            color=discord.Color.blurple(),
        )
        embed.add_field(
            name="Available Colors",
            value="\n".join([f"<@&{role.id}>" for role in color_roles.values()]),
            inline=False,
        )
        view = ColorSelect(color_roles)
        message = await channel.send(embed=embed, view=view)

        color_data["color_message_id"] = message.id

        try:
            self.api.set_guild_data(
                guild_id=guild.id,
                endpoint="color-channel",
                value=color_data,
            )
        # pylint: disable=W0718
        except Exception as e:
            await interaction.response.send_message(
                f"Error: Failed to save color data: {str(e)}", ephemeral=True
            )
            return

        await interaction.response.send_message(
            f"Color roles created in <#{channel.id}>", ephemeral=True
        )


class Colors(commands.Cog):
    """Handles listeners, commands and restore process"""

    def __init__(self, bot):
        self.bot = bot
        self.api = API()
        self._restored = False
        self._lock = asyncio.Lock()

    @commands.Cog.listener()
    async def on_ready(self):
        """Triggers when bot is ready. Including on FULL bot restarts"""
        await self.bot.wait_until_ready()
        if not self._restored:
            await self.restore_colors()
            self._restored = True

    @commands.Cog.listener()
    async def on_resumed(self):
        """Triggered when bot doesn't restart, but reconnects to discord"""
        log.info("Session resumed, ensuring color views are restored")
        self._restored = False
        await self.restore_colors()

    async def restore_colors(self):
        """Restore the color view on all guilds"""
        async with self._lock:
            if self._restored:
                log.debug("Color views already restored, skipping")
                return

            log.info("Restoring color views for all guilds")
            for guild in self.bot.guilds:
                log.debug("Processing guild %s", guild.id)
                try:
                    color_data = self.api.get_guild_data(
                        guild_id=guild.id,
                        endpoint="color-channel",
                        data=None,
                    )

                    if not color_data:
                        log.debug("No color data found for guild %s", guild.id)
                        continue

                    log.debug("Raw color_data for guild %s: %s", guild.id, color_data)

                    if not isinstance(color_data, dict):
                        log.debug(
                            "Invalid color_data type for guild %s: %s",
                            guild.id,
                            type(color_data),
                        )
                        continue

                    channel_id = color_data.get("color_channel_id")
                    message_id = color_data.get("color_message_id")
                    color_roles_data = color_data.get("color_roles")

                    if isinstance(color_roles_data, str):
                        try:
                            color_roles_data = json.loads(color_roles_data)
                        except json.JSONDecodeError as e:
                            log.error(
                                "Failed to parse color_roles_data for guild %s: %s",
                                guild.id,
                                str(e),
                            )
                            continue

                    if not isinstance(color_roles_data, dict):
                        log.debug(
                            "Invalid color_roles_data type for guild %s: %s",
                            guild.id,
                            type(color_roles_data),
                        )
                        try:
                            self.api.set_guild_data(
                                guild_id=guild.id,
                                endpoint="color-channel",
                                value={
                                    "color_channel_id": None,
                                    "color_message_id": None,
                                    "color_roles": None,
                                },
                            )
                            log.info(
                                "Cleared invalid color data for guild %s", guild.id
                            )
                        # pylint: disable=W0718
                        except Exception as e:
                            log.error(
                                "Failed to clear color data for guild %s: %s",
                                guild.id,
                                str(e),
                            )
                        continue

                    if not channel_id or not message_id or not color_roles_data:
                        log.debug(
                            "Incomplete color data for guild %s: %s",
                            guild.id,
                            color_data,
                        )
                        continue

                    color_roles = {}
                    for name, role_id in color_roles_data.items():
                        role = guild.get_role(role_id)
                        if role:
                            color_roles[name] = role
                        else:
                            log.debug(
                                "Role %s not found in guild %s", role_id, guild.id
                            )

                    if not color_roles:
                        log.debug("No valid roles found for guild %s", guild.id)
                        try:
                            self.api.set_guild_data(
                                guild_id=guild.id,
                                endpoint="color-channel",
                                value={
                                    "color_channel_id": None,
                                    "color_message_id": None,
                                    "color_roles": None,
                                },
                            )
                            log.info(
                                "Cleared outdated color data (no valid roles) for guild %s",
                                guild.id,
                            )
                        # pylint: disable=W0718
                        except Exception as e:
                            log.error(
                                "Failed to clear color data for guild %s: %s",
                                guild.id,
                                str(e),
                            )
                        continue

                    channel = guild.get_channel(channel_id)
                    if not channel:
                        log.debug(
                            "Channel %s not found in guild %s", channel_id, guild.id
                        )
                        try:
                            self.api.set_guild_data(
                                guild_id=guild.id,
                                endpoint="color-channel",
                                value={
                                    "color_channel_id": None,
                                    "color_message_id": None,
                                    "color_roles": None,
                                },
                            )
                            log.info(
                                "Cleared outdated color data for guild %s", guild.id
                            )
                        # pylint: disable=W0718
                        except Exception as e:
                            log.error(
                                "Failed to clear color data for guild %s: %s",
                                guild.id,
                                str(e),
                            )
                        continue

                    try:
                        message = await channel.fetch_message(message_id)
                    except discord.NotFound:
                        log.debug(
                            "Message %s not found in channel %s, guild %s",
                            message_id,
                            channel_id,
                            guild.id,
                        )
                        try:
                            self.api.set_guild_data(
                                guild_id=guild.id,
                                endpoint="color-channel",
                                value={
                                    "color_channel_id": None,
                                    "color_message_id": None,
                                    "color_roles": None,
                                },
                            )
                            log.info(
                                "Cleared outdated color data for guild %s", guild.id
                            )
                        # pylint: disable=W0718
                        except Exception as e:
                            log.error(
                                "Failed to clear color data for guild %s: %s",
                                guild.id,
                                str(e),
                            )
                        continue
                    except discord.HTTPException as e:
                        log.error(
                            "Failed to fetch message %s in guild %s: %s",
                            message_id,
                            guild.id,
                            str(e),
                        )
                        continue

                    view = ColorSelect(color_roles)
                    self.bot.add_view(view, message_id=message.id)
                    log.info(
                        "Successfully registered view for message %s in guild %s",
                        message.id,
                        guild.id,
                    )
                # pylint: disable=W0718
                except Exception as e:
                    log.error(
                        "Failed to register view for guild %s: %s", guild.id, str(e)
                    )

                # Delay to avoid Discord rate limits
                await asyncio.sleep(0.5)

            self._restored = True

    @commands.slash_command(description="Create color roles")
    @commands.has_permissions(administrator=True)
    async def colorroles(self, ctx: discord.ApplicationContext):
        """Create color roles

        Args:
            ctx (discord.ApplicationContext): context application
        """
        modal = ColorsModal(self.api, ctx.channel)
        await ctx.interaction.response.send_modal(modal)


def setup(bot):
    bot.add_cog(Colors(bot))
