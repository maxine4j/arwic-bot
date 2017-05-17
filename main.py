import discord
import asyncio
import private
import music
import logging
import permissions
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


def log_info(message, s):
    #logger.info("[User: {} ({}), Server: {} ({})] {}".format(message.author.name, message.author.id, message.server.name, message.server.id, s))
    logger.info("[Server: {}, User: {}] {}".format(message.server.name, message.author.name, s))


def check_perms(author):
    for role in author.roles:
        if role.name == "ArwicBot Commander":
            return True
    return False


async def cmd_hello(client, message):
    '''
    Simple test command
    '''
    #await client.send_message(message.channel, "world")
    em = discord.Embed(title='Now Playing:', description='Hello World realasd alsdlasldlasdllasld - Adam Smith asdasd !!? :)', colour=0xcd201f)
    em.set_author(name='Youtube Music Bot', icon_url="https://www.youtube.com/yts/img/favicon_144-vflWmzoXw.png")
    em.set_thumbnail(url="https://i.ytimg.com/vi/yfwvEt94-nc/hqdefault.jpg")
    em.add_field(name="field1", value="value1", inline=False)
    em.add_field(name="field2", value="value2", inline=False)
    em.add_field(name="field3", value="value3", inline=False)
    #em.set_image(url="https://i.ytimg.com/vi/yfwvEt94-nc/hqdefault.jpg")
    await client.send_message(message.channel, embed=em)



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
    log_info(message, "Parsing message: " + message.content)
    server = message.server
    user = message.author
    # run commands
    if message.content.startswith(prefix + "join"):
        if permissions.has_permission(server, user, permissions.LEVEL_USER):
            await music.cmd_join(client, message)
        else:
            await client.send_message(message.channel, "You require permission level {} to perform that action".format(permissions.LEVEL_USER))
    elif message.content.startswith(prefix + "leave"):
        if permissions.has_permission(server, user, permissions.LEVEL_USER):
            await music.cmd_leave(client, message)
        else:
            await client.send_message(message.channel, "You require permission level {} to perform that action".format(permissions.LEVEL_USER))
    elif message.content.startswith(prefix + "queue"):
        if permissions.has_permission(server, user, permissions.LEVEL_USER):
            await music.cmd_queue(client, message)
        else:
            await client.send_message(message.channel, "You require permission level {} to perform that action".format(permissions.LEVEL_USER))
    elif message.content.startswith(prefix + "play"):
        if permissions.has_permission(server, user, permissions.LEVEL_USER):
            await music.cmd_play(client, message)
        else:
            await client.send_message(message.channel, "You require permission level {} to perform that action".format(permissions.LEVEL_USER))
    elif message.content.startswith(prefix + "stop"):
        if permissions.has_permission(server, user, permissions.LEVEL_USER):
            await music.cmd_stop(client, message)
        else:
            await client.send_message(message.channel, "You require permission level {} to perform that action".format(permissions.LEVEL_USER))
    elif message.content.startswith(prefix + "pause"):
        if permissions.has_permission(server, user, permissions.LEVEL_USER):
            await music.cmd_pause(client, message)
        else:
            await client.send_message(message.channel, "You require permission level {} to perform that action".format(permissions.LEVEL_USER))
    elif message.content.startswith(prefix + "skip"):
        if permissions.has_permission(server, user, permissions.LEVEL_USER):
            await music.cmd_skip(client, message)
        else:
            await client.send_message(message.channel, "You require permission level {} to perform that action".format(permissions.LEVEL_USER))
    elif message.content.startswith(prefix + "get-level"):
        if permissions.has_permission(server, user, permissions.LEVEL_EVERYONE):
            await permissions.cmd_get_level(client, message)
        else:
            await client.send_message(message.channel, "You require permission level {} to perform that action".format(permissions.LEVEL_EVERYONE))
    elif message.content.startswith(prefix + "set-level"):
        if permissions.has_permission(server, user, permissions.LEVEL_MOD):
            await permissions.cmd_set_level(client, message)
        else:
            await client.send_message(message.channel, "You require permission level {} to perform that action".format(permissions.LEVEL_MOD))
    elif message.content.startswith(prefix + "hello"):
        if permissions.has_permission(server, user, permissions.LEVEL_USER):
            await cmd_hello(client, message)
        else:
            await client.send_message(message.channel, "You require permission level {} to perform that action".format(permissions.LEVEL_USER))
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