import asyncio
from random import randrange
from typing import List, Dict

from nio import AsyncClient, UnknownEvent

from core.bot_commands import Command
from core.plugin import Plugin
import logging
import datetime
from asyncio import sleep
from PIL import Image

logger = logging.getLogger(__name__)

plugin = Plugin("sample", "General", "Just a simple sample.")

# Change this to true to actually enable the dummy timers for demo purposes
timers_enabled: bool = False


def setup():
    plugin.add_command(
        "sample",
        sample_command,
        "A simple sample command, producing a simple sample output",
    )
    plugin.add_command("sample_store", sample_store, "Store a message persistently", power_level=50)
    plugin.add_command("sample_read", sample_read, "Read the stored message")
    plugin.add_command("sample_clear", sample_clear, "Clear the stored message")
    plugin.add_command(
        "sample_link_user",
        sample_link_user,
        "Given a displayname, try to produce a userlink",
    )
    plugin.add_command(
        "sample_reaction_test",
        sample_reaction_test,
        "Post a message and record reactions to this message",
    )
    plugin.add_command("sample_react", sample_react, "Post reactions to a command")
    plugin.add_command("sample_replace", sample_replace, "Post a message and edit it afterwards")
    plugin.add_command(
        "sample_add_command",
        add_command,
        "Dynamically adds an active command `sample_remove_command`",
    )
    plugin.add_command(
        "sample_sleep",
        sample_sleep,
        "Sleep for five seconds, then post a message, to test parallel execution of commands",
    )
    plugin.add_command(
        "sample_user",
        sample_user,
        "Respond with the mxid and displayname of the user issuing the command",
    )
    plugin.add_command(
        "sample_add_config",
        sample_add_config,
        "Dynamically load a configuration option at runtime and read it",
    )
    plugin.add_command(
        "sample_expandable_message",
        sample_expandable_message,
        "Send a message that can be expanded to view it's full content",
    )
    plugin.add_command(
        "sample_expandable_notice",
        sample_expandable_notice,
        "Send a notice that can be expanded to view it's full content",
    )
    plugin.add_command("sample_send_image", sample_send_image, "Generate a small image and post it")
    plugin.add_command("sample_fetch_image", sample_fetch_image, "Fetch a test image and post it")
    plugin.add_command(
        "sample_list_servers_on_room",
        sample_list_servers_on_room,
        "List servers on current room",
    )
    plugin.add_command(
        "sample_count_rooms_for_server",
        sample_count_rooms_for_server,
        "Post a count of rooms shared with users on a given server",
    )
    plugin.add_command(
        "sample_link_users_per_server",
        sample_link_users_per_server,
        "List all users in the room by their homeserver",
    )

    """The following part demonstrates defining a configuration value to be expected in the plugin's configuration file and reading the value

    Define a configuration value to be loaded at startup.
    The value supplied is a default value that is used if no configuration was found in the configuration file 
    """
    plugin.add_config("default_message", "this is the default message", is_required=True)
    plugin.add_command(
        "sample_read_config",
        sample_read_config,
        "Reads the value `default_message` from the plugin configuration",
    )

    """The following part demonstrates registering timers by fixed interval and timedelta"""
    if timers_enabled:
        plugin.add_timer(timer_daily, frequency="daily")
        plugin.add_timer(timer_every_36_minutes, frequency=datetime.timedelta(minutes=36))


class Sample:
    def __init__(self, message: str):
        self.message = message


async def sample_command(command):
    await plugin.respond_message(command, "This is a sample output")


async def sample_store(command):
    """
    Persistently store a message
    :param command:
    :return:
    """

    if command.args:
        logger.debug(f"sample_store called with {command.args}")
        message: str = " ".join(command.args)
        sample: Sample = Sample(message)
        if await plugin.store_data("sample", sample):
            await plugin.respond_notice(command, f'Message "{message}" stored successfully')
        else:
            await plugin.respond_notice(command, "Could not store message")
    else:
        await plugin.respond_notice(command, "No message supplied")


async def sample_read(command):
    """
    Read previously stored message
    :param command:
    :return:
    """

    try:
        sample: Sample = await plugin.read_data("sample")
        await plugin.respond_message(command, f"Message: {sample.message}", delay=200)
    except KeyError:
        await plugin.respond_notice(command, "Message could not be loaded")


async def sample_clear(command):
    """
    Clear a previously stored message
    :param command:
    :return:
    """

    if await plugin.clear_data("sample"):
        await plugin.respond_notice(command, "Message cleared")
    else:
        await plugin.respond_notice(command, "Could not clear message as no message was stored")


async def sample_link_user(command):
    """
    Highlight a user (produce userlink by displayname)
    :param command:
    :return:
    """

    if len(command.args) == 1:
        if await plugin.is_user_in_room(command.client, command.room.room_id, command.args[0]):
            user_link: str = await plugin.link_user(command.client, command.room.room_id, command.args[0])
            await plugin.respond_message(
                command,
                f"Requested Displayname: {command.args[0]}, User Link: {user_link}",
            )
        else:
            await plugin.respond_notice(command, f"No user found for {command.args[0]}")


async def sample_reaction_test(command):
    """
    Posts a message and tracks reactions. If a reaction is received, post it to the room.
    This only stores the event_id of the tracked message but needs another method to track replies or reactions.
    :param command:
    :return:
    """

    if len(command.args) == 0:
        event_id: str = await plugin.respond_message(
            command,
            f"A reaction to this message will be tracked and posted back to the room.",
        )
        await plugin.respond_notice(command, f"Tracking Event ID {event_id}")
        await plugin.store_data("tracked_message", event_id)

        # Dynamically add a reaction hook for one specific event-id
        plugin.add_hook("m.reaction", hook_reactions, event_ids=[event_id], hook_type="dynamic")

    else:
        await plugin.respond_notice(command, "Usage: sample_reaction_test")


async def hook_reactions(client: AsyncClient, room_id: str, event: UnknownEvent):
    """
    Is being called when a reaction to the message posted by `sample_reaction_test` has been received
    :param client: AsyncClient
    :param room_id: The room_id the reaction was received on
    :param event: nio.events.room_events.UnknownEvent: the actual event received
    :return:
    """

    tracked_message: str = await plugin.read_data("tracked_message")
    reaction: str = event.source["content"]["m.relates_to"]["key"]

    if tracked_message is not None:
        await plugin.send_notice(
            client,
            room_id,
            f"Reaction received to event {tracked_message} received: {reaction}. Disabling reaction tracking.",
        )
        # Remove dynamic reaction hook
        plugin.del_hook("m.reaction", hook_reactions)


async def sample_react(command):
    """
    Posts a message and reacts to it
    :param command:
    :return:
    """

    if len(command.args) == 0:
        await plugin.send_reaction(command.client, command.room.room_id, command.event.event_id, "Hello")
        await plugin.send_reaction(command.client, command.room.room_id, command.event.event_id, "👋")


async def sample_replace(command):
    """
    Posts a message and edits if after three seconds.
    :param command: (Command) the command issued to the bot
    :return: -
    """

    message_id: str = await plugin.respond_message(command, f'<font color="red">This is a test message</font>')
    await sleep(3)

    # this should actually edit the message ...
    await plugin.replace_message(
        command.client,
        command.room.room_id,
        message_id,
        f'<font color="green">This is an edited test message</font>',
    )
    await sleep(3)

    # ... this should not
    await plugin.replace_message(
        command.client,
        command.room.room_id,
        message_id,
        f'<font color="green">This is an edited test message</font>',
    )


async def sample_read_config(command):
    """
    Reads `default_message` from configuration and sends it as message
    :param command:
    :return:
    """

    message: str = plugin.read_config("default_message")
    if message:
        await plugin.respond_message(command, f"Configuration value: {message}")
    else:
        await plugin.respond_notice(command, f"Could not read message from configuration")


async def timer_daily(client):
    """
    Prints a dummy message at the start of the day
    :param client:
    :return:
    """

    print(f"This method is being executed around midnight every day")


async def timer_every_36_minutes(client):
    """
    Prints a dummy message every 36 minutes
    :param client:
    :return:
    """

    print(f"This method is being executed every 36 minutes")


async def add_command(command):
    """
    Dynamically activate a command and a hook for reactions
    :param command:
    :return:
    """

    plugin.add_command(
        "sample_remove_command",
        remove_command,
        "Dynamically removes an active command `sample_remove_command`",
        command_type="dynamic",
    )
    plugin.add_hook(
        "m.reaction",
        remove_command,
        room_id_list=[command.room.room_id],
        hook_type="dynamic",
    )
    await plugin.respond_message(
        command,
        "Dynamic command `sample_remove_command` and dynamic hook for reactions activated.  \n" "Use `sample_remove_command` or a reaction to disable again",
    )


async def remove_command(
    command_client: AsyncClient or Command,
    room_id: str = "",
    event: UnknownEvent or None = None,
):
    """
    Dynamically remove the command and hook added by add_command()
    :param event:
    :param command_client:
    :param room_id:
    :return:
    """

    plugin.del_command("sample_remove_command")
    plugin.del_hook("m.reaction", remove_command)

    if isinstance(command_client, AsyncClient):
        client = command_client
        room = room_id
    else:
        client = command_client.client
        room = command_client.room.room_id
    await plugin.send_message(
        client,
        room,
        "Dynamic command `sample_remove_command` and hook for reactions deactivated.",
    )


async def sample_sleep(command: Command):
    """
    Post a message before and after a timer, to demonstrate and test parallel execution of commands
    If called twice in rapid succession, both timers should run in parallel
    :param command:
    :return:
    """

    random_int: int = randrange(1000)
    await plugin.respond_message(command, f"ID: {random_int} - before timer")
    await asyncio.sleep(5)
    await plugin.respond_message(command, f"ID: {random_int} - after timer")


async def sample_user(command: Command):
    """
    Respond with the mxid and displayname of the user issuing the command
    :param command:
    :return:
    """

    mxid: str = command.event.sender
    display_name: str = command.room.user_name(mxid)
    user_link: str = await plugin.link_user(command.client, command.room.room_id, display_name)
    await plugin.respond_message(command, f"Command received from {display_name} ({mxid}). Userlink: {user_link}")


async def sample_add_config(command: Command):
    """
    Dynamically add a configuration option at runtime.
    There probably isn't any use-case for that and behaviour might not be what is expected.
    :param command:
    :return:
    """

    plugin.add_config("sample_add_config", is_required=True)
    message: str = plugin.read_config("sample_add_config")
    await plugin.respond_message(command, f"Loaded from config: {message}")


async def sample_expandable_message(command: Command):
    """
    Send an expandable message
    :param command:
    :return:
    """

    message: str = "This part is always visible"
    expanded_message: str = "This part is only visible when the message is expanded."
    await plugin.respond_message(command, message, expanded_message=expanded_message)


async def sample_expandable_notice(command: Command):
    """
    Send an expandable message
    :param command:
    :return:
    """

    message: str = "This part is always visible"
    expanded_message: str = "This part is only visible when the message is expanded."
    await plugin.respond_notice(command, message, expanded_message=expanded_message)


async def sample_send_image(command: Command):
    """
    Generate a small image and post it
    :param command:
    :return:
    """

    image: Image.Image = Image.new("RGBA", (40, 40), (255, 0, 0, 255))
    await plugin.send_image(command.client, command.room.room_id, image)


async def sample_fetch_image(command: Command):
    """
    Fetch a test image and post it
    :param command:
    :return:
    """

    if len(command.args) == 0:
        image = await plugin.fetch_image_from_url("https://avatars.githubusercontent.com/u/1785173?s=120&v=4")
        if image is not None:
            await plugin.send_image(command.client, command.room.room_id, image)
        else:
            await plugin.respond_notice(command, "Error fetching image")

    else:
        await plugin.respond_notice(command, "Usage: `sample_fetch_image`")


async def sample_list_servers_on_room(command: Command):
    """
    List servers on current room
    :param command:
    :return:
    """

    client: AsyncClient = command.client
    room_id: str = command.room.room_id
    connected_servers: str = ", ".join(await plugin.get_connected_servers(client, [room_id]))
    await plugin.respond_notice(command, f"Homeservers in this room: {connected_servers}")


async def sample_count_rooms_for_server(command: Command):
    """
    Post a count of rooms shared with users on a given server
    :return:
    """

    if len(command.args) == 1:
        client: AsyncClient = command.client
        rooms_for_server: int = len(await plugin.get_rooms_for_server(client, command.args[0]))
        await plugin.respond_notice(
            command,
            f"I'm sharing {rooms_for_server} rooms with users on {command.args[0]}",
        )
    else:
        await plugin.respond_notice(command, "Usage: sample_list_rooms_for_server <server_name>")


async def sample_link_users_per_server(command: Command):
    """
    List all users in the room by their homeserver
    :param command:
    :return:
    """

    client: AsyncClient = command.client
    room_id: str = command.room.room_id
    connected_servers: List[str] = await plugin.get_connected_servers(client, [room_id])
    connected_user_ids: Dict[str, List[str]] = await plugin.get_users_on_servers(client, connected_servers, [room_id])

    message: str = ""
    user_ids: List[str]
    for server, user_ids in connected_user_ids.items():
        user_id: str
        message += f"Server: {server}  \n  "
        message += ", ".join([await plugin.link_user_by_id(client, room_id, user_id) for user_id in user_ids])
        message += "  \n"

    await plugin.respond_notice(command, message)


setup()
