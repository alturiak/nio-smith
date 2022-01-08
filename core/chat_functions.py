import logging
import os
from io import StringIO
from html.parser import HTMLParser
from typing import Union

import aiofiles.os
from PIL import Image
import uuid
import blurhash

from nio import (
    SendRetryError, RoomSendResponse, Event, RoomGetEventResponse, RoomGetEventError, UploadResponse
)
from markdown import markdown

logger = logging.getLogger(__name__)


class MLStripper(HTMLParser):

    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = StringIO()

    def handle_data(self, d):
        self.text.write(d)

    def get_data(self):
        return self.text.getvalue()


def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()


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
        "body": strip_tags(message),
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


async def send_reaction(client, room_id, event_id: str, reaction: str):
    """
    Send a reaction to a specific event
    :param client: (nio.AsyncClient) The client to communicate to matrix with
    :param room_id: (str) room_id to send the reaction to (is this actually being used?)
    :param event_id: (str) event_id to react to
    :param reaction: (str) the reaction to send
    :return:
    """

    content = {
        "m.relates_to": {
            "event_id": event_id,
            "rel_type": "m.annotation",
            "key": reaction,
        }
    }

    await client.room_send(room_id, "m.reaction", content, ignore_unverified_devices=True)


async def send_replace(client, room_id: str, event_id: str, message: str) -> str or None:
    """
    Send a replacement message (edit a previous message).
    Gets the event from the server first and compares old content against new content. Only if the content differs, will the m.replace event be sent
    :param client: (nio.AsyncClient) The client to communicate to matrix with
    :param room_id: (str) room_id to send the edit to
    :param event_id: (str) event_id to react to
    :param message: (str) the new message body
    :return:    (str) the event-id of the new room-event, if the original event has been replaced or
                None, if the event has not been edited
    """

    try:
        original_response: Union[RoomGetEventResponse, RoomGetEventError] = await client.room_get_event(room_id, event_id)
        original_event: Event = original_response.event
        original_content = original_event.source["content"]
    except Exception:
        return None

    if isinstance(original_response, RoomGetEventResponse) and original_content != {}:

        new_content = {
            "m.new_content": {
                "msgtype": "m.text",
                "format": "org.matrix.custom.html",
                "body": strip_tags(message),
                "formatted_body": markdown(message)
            },
            "m.relates_to": {
                "rel_type": "m.replace",
                "event_id": event_id
            },
            "msgtype": "m.text",
            "format": "org.matrix.custom.html",
            "body": strip_tags(message),
            "formatted_body": markdown(message)
        }

        # check if there are any differences in body or formatted_body before actually sending the m.replace-event
        if new_content["body"] != original_content["body"] or new_content["formatted_body"] != original_content["formatted_body"]:
            return await client.room_send(room_id, "m.room.message", new_content, ignore_unverified_devices=True)
        else:
            return None
    else:
        return None


async def send_image(client, room_id: str, image: Image.Image) -> str or None:
    """
    Uploads the given Image-Object to the matrix-server and sends a new message including the image.
    :param client:
    :param room_id:
    :param image:
    :return:     (str) the event-id of the new room-event
                None if sending image or message failed
    """

    # temporarily save the image to a file
    temp_filename: str = f"{uuid.uuid4().hex}.png"
    try:
        image.save(temp_filename, "PNG")
    except OSError:
        return None

    (width, height) = image.size  # image.size returns (width,height) tuple
    mime_type: str = "image/png"

    # first do an upload of image, then send URI of upload to room
    file_stat = await aiofiles.os.stat(temp_filename)
    image_hash = blurhash.encode(temp_filename, x_components=4, y_components=3)

    try:
        async with aiofiles.open(temp_filename, "r+b") as f:
            resp, maybe_keys = await client.upload(f, content_type=mime_type, filename=os.path.basename(temp_filename), filesize=file_stat.st_size)
        os.remove(temp_filename)
    except OSError:
        logger.warning(f"Failed to remove temporary image file {temp_filename}")

    if isinstance(resp, UploadResponse):
        content = {
            "body": os.path.basename(temp_filename),  # descriptive title
            "info": {
                "size": file_stat.st_size,
                "mimetype": mime_type,
                "w": width,  # width in pixel
                "h": height,  # height in pixel
                "xyz.amorgan.blurhash": image_hash
            },
            "msgtype": "m.image",
            "url": resp.content_uri,
        }

        try:
            return await client.room_send(room_id, message_type="m.room.message", content=content)
        except Exception:
            return None
    else:
        return None
