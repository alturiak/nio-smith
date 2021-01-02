from nio import RoomMessageText, AsyncClient, MatrixRoom


class Command(object):
    def __init__(self, client, store, config, command, room, event):
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
