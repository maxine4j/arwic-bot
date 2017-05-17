import discord
import asyncio
import multiprocessing
import pafy
import re
import os.path
import queue
import logging
from pprint import pprint


logger = logging.getLogger("arwicbot")
temp_base_dir = "/tmp/arwicbot/"
youtube_red = 0xcd201f
youtube_icon = "https://www.youtube.com/yts/img/favicon_144-vflWmzoXw.png"
jobs = []
sessions = {}


class MusicSession:
    class PlayListEmpty(Exception):
        pass

    def __init__(self, server):
        self.server = server
        self.player = None
        self.playlist = queue.Queue()
        self.current_song = None
        self.current_channel = None

    def queue(self, id):
        self.playlist.put(id, block=False)

    def next_song(self):
        self.current_song = self.playlist.get(block=False)
        return self.current_song
        

def log_info(message, s):
    logger.info("[Server: {}, User: {}] {}".format(message.server.name, message.author.name, s))
    
    
def get_session(server):
    if server.id in sessions:
        return sessions[server.id]
    sessions[server.id] = MusicSession(server)
    return sessions[server.id]


def get_youtube_id(url):
    youtube_regex = (
        r'(https?://)?(www\.)?'
        '(youtube|youtu|youtube-nocookie)\.(com|be)/'
        '(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
    youtube_regex_match = re.match(youtube_regex, url)
    if youtube_regex_match:
        return youtube_regex_match.group(6)
    return youtube_regex_match


def get_song_info(id):
    try:
        with open(temp_base_dir + id + "_info", "r") as file_handle:
            lines = file_handle.readlines()
            return lines[0], lines[1], lines[2]
    except:
        logger.error("Failed to get song info: ", e)


def get_voice_channel_by_name(server, name):
    '''
    Gets a voice channel by name
    '''
    for channel in server.channels:
        if channel.type == discord.ChannelType.voice and channel.name.lower() == name.lower():
            return channel
    return None


async def cmd_join(client, message):
    '''
    Joins or moves to a voice channel
    '''
    try:
        # get arguments
        args = message.content.split()
        # default to the messengers current channel
        if len(args) == 1:
            if message.author.voice.voice_channel is None:
                await client.send_message(message.channel, "Usage: `!join <channel-name>`")
                return
            channel_name = message.author.voice.voice_channel.name
        elif len(args) > 1:
            channel_name = args[1]
        # get the desired channel
        channel = get_voice_channel_by_name(message.server, channel_name)
        if channel is None:
            await client.send_message(message.channel, "Channel {} does not exist".format(channel_name))
            return
        # try get the server's current voice client
        voice_client = client.voice_client_in(message.server)
        if voice_client is None:
            # if we dont have a client, make one by joining the specified channel
            await client.join_voice_channel(channel)
            session = get_session(message.server)
            session.current_channel = channel
            await client.send_message(message.channel, "Joined voice channel: {}".format(channel.name))
            log_info(message, "Joined voice channel {}".format(channel.name))
        else:
            # if we do, then change the current client's channel
            await voice_client.move_to(channel)
            session = get_session(message.server)
            session.current_channel = channel
            await client.send_message(message.channel, "Moved to voice channel: {}".format(channel.name))
            log_info(message, "Moved to voice channel {}".format(channel.name))
    except Exception as e:
        logger.error("Error joining channel (server: {}): {}".format(message.server.id, e))
        await client.send_message(message.channel, "Usage: `!join <channel-name>`")

    
async def cmd_leave(client, message):
    '''
    Leaves the current voice channel
    '''
    if client.is_voice_connected(message.server):
        voice_client = client.voice_client_in(message.server)
        await voice_client.disconnect()
        session = get_session(message.server)
        last_channel = session.current_channel
        session.current_channel = None
        log_info(message, "Left voice channel {}".format(last_channel.name))
        await client.send_message(message.channel, "Left voice channel.")    


async def cmd_play(client, message):
    try:
        # check if the bot is in a vocie channel
        if not client.is_voice_connected(message.server):
            await client.send_message(message.channel, "Cannot play music when not in a voice channel. Use `!join <channel>` to connect me to a channel.")    
            return
        # get the servers session
        session = get_session(message.server)
        # if the server doesnt have a session, there is no music playing
        if session.player is None:
            try:
                next_song = session.next_song()
            except queue.Empty:
                await client.send_message(message.channel, "The playlist is empty. Add songs with `!queue <youtube-link>`")
                return
            voice_client = client.voice_client_in(message.server)
            session.player = voice_client.create_ffmpeg_player(temp_base_dir + next_song)
            session.player.start()
            session.current_song = next_song
            log_info(message, "Started playback of song {} on channel {}".format(next_song, session.current_channel.name))
            song_title, song_uploader, song_thumbnail = get_song_info(session.current_song)
            # add embed
            em = discord.Embed(title="Now Playing: {}".format(song_title), description=song_uploader, colour=youtube_red)
            em.set_author(name="Youtube Music Bot", icon_url=youtube_icon)
            em.set_thumbnail(url=song_thumbnail)
            # add up next
            if len(session.playlist.queue) >= 2:
                title1, uploader1, thumb1 = get_song_info(session.playlist.queue[0])
                title2, uploader2, thumb2 = get_song_info(session.playlist.queue[1])
                em.add_field(name="Up Next: {}".format(title1), value="{}".format(uploader1), inline=True)
                em.add_field(name="Up Next: {}".format(title2), value="{}".format(uploader2), inline=True)
            elif len(session.playlist.queue) >= 1:
                title1, uploader1, thumb1 = get_song_info(session.playlist.queue[0])
                em.add_field(name="Up Next: {}".format(title1), value="{}".format(uploader1), inline=True)
            await client.send_message(message.channel, embed=em)

        # if the server has a session, there is music paused
        elif not session.player.is_playing():
            if session.player.is_done():
                session.player = None
                await cmd_play(client, message)
            else:
                session.player.resume()
                log_info(message, "Resumed playback of song {} on channel {}".format(session.current_song, session.current_channel.name))
                await client.send_message(message.channel, "Resuming playback: {}".format(get_song_info(session.current_song)[0]))
    except Exception as e:
        logger.error("Error starting/resuming player (server: {}): {}".format(message.server.id, e))
        await client.send_message(message.channel, "Internal Error.")


async def cmd_pause(client, message):
    try:
        # check if the bot is in a vocie channel
        if not client.is_voice_connected(message.server):
            await client.send_message(message.channel, "Cannot play music when not in a voice channel. Use `!join <channel>` to connect me to a channel.")    
            return
        # get the servers session
        session = get_session(message.server)
        if session.player is not None:
            session.player.pause()
            log_info(message, "Paused playback of song {} on channel {}".format(session.current_song, session.current_channel.name))
            await client.send_message(message.channel, "Paused playback.")
    except Exception as e:
        logger.error("Error pausing player (server: {}): {}".format(message.server.id, e))
        await client.send_message(message.channel, "Internal Error.")


async def cmd_skip(client, message):
    try:
        # check if the bot is in a vocie channel
        if not client.is_voice_connected(message.server):
            await client.send_message(message.channel, "Cannot play music when not in a voice channel. Use `!join <channel>` to connect me to a channel.")    
            return
        # get the servers session
        session = get_session(message.server)
        if session.player is not None:
            session.player.after = None
            session.player.stop()
            session.player = None
        try:
            next_song = session.next_song()
        except queue.Empty:
            await client.send_message(message.channel, "The playlist is empty. Add songs with `!queue <youtube-link>`")
            return
        voice_client = client.voice_client_in(message.server)
        session.player = voice_client.create_ffmpeg_player(temp_base_dir + next_song)
        session.player.start()
        log_info(message, "Skipping {} on channel {}".format(session.current_song, session.current_channel.name))
        log_info(message, "Started playback of song {} on channel {}".format(next_song, session.current_channel.name))
        session.current_song = next_song
        await client.send_message(message.channel, "Now playing: {}".format(get_song_info(session.current_song)[0]))
    except Exception as e:
        logger.error("Error skipping song (server: {}): {}".format(message.server.id, e))
        await client.send_message(message.channel, "Internal Error.")


async def cmd_stop(client, message):
    try:
        # check if the bot is in a vocie channel
        if not client.is_voice_connected(message.server):
            await client.send_message(message.channel, "Cannot play music when not in a voice channel. Use `!join <channel>` to connect me to a channel.")    
            return
        # get the servers session
        session = get_session(message.server)
        if session.player is not None:
            # stop the player
            session.player.after = None
            session.player.stop()
            session.player = None
            log_info(message, "Stopped playback of song {} on channel {}".format(session.current_song, session.current_channel.name))
            session.current_song = None
            await client.send_message(message.channel, "Stopped playback.")
    except Exception as e:
        logger.error("Error stopping player (server: {}): {}".format(message.server.id, e))
        await client.send_message(message.channel, "Internal Error.")


async def cmd_queue(client, message):
    '''
    Adds a youtube video to the song queue
    This command downloads the audio stream and adds it to the queue
    '''
    try:
        # get arguments
        args = message.content.split()
        if len(args) < 2:
            raise Exception
        # determine if we should redownload the file
        purge = len(args) > 2 and args[2] == "purge"
        # determine play count
        play_count = 1
        if len(args) == 3:
            # format -> !queue link count
            play_count = int(args[2])
        elif len(args) == 4:
            # format -> !queue link purge count
            play_count = int(args[3])
        # check if the arg is a youtube link
        youtube_id = get_youtube_id(args[1])
        if youtube_id is None:
            await client.send_message(message.channel, "Error: Link must be a video from <https://youtube.com/>")
            return
        # add the song to the server's queue
        session = get_session(message.server)
        for c in range(play_count):
            session.queue(youtube_id)
        log_info(message, "Queued song '{}' {} times".format(youtube_id, play_count))
        # check if we have already downloaded the video (purge overrides this)
        if os.path.isfile(temp_base_dir + youtube_id) and not purge:
            await client.send_message(message.channel, "Added song to the server's playlist.")
            return
        # build a standard url with the video id
        url = "https://www.youtube.com/watch?v={}".format(youtube_id)
        def worker():
            if not os.path.isdir(temp_base_dir):
                os.makedirs(temp_base_dir)
            # instantiate pafy object
            video = pafy.new(url)
            # write video info to disk
            with open(temp_base_dir + youtube_id + "_info", "w+") as file_handle:
                file_handle.write(video.title + "\n")
                file_handle.write(video.author + "\n")
                file_handle.write(video.thumb + "\n")
            # download the audio stream
            logger.info("Downloading {} by {} ({})".format(video.title, video.author, youtube_id))
            audio_stream = video.getbestaudio()
            audio_stream.download(filepath=temp_base_dir + youtube_id, quiet=True)
        # start the download in a seperate process
        p = multiprocessing.Process(name='arwicbot-downloader', target=worker)
        jobs.append(p)
        p.start()
        await client.send_message(message.channel, "Added song to the server's playlist.")
    except Exception as e:
        pprint(e)
        await client.send_message(message.channel, "Usage: `!queue <youtube-link>`")
