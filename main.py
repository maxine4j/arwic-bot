import discord
import asyncio
import private
import music
import logging
from pprint import pprint

prefix = "!"
client = discord.Client()

# setup logging
logger = logging.getLogger("arwicbot")
logger.setLevel(logging.DEBUG)
# file handler
fh = logging.FileHandler('arwicbot.log')
fh.setLevel(logging.DEBUG)
# console handler
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# formatter
#formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
formatter = logging.Formatter('[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s')
ch.setFormatter(formatter)
fh.setFormatter(formatter)
# add the handlers to logger
logger.addHandler(ch)
logger.addHandler(fh)


def check_perms(author):
    for role in author.roles:
        if role.name == "ArwicBot Commander":
            return True
    return False


async def cmd_hello(client, message):
    '''
    Simple test command
    '''
    await client.send_message(message.channel, "world")


@client.event
async def on_ready():
    '''
    Event fired when client logs in
    '''
    logger.info("Logged in as " + client.user.name+ " " + client.user.id)


@client.event
async def on_message(message):
    '''
    Event fired when message received
    '''
    # discard messages without our prefix
    if not message.content.startswith(prefix):
        return
    # check if the auther has the bot commander role
    if not check_perms(message.author):
        await client.send_message(message.channel, "You do not have the required role to issue commands.")
        return
    logger.info("Parsing message: " + message.author.name + " (" + message.author.id + "): " + message.content)
    # run commands
    if message.content.startswith(prefix + "join"):
        await music.cmd_join(client, message)
    elif message.content.startswith(prefix + "leave"):
        await music.cmd_leave(client, message)
    elif message.content.startswith(prefix + "play_file"):
        await music.cmd_play_file(client, message)
    elif message.content.startswith(prefix + "queue_song"):
        await music.cmd_queue_song(client, message)
    elif message.content.startswith(prefix + "play"):
        await music.cmd_play(client, message)
    elif message.content.startswith(prefix + "stop"):
        await music.cmd_stop(client, message)
    elif message.content.startswith(prefix + "pause"):
        await music.cmd_pause(client, message)
    elif message.content.startswith(prefix + "skip"):
        await music.cmd_skip(client, message)
    elif message.content.startswith(prefix + "hello"):
        await cmd_hello(client, message)
    else:
        await client.send_message(message.channel, "Unknown command")

def main():
    '''
    Entry point
    '''
    client.run(private.arwic_bot_token)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt")
        client.close()
        logger.info("Logged out")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)