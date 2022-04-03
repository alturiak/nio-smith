from nio import AsyncClient, MatrixRoom
from core.plugin import Plugin

plugin = Plugin("manage_bot", "General", "Provide functions to manage the bot from an admin-room")


def setup():
    plugin.add_config("manage_bot_rooms", is_required=True)
    plugin.add_config("manage_bot_power_level", is_required=False, default_value=100)
    plugin.add_command(
        "bot_rooms_list",
        bot_rooms_list,
        "Displays a list of rooms the bot is in",
        plugin.read_config("manage_bot_rooms"),
        plugin.read_config("manage_bot_power_level"),
    )
    plugin.add_command(
        "bot_rooms_cleanup",
        bot_rooms_cleanup,
        "Leave rooms the bot is alone in",
        plugin.read_config("manage_bot_rooms"),
        plugin.read_config("manage_bot_power_level"),
    )
    plugin.add_command(
        "bot_leave_room",
        bot_leave_room,
        "Make the bot leave a specific room",
        plugin.read_config("manage_bot_rooms"),
        plugin.read_config("manage_bot_power_level"),
    )


async def bot_rooms_list(command):
    """
    Display name, room_id and member count of all rooms the bot is in.
    Display a list of members of rooms with only two members (e.g. DMs with the bot)
    :param command:
    :return:
    """

    client: AsyncClient = command.client
    room: MatrixRoom
    message: str = ""
    # sort rooms by display_name
    rooms = {k: v for k, v in sorted(client.rooms.items(), key=lambda item: item[1].display_name)}

    for room in rooms.values():
        message += f"`{room.display_name}` ({room.room_id}): {room.member_count}  \n"
        if room.member_count == 2:
            message += f"{room.users}  \n"
    await plugin.respond_message(command, message)


async def bot_rooms_cleanup(command):
    """
    Make the bot leave all rooms that the bot is the only user in
    :param command:
    :return:
    """

    client: AsyncClient = command.client
    room: MatrixRoom
    message: str = ""
    for room in client.joined_rooms.values():
        if room.member_count < 2:
            message += f"Leaving {room.display_name} ({room.room_id})  \n"
            await client.room_leave(room.room_id)

    await plugin.respond_message(command, message)


async def bot_leave_room(command):
    """
    Make the bot leave a specific room
    :param command:
    :return:
    """

    client: AsyncClient = command.client
    if len(command.args) == 1:
        leave_room: MatrixRoom = command.args[0]
        room: MatrixRoom
        for room in client.rooms.values():
            if room.room_id == leave_room:
                await plugin.respond_notice(command, f"Left room {room.display_name} ({room.room_id})")
                await client.room_leave(room.room_id)
                await client.room_forget(room.room_id)
                break
        else:
            await plugin.respond_notice(command, f"Error: I'm not in room {leave_room}")

    else:
        await plugin.respond_notice(command, f"Usage: `bot_leave_room <room_id>`")


setup()
