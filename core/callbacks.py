from core.bot_commands import Command
from nio import (
    JoinError, MatrixRoom, UnknownEvent, InviteEvent, RoomMessageText
)

import logging

from core.pluginloader import PluginLoader

logger = logging.getLogger(__name__)


class Callbacks(object):

    def __init__(self, client, store, config, plugin_loader):
        """
        Args:
            client (nio.AsyncClient): nio client used to interact with matrix

            store (Storage): Bot storage

            config (Config): Bot configuration parameters
        """
        self.client = client
        self.store = store
        self.config = config
        self.command_prefix = config.command_prefix
        self.plugin_loader: PluginLoader = plugin_loader

    async def message(self, room: MatrixRoom, event: RoomMessageText):
        """Callback for when a message event is received

        Args:
            room (nio.rooms.MatrixRoom): The room the event came from

            event (nio.events.room_events.RoomMessageText): The event defining the message

        """
        # Extract the message text
        msg = event.body

        # Ignore messages from ourselves
        if event.sender == self.client.user:
            return

        logger.debug(
            f"Bot message received for room {room.display_name} | "
            f"{room.user_name(event.sender)}: {msg}"
        )

        # process each line as separate message to check for commands
        messages = msg.split("\n\n")
        for split_message in messages:
            # Process as message if in a public room without command prefix
            has_command_prefix = split_message.startswith(self.command_prefix)
            if not has_command_prefix and not room.is_group:
                await self.plugin_loader.run_hooks(self.client, "m.room.message", room, event)
                continue

            # Otherwise if this is in a 1-1 with the bot or features a command prefix,
            # treat it as a command
            if has_command_prefix:
                # Remove the command prefix
                split_message = split_message[len(self.command_prefix):]
                # remove leading spaces
                split_message = split_message.lstrip()

            if split_message != "":
                command = Command(self.client, self.store, self.config, split_message, room, event, self.plugin_loader)
                await self.plugin_loader.run_command(command)

    async def event_unknown(self, room: MatrixRoom, event: UnknownEvent):
        """
        Handles events that are not yet known to matrix-nio (might change or break on updates)
        :param room: nio.rooms.MatrixRoom: the room the event came from
        :param event: nio.events.room_events.RoomMessage: The event defining the message
        :return:
        """

        # Ignore messages from ourselves
        if event.sender == self.client.user:
            return

        if event.type == "m.reaction":
            await self.plugin_loader.run_hooks(self.client, event.type, room, event)

    async def invite(self, room: MatrixRoom, event: InviteEvent):
        """Callback for when an invite is received. Join the room specified in the invite"""
        logger.info(f"Got invite to {room.room_id} from {event.sender}.")

        # Only join when inviter is botmaster, botmasters are empty or room is DM
        if self.config.botmasters == [] or event.sender in self.config.botmasters or room.is_group:

            result = await self.client.join(room.room_id)
            if type(result) == JoinError:
                logger.error(f"Error joining room {room.room_id}: {result.message}")
            else:
                logger.info(f"Joined {room.room_id}")

            # room.is_group is not reliable before joining, verify:
            if not room.is_group or room.member_count > 2:
                # room is not a DM, check if we have been invited by botmaster or botmasters empty
                if not self.config.botmasters == [] and event.sender not in self.config.botmasters:
                    logger.warning(f"Leaving {room.display_name} ({room.room_id}) due to unauthorised invite.")
                    await self.client.room_leave(room.room_id)

        else:
            logger.warning(f"Rejecting invite to {room.display_name} ({room.room_id}) due to unauthorised invite.")
            await self.client.room_leave(room.room_id)
