import datetime
import re
import json
import os
import fcntl
from collections import defaultdict

import discord
from discord.ext import commands, tasks
from maya.core.logs import log

POLL_FILE = "polls.json"


def lock_file(file_obj):
    """Lock a file using fcntl (Unix) or no-op on unsupported platforms."""
    try:
        fcntl.flock(file_obj.fileno(), fcntl.LOCK_EX)
    except (AttributeError, OSError):
        pass


def unlock_file(file_obj):
    """Unlock a file."""
    try:
        fcntl.flock(file_obj.fileno(), fcntl.LOCK_UN)
    except (AttributeError, OSError):
        pass


def load_polls():
    """Load poll data from JSON file with locking."""
    if os.path.exists(POLL_FILE):
        with open(POLL_FILE, "r", encoding="utf-8") as f:
            lock_file(f)
            try:
                return json.load(f)
            finally:
                unlock_file(f)
    return {}


def save_poll_data(
    message_id,
    channel_id,
    question,
    options,
    allow_multiple,
    expiration,
    votes,
    user_votes,
):
    """Save poll data to JSON file with locking."""
    polls = load_polls()
    polls[str(message_id)] = {
        "message_id": message_id,
        "channel_id": channel_id,
        "question": question,
        "options": options,
        "allow_multiple": allow_multiple,
        "expiration": expiration.isoformat(),
        "votes": dict(votes),
        "user_votes": {str(k): v for k, v in user_votes.items()},
    }
    with open(POLL_FILE, "w", encoding="utf-8") as f:
        lock_file(f)
        try:
            json.dump(polls, f, indent=2)
        except Exception as e:
            log.error("Failed to save polls to JSON: %s", str(e))
            raise
        finally:
            unlock_file(f)


def update_poll_votes(message_id, votes, user_votes):
    """Update votes in JSON file with locking."""
    polls = load_polls()
    if str(message_id) in polls:
        polls[str(message_id)]["votes"] = dict(votes)
        polls[str(message_id)]["user_votes"] = {
            str(k): v for k, v in user_votes.items()
        }
        with open(POLL_FILE, "w", encoding="utf-8") as f:
            lock_file(f)
            try:
                json.dump(polls, f, indent=2)
            except Exception as e:
                log.error("Failed to update poll votes in JSON: %s", str(e))
                raise
            finally:
                unlock_file(f)


def remove_poll_data(message_id):
    """Remove poll data from JSON file with locking."""
    polls = load_polls()
    if str(message_id) in polls:
        del polls[str(message_id)]
        with open(POLL_FILE, "w", encoding="utf-8") as f:
            lock_file(f)
            try:
                json.dump(polls, f, indent=2)
                log.info("Removed poll %s from JSON", message_id)
            except Exception as e:
                log.error("Failed to remove poll %s from JSON: %s", message_id, str(e))
                raise
            finally:
                unlock_file(f)


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
                placeholder="Enter duration (e.g., 30m, 11h, 3d)",
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
        duration = (
            number * 60
            if unit == "m"
            else number * 3600 if unit == "h" else number * 86400
        )

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
            f"**{question}**\nPoll ends: {expiration_str}\n\n**Total votes**: 0",
            view=view,
            ephemeral=False,
        )
        view.message = await interaction.original_response()

        save_poll_data(
            message_id=view.message.id,
            channel_id=interaction.channel_id,
            question=question,
            options=option_list,
            allow_multiple=allow_multiple,
            expiration=expiration,
            votes=view.votes,
            user_votes=view.user_votes,
        )

    async def on_error(self, error: Exception, interaction: discord.Interaction):
        log.error("PollModal error: %s", str(error))
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
        log.info("Initialized poll: %s, timeout: %ss", question, timeout)
        self.add_item(self.create_select_menu(allow_multiple))

    def create_select_menu(self, allow_multiple: bool):
        select = discord.ui.Select(
            placeholder="Choose an option",
            min_values=1,
            max_values=len(self.options) if allow_multiple else 1,
            options=self.options,
        )
        select.callback = self.select_callback
        return select

    async def select_callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        selected_values = interaction.data["values"]

        if user_id in self.user_votes:
            for value in self.user_votes[user_id]:
                self.votes[value] -= 1
        for value in selected_values:
            self.votes[value] += 1
        self.user_votes[user_id] = selected_values

        update_poll_votes(
            message_id=self.message.id if self.message else 0,
            votes=self.votes,
            user_votes=self.user_votes,
        )

        expiration_str = discord.utils.format_dt(self.expiration, style="R")
        total_votes = sum(self.votes.values())
        try:
            await self.message.edit(
                content=f"**{self.question}**\nPoll ends: {expiration_str}\n\n**Total votes**: {total_votes}",
                view=self,
            )
            log.info("Updated poll message with total votes for: %s", self.question)
        except Exception as e:
            log.error("Error updating poll message for %s: %s", self.question, str(e))

        await interaction.response.send_message(
            f"You selected: {', '.join(selected_values)}", ephemeral=True
        )

    async def on_timeout(self):
        log.info("Poll timeout triggered for: %s", self.question)
        for item in self.children:
            item.disabled = True
        expiration_str = discord.utils.format_dt(self.expiration, style="R")

        if not self.votes:
            results = "No votes were cast."
        else:
            max_votes = max(self.votes.values())
            winners = [opt for opt, count in self.votes.items() if count == max_votes]
            results = "\n".join(
                f"{opt}: {self.votes[opt]} votes"
                for opt in [o.label for o in self.options]
            )
            results += f"\n**Winners**: {', '.join(winners)} ({max_votes} votes)"

        try:
            await self.message.edit(
                content=f"**{self.question}**\nPoll closed: {expiration_str}\n\n**Results**:\n{results}",
                view=self,
            )
            remove_poll_data(self.message.id)
        except Exception as e:
            log.error("Error in on_timeout: %s", str(e))


class Polls(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_session_id = None
        self.invalid_polls = set()
        self.cleanup_polls.start()

    async def restore_polls(self, session_id: str):
        """Restore active polls after connect or resume."""
        log.info("Starting poll restoration for session: %s", session_id)
        polls = load_polls()
        now = datetime.datetime.now(datetime.timezone.utc)
        for poll_data in polls.values():
            expiration = datetime.datetime.fromisoformat(poll_data["expiration"])
            if expiration > now:
                timeout = (expiration - now).total_seconds()
                options = [
                    discord.SelectOption(label=opt) for opt in poll_data["options"]
                ]
                view = AnonPolling(
                    options=options,
                    allow_multiple=poll_data["allow_multiple"],
                    timeout=timeout,
                    question=poll_data["question"],
                    expiration=expiration,
                )
                view.votes = defaultdict(int, poll_data["votes"])
                view.user_votes = {
                    int(k): v for k, v in poll_data["user_votes"].items()
                }
                try:
                    channel = await self.bot.fetch_channel(poll_data["channel_id"])
                    message = await channel.fetch_message(poll_data["message_id"])
                    view.message = message
                    total_votes = sum(view.votes.values())
                    expiration_str = discord.utils.format_dt(expiration, style="R")
                    await message.edit(
                        content=f"**{poll_data['question']}**\nPoll ends: {expiration_str}\n\n**Total votes**: {total_votes}",
                        view=view,
                    )
                    log.info("Restored poll: %s", poll_data["question"])
                except (
                    discord.NotFound,
                    discord.Forbidden,
                    discord.HTTPException,
                ) as e:
                    log.error(
                        "Failed to restore poll %s (channel %s): %s",
                        poll_data["question"],
                        poll_data["channel_id"],
                        str(e),
                    )
                    self.invalid_polls.add(poll_data["message_id"])
                except Exception as e:
                    log.error(
                        "Unexpected error restoring poll %s: %s",
                        poll_data["question"],
                        str(e),
                    )
                    self.invalid_polls.add(poll_data["message_id"])
        log.info("Poll restoration complete")

    @tasks.loop(hours=1.0)
    async def cleanup_polls(self):
        """Periodically clean up invalid polls from JSON."""
        if not self.invalid_polls:
            return
        log.info("Cleaning up %s invalid polls", len(self.invalid_polls))
        for message_id in list(self.invalid_polls):
            try:
                remove_poll_data(message_id)
                self.invalid_polls.remove(message_id)
            except Exception as e:
                log.error("Failed to clean up poll %s: %s", message_id, str(e))

    @cleanup_polls.before_loop
    async def before_cleanup_polls(self):
        """Wait for bot to be ready before starting cleanup task."""
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_connect(self):
        """Restore polls on WebSocket connect."""
        session_id = getattr(self.bot, "session_id", "unknown")
        if session_id != self._last_session_id:
            await self.restore_polls(session_id)
            self._last_session_id = session_id

    @commands.Cog.listener()
    async def on_resumed(self):
        """Restore polls after WebSocket resume."""
        session_id = getattr(self.bot, "session_id", "unknown")
        log.info("Resumed session: %s", session_id)
        await self.restore_polls(session_id)

    @commands.slash_command(description="Create a poll")
    @commands.has_permissions(administrator=True)
    async def poll(self, ctx: discord.ApplicationContext):
        modal = PollModal()
        await ctx.response.send_modal(modal)


def setup(bot):
    bot.add_cog(Polls(bot))
