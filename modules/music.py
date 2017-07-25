from modules._base_ import BaseModule, Command
import logging_helper
import asyncio
import discord
import sqlite3
import queue
import re
import multiprocessing
import pafy
import constants
import os
import math


def get_youtube_id(url):
    youtube_regex = (
        r'(https?://)?(www\.)?'
        '(youtube|youtu|youtube-nocookie)\.(com|be)/'
        '(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
    youtube_regex_match = re.match(youtube_regex, url)
    if youtube_regex_match:
        return youtube_regex_match.group(6)
    return youtube_regex_match
    

def time_format(length):
    secs = length % 60
    mins = math.floor(length / 60)
    return "{:0>2}:{:0>2}".format(mins, secs)


class MusicModule(BaseModule):
    class MusicSession:
        def __init__(self, server):
            self.server = server
            self.player = None
            self.playlist = queue.Queue()
            self.current_song_id = None

    def __init__(self):
        BaseModule.__init__(self)
        self.logger = logging_helper.init_logger(MusicModule.__name__)
        self.sessions = {}
        self.downloader_jobs = []
        self.db = sqlite3.connect("{}music{}".format(constants.DATA_DIR, constants.DATA_EXT))
        self.db.cursor().execute('''
            CREATE TABLE IF NOT EXISTS music (
                id VARCHAR(11) NOT NULL,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                length INTEGER NOT NULL,
                date TEXT NOT NULL,
                thumb_s TEXT NOT NULL,
                thumb_m TEXT NOT NULL,
                thumb_l TEXT NOT NULL,
                PRIMARY KEY (id));
        ''')
        self.db.commit()
        super().register_command(Command("join", self.cmd_join, constants.LEVEL_USER))
        super().register_command(Command("leave", self.cmd_leave, constants.LEVEL_USER))
        super().register_command(Command("play", self.cmd_play, constants.LEVEL_USER))
        super().register_command(Command("stop", self.cmd_stop, constants.LEVEL_USER))
        super().register_command(Command("pause", self.cmd_pause, constants.LEVEL_USER))
        super().register_command(Command("skip", self.cmd_skip, constants.LEVEL_USER))
        super().register_command(Command("queue", self.cmd_queue, constants.LEVEL_USER))
        super().register_command(Command("now-playing", self.cmd_now_playing, constants.LEVEL_EVERYONE))

    def download_video(self, id):
        # check if the video has already been downloaded
        if os.path.isfile(constants.DOWNLOAD_DIR + id):
            return
        # multiprocess worker
        def worker():
            # get video info
            video = pafy.new(id)
            # update database
            self.db.cursor().execute('''
                INSERT INTO music VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            ''',
            (video.videoid, video.title, video.author, video.length,
            video.published, video.thumb, video.bigthumb, video.bigthumbhd))
            self.db.commit()
            # download the best audio stream
            self.logger.info("Downloading {} by {} ({})".format(video.title, video.author, id))
            audio_stream = video.getbestaudio()
            audio_stream.download(filepath="{}{}".format(constants.DOWNLOAD_DIR, id), quiet=True)
        # start the download in a seperate process
        p = multiprocessing.Process(name='arwicbot-music-downloader', target=worker)
        self.downloader_jobs.append(p)
        p.start()

    def get_session(self, server):
        # try get a session
        if server.id in self.sessions:
            return self.sessions[server.id]
        # make a new one if none exist for this server
        self.sessions[server.id] = MusicModule.MusicSession(server)
        return self.sessions[server.id]
        
    async def send_now_playing(self, client, channel, session):
        def query_db(song_id):
            cursor = self.db.cursor()
            cursor.execute('''
                SELECT title, author, length, thumb_s FROM music WHERE id = ?;
            ''', (song_id,))
            res = cursor.fetchone()
            if res is None:
                return None
            else:
                return res[0], res[1], res[2], res[3]

        if session.current_song_id is None:
            await client.send_message(channel, "Music: Nothing playing")
            return
        title, author, length, thumbnail = query_db(session.current_song_id)
        if title is None:
            await client.send_message(channel, "Music: Nothing playing")
            return
        # add embed
        em = discord.Embed(title="Now Playing: {} ({})".format(title, time_format(length)),
                           description=author,
                           colour=constants.COLOR_YOUTUBE_RED,
                           url="https://www.youtube.com/watch?v={}".format(session.current_song_id))
        em.set_author(name="Youtube Music Bot", icon_url=constants.ICON_YOUTUBE)
        em.set_thumbnail(url=thumbnail)
        # add up next
        if len(session.playlist.queue) >= 2:
            title1, author1, length1, thumbnail1 = query_db(session.playlist.queue[0])
            title2, author2, length2, thumbnail2 = query_db(session.playlist.queue[1])
            em.add_field(name="Up Next: {}".format(title1), value="{}".format(author1), inline=True)
            em.add_field(name="Up Next: {}".format(title2), value="{}".format(author2), inline=True)
        elif len(session.playlist.queue) >= 1:
            title1, author1, length1, thumbnail1 = query_db(session.playlist.queue[0])
            em.add_field(name="Up Next: {}".format(title1), value="{}".format(author1), inline=True)
        await client.send_message(channel, embed=em)

    async def cmd_play(self, client, message):
        try:
            # check if we are in a voice channel
            if not client.is_voice_connected(message.server):
                await client.send_message(message.channel, "Music: Error: Not in voice channel")
                return
            # check if a song is already playing
            session = self.get_session(message.server)
            if session.current_song_id is not None and session.player.is_playing():
                await client.send_message(message.channel, "Music: Error: Song already playing")
                return
            # check if we need to resume a song that was paused
            if session.current_song_id is not None and not session.player.is_playing():
                session.player.resume()
                await self.send_now_playing(client, message.channel, session)
                return
            # play the next song in the queue
            voice = client.voice_client_in(message.server)
            try:
                next_song_id = session.playlist.get(block=False)
            except queue.Empty:
                await client.send_message(message.channel, "Music: Error: Playlist empty. Add songs with `!queue <youtube-link>`")
                return
            session.player = voice.create_ffmpeg_player(constants.DOWNLOAD_DIR + next_song_id)
            session.player.start()
            session.current_song_id = next_song_id
            await self.send_now_playing(client, message.channel, session)
        except Exception as e:
            self.logger.error(e)
            await client.send_message(message.channel, "Music: Internal Error")

    async def cmd_skip(self, client, message):
        try:
            # check if we are in a voice channel
            if not client.is_voice_connected(message.server):
                await client.send_message(message.channel, "Music: Error: Not in voice channel")
                return
            # stop the player
            session = self.get_session(message.server)
            try:
                session.player.stop()
                session.player = None
                session.current_song_id = None
            except:
                pass
            # play the next song in the queue
            voice = client.voice_client_in(message.server)
            try:
                next_song_id = session.playlist.get(block=False)
            except queue.Empty:
                await client.send_message(message.channel, "Music: Error: Playlist empty. Add songs with `!queue <youtube-link>`")
                return
            session.player = voice.create_ffmpeg_player(constants.DOWNLOAD_DIR + next_song_id)
            session.player.start()
            session.current_song_id = next_song_id
            await self.send_now_playing(client, message.channel, session)
        except Exception as e:
            self.logger.error(e)
            await client.send_message(message.channel, "Music: Internal Error")

    async def cmd_stop(self, client, message):
        try:
            session = self.get_session(message.server)
            try:
                session.player.stop()
            except:
                pass
            session.player = None
            session.current_song_id = None
            await client.send_message(message.channel, "Music: Stopped Playback")
        except Exception as e:
            self.logger.error(e)
            await client.send_message(message.channel, "Music: Internal Error")

    async def cmd_pause(self, client, message):
        try:
            session = self.get_session(message.server)
            try:
                if session.player and session.player.is_playing():
                    session.player.pause()
                    await client.send_message(message.channel, "Music: Paused Playback")
                    return
                else:
                    await client.send_message(message.channel, "Music: Nothing Playing")
                    return
            except:
                pass
            session.player = None
            session.current_song_id = None
        except Exception as e:
            self.logger.error(e)
            await client.send_message(message.channel, "Music: Internal Error")

    async def cmd_now_playing(self, client, message):
        session = self.get_session(message.server)
        await self.send_now_playing(client, message.channel, session)

    async def cmd_join(self, client, message):
        try:
            args = message.content.split()
            # get the target channel
            target_channel = None
            if len(args) == 1:  # i.e. "!join"
                # try get the users current voice channel
                if message.author.voice.voice_channel is None:
                    # user isnt in a voice channel
                    await client.send_message(message.channel, "Music: Usage: `!join` (you must be in a voice channel) or `!join <channel-name>`")
                    return
                target_channel = message.author.voice.voice_channel
            elif len(args) > 1:  # i.e. "!join general"
                # try get the voice channel the user specified by name
                for c in message.server.channels:
                    if c.type == discord.ChannelType.voice and c.name.lower() == args[1].lower():
                        target_channel = c
                        break
            # join or move to the target channel
            voice = client.voice_client_in(message.server)
            if voice is None:
                await client.join_voice_channel(target_channel)
                await client.send_message(message.channel, "Music: Joined voice channel: {}".format(target_channel.name))
                return
            else:
                await voice.move_to(target_channel)
                await client.send_message(message.channel, "Music: Moved to voice channel: {}".format(target_channel.name))
                return
        except Exception as e:
            # log the error, and notify the user
            self.logger.error(e)
            await client.send_message(message.channel, "Music: Internal Error")

    async def cmd_leave(self, client, message):
        try:
            # check if we are in a channel
            if not client.is_voice_connected(message.server):
                await client.send_message(message.channel, "Music: Error: Not in a voice channel")
                return
            # leave the channel
            voice = client.voice_client_in(message.server)
            last_channel = voice.channel
            await voice.disconnect()
            await client.send_message(message.channel, "Music: Left voice channel: {}".format(last_channel.name))
        except Exception as e:
            # log the error, and notify the user
            self.logger.error(e)
            await client.send_message(message.channel, "Music: Internal Error")

    async def cmd_queue(self, client, message):
        try:
            # get arguments
            args = message.content.split()
            if len(args) < 2:
                raise Exception
            # determine play count
            play_count = 1
            if len(args) == 3:
                # format -> !queue link count
                play_count = int(args[2])
            # check if the arg is a youtube link
            youtube_id = get_youtube_id(args[1])
            if youtube_id is None:
                await client.send_message(message.channel, "Music: Error: Invalid link")
                return
            # add the song to the server's queue
            session = self.get_session(message.server)
            for c in range(play_count):
                session.playlist.put(youtube_id)
            self.download_video(youtube_id)
            await client.send_message(message.channel, "Music: Added song to the server's playlist")
        except Exception as e:
            self.logger.error(e)
            await client.send_message(message.channel, "Usage: `!queue <youtube-link>`")
