import logging

from nio import RoomMessageText

from pluginloader import PluginLoader

logger = logging.getLogger(__name__)


class Message(object):

    def __init__(self, client, store, config, message_content, room, event, plugin_loader):
        """Initialize a new Message

        Args:
            client (nio.AsyncClient): nio client used to interact with matrix

            store (Storage): Bot storage

            config (Config): Bot configuration parameters

            message_content (str): The body of the message

            room (nio.rooms.MatrixRoom): The room the event came from

            event (nio.events.room_events.RoomMessageText): The event defining the message
        """
        self.client = client
        self.store = store
        self.config = config
        self.message_content = message_content
        self.room = room
        self.event: RoomMessageText = event
        self.plugin_loader: PluginLoader = plugin_loader

    async def process(self):

        await self.plugin_loader.run_hooks(self.client, "m.room.message", self.room, self.event)
