import discord
import asyncio
import private
from pprint import pprint

prefix = "!"
client = discord.Client()


def get_voice_channel_by_name(server, name):
    '''
    Gets a voice channel by name
    '''
    for channel in server.channels:
        if channel.type == discord.ChannelType.voice and channel.name.lower() == name.lower():
            return channel
    return None


async def cmd_join(message):
    '''
    Joins or moves to a voice channel
    '''
    try:
        # get arguments
        args = message.content.split()
        # get the desired channel
        channel = get_voice_channel_by_name(message.server, args[1])
        if channel is None:
            await client.send_message(message.channel, "Channel " + args[1] + " does not exist")    
            return
        # try get the server's current voice client
        voice_client = client.voice_client_in(message.server)
        if voice_client is None:
            # if we dont have a client, make one by joining the specified channel
            await client.join_voice_channel(channel)
            await client.send_message(message.channel, "Joined voice channel: " + args[1])    
        else:
            # if we do, then change the current client's channel
            await voice_client.move_to(channel)
            await client.send_message(message.channel, "Moved to voice channel: " + args[1])    
    except Exception as e:
        pprint(e)
        await client.send_message(message.channel, "Usage: !join <channel-name>")

    
async def cmd_leave(message):
    '''
    Leaves the current voice channel
    '''
    if client.is_voice_connected(message.server):
        voice_client = client.voice_client_in(message.server)
        voice_client.dissconnect()


async def cmd_hello(message):
    await client.send_message(message.channel, "world")


async def cmd_play_mp3(message):
    try:
        # check if the bot is in a vocie channel
        if not client.is_voice_connected(message.server):
            await client.send_message(message.channel, "I need to be in a voice channel before I can play music.")    
            return
        # get arguments
        args = message.content.split()
        # play the mp3
        voice_client = client.voice_client_in(message.server)
        player = voice_client.create_ffmpeg_player(args[1])
        player.start()
    except Exception as e:
        pprint(e)
        await client.send_message(message.channel, "Usage: !play_mp3 <file-name>")


@client.event
async def on_ready():
    '''
    Event fired when client logs in
    '''
    print("Logged in as")
    print(client.user.name)
    print(client.user.id)
    print("------")


@client.event
async def on_message(message):
    '''
    Event fired when message received
    '''
    # discard messages without our prefix
    if not message.content.startswith(prefix):
        return
    # run commands
    if message.content.startswith(prefix + "join"):
        await cmd_join(message)
    elif message.content.startswith(prefix + "leave"):
        await cmd_leave(message)
    elif message.content.startswith(prefix + "play_mp3"):
        await cmd_play_mp3(message)
    elif message.content.startswith(prefix + "hello"):
        await cmd_hello(message)


def main():
    '''
    Entry point
    '''
    client.run(private.arwic_bot_token)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Logging out")
        client.close()
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)