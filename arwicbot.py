import discord
import asyncio
import sys
import os
import private
import logging_helper
import modules
import constants
from modules._base_ import InsufficientPrivilegesException

# invite link "https://discordapp.com/oauth2/authorize?client_id=313663820822216705&scope=bot&permissions=2146958591"


prefix = "!"
client = discord.Client()
logger = logging_helper.init_logger("ArwicBot")


@client.event
async def on_ready():
    '''
    Event fired when client logs in
    '''
    logger.info("Logged in as " + client.user.name+ " " + client.user.id)
    game = discord.Game(name="ArwicBot: #{}".format(constants.CURRENT_COMMIT))
    await client.change_presence(game=game)


@client.event
async def on_message(message):
    '''
    Event fired when message received
    '''
    # discard messages without our prefix
    if not message.content.startswith(prefix):
        return
    logger.info("[Server: {}, User: {}] Parsing message: {}".format(message.server.name, message.author.name, message.content))
    try:
        await modules.try_run_command(prefix, client, message)
    except InsufficientPrivilegesException as ipe:
        await client.send_message(message.channel, "Permissions: {}".format(ipe.msg))


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