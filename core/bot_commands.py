from nio import RoomMessageText, AsyncClient, MatrixRoom
from pluginloader import PluginLoader
from chat_functions import send_text_to_room


class Command(object):
    def __init__(self, client, store, config, command, room, event, plugin_loader: PluginLoader):
        """A command made by a user

        Args:
            client (nio.AsyncClient): The client to communicate to matrix with

            store (Storage): Bot storage

            config (Config): Bot configuration parameters

            command (str): The command and arguments

            room (nio.rooms.MatrixRoom): The room the command was sent in

            event (nio.events.room_events.RoomMessageText): The event describing the command
        """
        self.client: AsyncClient = client
        self.store = store
        self.config = config
        self.command = command
        self.room: MatrixRoom = room
        self.event: RoomMessageText = event
        self.args = self.command.split()[1:]
        self.plugin_loader: PluginLoader = plugin_loader

    async def process(self):
        """
        Process the command, posting an error when user's power_level is insufficient
        Do not react to commands that could not be found as those might be handled by other clients!
        :return:
        """

        if await self.plugin_loader.run_command(self) == 2:
            # power_level insufficient
            await send_text_to_room(self.client, self.room.room_id, f"Required power level for command {self.command[0]} not met")
