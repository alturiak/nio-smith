from chat_functions import send_text_to_room
from time import sleep


async def send_typing(client, room_id, message, notice=False, markdown_convert=True):
    await client.room_typing(room_id, timeout=1000)
    sleep(1)
    await send_text_to_room(client, room_id, message, notice, markdown_convert)
    await client.room_typing(room_id, typing_state=False)