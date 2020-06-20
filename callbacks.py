from bot_commands import Command
from nio import (
    JoinError,
)
from message_responses import Message

import logging
logger = logging.getLogger(__name__)


class Callbacks(object):

    def __init__(self, client, store, config):
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

    async def message(self, room, event):
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

        # process each line as separate message
        messages = msg.split("\n\n")

        for splitmessage in messages:
            # Process as message if in a public room without command prefix
            has_command_prefix = splitmessage.startswith(self.command_prefix)
            if not has_command_prefix and not room.is_group:
                # General message listener
                message = Message(self.client, self.store, self.config, splitmessage, room, event)
                await message.process()
                continue

            # Otherwise if this is in a 1-1 with the bot or features a command prefix,
            # treat it as a command
            if has_command_prefix:
                # Remove the command prefix
                splitmessage = splitmessage[len(self.command_prefix):]

            if splitmessage:
                command = Command(self.client, self.store, self.config, splitmessage, room, event)
                await command.process()

    async def invite(self, room, event):
        """Callback for when an invite is received. Join the room specified in the invite"""
        logger.debug(f"Got invite to {room.room_id} from {event.sender}.")

        if event.sender in self.config.botmasters:
            # Attempt to join 3 times before giving up
            for attempt in range(3):
                result = await self.client.join(room.room_id)
                if type(result) == JoinError:
                    logger.error(
                        f"Error joining room {room.room_id} (attempt %d): %s",
                        attempt, result.message,
                    )
                else:
                    logger.info(f"Joined {room.room_id}")
                    break
