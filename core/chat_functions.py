import logging
from io import StringIO
from html.parser import HTMLParser

from nio import (
    SendRetryError, RoomSendResponse, Event, RoomGetEventResponse
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

    original_response: RoomGetEventResponse = await client.room_get_event(room_id, event_id)
    original_event: Event = original_response.event
    original_content = original_event.source["content"]

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
