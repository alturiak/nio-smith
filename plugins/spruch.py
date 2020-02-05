from chat_functions import send_text_to_room
import random
import os.path


async def spruch(command):
    with open(os.path.join(os.path.dirname(__file__), "spruchdb.txt")) as spruchdb:
        sprueche = spruchdb.readlines()

    message = random.choice(sprueche)
    await send_text_to_room(command.client, command.room.room_id, message, notice=False, markdown_convert=True)
