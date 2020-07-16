import logging
from asyncio import sleep

from nio import (
    SendRetryError, RoomSendResponse
)
from markdown import markdown

logger = logging.getLogger(__name__)


async def send_text_to_room(
    client,
    room_id,
    message,
    notice=True,
    markdown_convert=True
) -> RoomSendResponse or None:
    """Send text to a matrix room

    Args:
        client (nio.AsyncClient): The client to communicate to matrix with

        room_id (str): The ID of the room to send the message to

        message (str): The message content

        notice (bool): Whether the message should be sent with an "m.notice" message type
            (will not ping users)

        markdown_convert (bool): Whether to convert the message content to markdown.
            Defaults to true.
    """
    # Determine whether to ping room members or not
    msgtype = "m.notice" if notice else "m.text"

    content = {
        "msgtype": msgtype,
        "format": "org.matrix.custom.html",
        "body": message,
    }

    if markdown_convert:
        content["formatted_body"] = markdown(message)

    response: RoomSendResponse

    try:
        response = await client.room_send(
            room_id,
            "m.room.message",
            content,
            ignore_unverified_devices=True,
        )
        return response
    except SendRetryError:
        logger.exception(f"Unable to send message response to {room_id}")
        return None


async def send_typing(client, room_id, message, notice=False, markdown_convert=True):
    """DEPRECATED by plugin.message(): Send text to a room after displaying a typing notification for .2s
    Args:
        client (nio.AsyncClient): The client to communicate to matrix with

        room_id (str): The ID of the room to send the message to

        message (str): The message content

        notice (bool): Whether the message should be sent with an "m.notice" message type
            (will not ping users)
            Defaults to False

        markdown_convert (bool): Whether to convert the message content to markdown.
            Defaults to True.
    """
    await client.room_typing(room_id, timeout=200)
    await sleep(.2)
    await client.room_typing(room_id, typing_state=False)
    await send_text_to_room(client, room_id, message, notice, markdown_convert)
