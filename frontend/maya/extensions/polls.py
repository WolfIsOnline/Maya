import datetime
import re
from collections import defaultdict

import discord
from discord.ext import commands


class PollModal(discord.ui.Modal):
    """Poll Modal setup"""

    def __init__(self):
        super().__init__(title="Create a Poll")

        self.add_item(
            discord.ui.InputText(
                label="Poll Question",
                placeholder="Enter the poll question",
                style=discord.InputTextStyle.short,
                required=True,
                max_length=100,
            )
        )
        self.add_item(
            discord.ui.InputText(
                label="Options (one per line)",
                placeholder="Option 1\nOption 2\nOption 3",
                style=discord.InputTextStyle.paragraph,
                required=True,
                max_length=1000,
            )
        )
        self.add_item(
            discord.ui.InputText(
                label="Allow Multiple Selections? (yes/no)",
                placeholder="no",
                style=discord.InputTextStyle.short,
                required=False,
                max_length=3,
            )
        )
        self.add_item(
            discord.ui.InputText(
                label="Poll Duration (e.g., 30m, 11h, 3d)",
                placeholder="Enter duration (e.g., 30m for minutes, 11h for hours, 3d for days)",
                style=discord.InputTextStyle.short,
                required=True,
                max_length=10,
            )
        )

    async def callback(self, interaction: discord.Interaction):
        question = self.children[0].value
        options_input = self.children[1].value
        allow_multiple = (
            self.children[2].value.lower() in ("yes", "y")
            if self.children[2].value
            else False
        )
        duration_input = self.children[3].value.lower()

        match = re.match(r"^(\d+)([mhd])$", duration_input)
        if not match:
            await interaction.response.send_message(
                "Error: Duration must be a number followed by m, h, or d (e.g., 30m, 11h, 3d)!",
                ephemeral=True,
            )
            return
        number = int(match.group(1))
        unit = match.group(2)
        if unit == "m":
            duration = number * 60
        elif unit == "h":
            duration = number * 3600
        else:
            duration = number * 86400

        if duration > 604800:
            await interaction.response.send_message(
                "Error: Duration cannot exceed 7 days!", ephemeral=True
            )
            return

        option_list = [opt.strip() for opt in options_input.split("\n") if opt.strip()]
        if len(option_list) < 2:
            await interaction.response.send_message(
                "Error: At least two options are required!", ephemeral=True
            )
            return
        if len(option_list) > 25:
            await interaction.response.send_message(
                "Error: Cannot have more than 25 options!", ephemeral=True
            )
            return
        if any(len(opt) > 100 for opt in option_list):
            await interaction.response.send_message(
                "Error: Each option must be 100 characters or less!", ephemeral=True
            )
            return

        select_options = [discord.SelectOption(label=opt) for opt in option_list]

        expiration = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
            seconds=duration
        )
        expiration_str = discord.utils.format_dt(expiration, style="R")

        view = AnonPolling(
            select_options, allow_multiple, duration, question, expiration
        )
        await interaction.response.send_message(
            f"**{question}**\nPoll ends: {expiration_str}", view=view, ephemeral=False
        )

    async def on_error(self, error: Exception, interaction: discord.Interaction):
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "An error occurred while processing the poll. Please try again.",
                ephemeral=True,
            )


class AnonPolling(discord.ui.View):
    def __init__(
        self,
        options,
        allow_multiple: bool,
        timeout: int,
        question: str,
        expiration: datetime.datetime,
    ):
        super().__init__(timeout=timeout)
        self.options = options
        self.question = question
        self.expiration = expiration
        self.votes = defaultdict(int)
        self.user_votes = {}
        self.add_item(self.create_select_menu(allow_multiple))

    def create_select_menu(self, allow_multiple: bool):
        """Select menu setup using discords built-in select menu

        Args:
            allow_multiple (bool): allow multiple options or not

        Returns:
            discord.ui.Select: the select object
        """
        select = discord.ui.Select(
            placeholder="Choose an option",
            min_values=1,
            max_values=len(self.options) if allow_multiple else 1,
            options=self.options,
        )
        select.callback = self.select_callback
        return select

    async def select_callback(self, interaction: discord.Interaction):
        """Runs when user selects an option

        Args:
            interaction (discord.Interaction): Interaction object
        """
        user_id = interaction.user.id
        selected_values = interaction.data["values"]

        if user_id in self.user_votes:
            for value in self.user_votes[user_id]:
                self.votes[value] -= 1

        for value in selected_values:
            self.votes[value] += 1

        self.user_votes[user_id] = selected_values

        await interaction.response.send_message(
            f"You selected: {', '.join(selected_values)}", ephemeral=True
        )

    async def on_timeout(self):
        """Called when vote is done/timed out"""
        for item in self.children:
            item.disabled = True
        expiration_str = discord.utils.format_dt(self.expiration, style="R")

        if not self.votes:
            results = "No votes were cast."
        else:
            max_votes = max(self.votes.values())
            winners = [opt for opt, count in self.votes.items() if count == max_votes]
            results = "\n".join(
                f"{opt}: {self.votes[opt]} vote(s)"
                for opt in [o.label for o in self.options]
            )
            results += f"\n**Winner(s)**: {', '.join(winners)} ({max_votes} vote(s))"

        await self.message.edit(
            content=f"**{self.question}**\nPoll closed: {expiration_str}\n\n**Results**:\n{results}",
            view=self,
        )


class Polls(commands.Cog):
    """Poll command"""

    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Create a poll")
    @commands.has_permissions(administrator=True)
    async def poll(self, ctx: discord.ApplicationContext):
        """Create a poll

        Args:
            ctx (discord.ApplicationContext): context application
        """
        modal = PollModal()
        await ctx.interaction.response.send_modal(modal)


def setup(bot):
    bot.add_cog(Polls(bot))
