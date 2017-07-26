from modules._base_ import BaseModule, Command
import logging_helper
import discord
import sqlite3
import queue
import re
import multiprocessing
import pafy
import constants
import os
import math
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
import requests


def get_youtube_video_id(url):
    exp = r'(\&|\?)v=(?P<id>[^\&])+'
    m = re.match(exp, url)
    if m:
        return m.group("id")
    return None


def get_youtube_playlist_id(url):
    # yt.com/watch?list=123456&arg2=asd
    # yt.com/watch?v=12345&list=123456&arg2=asd
    exp = r'(\&|\?)list=(?P<id>[^\&])+'
    m = re.match(exp, url)
    if m:
        return m.group("id")
    return None
    

def time_format(length):
    secs = length % 60
    mins = math.floor(length / 60)
    return "{:0>2}:{:0>2}".format(mins, secs)


def get_voice_channel_by_name(server, name):
    for c in server.channels:
        if c.type == discord.ChannelType.voice and c.name.lower() == name.lower():
            return c
    return None


def search_youtube(search_terms):
    query_string = urllib.parse.urlencode({"search_query": search_terms})
    results_page = requests.get("http://www.youtube.com/results?" + query_string)
    soup = BeautifulSoup(results_page.content, 'html.parser')
    atags = soup.select("li > div > div > div.yt-lockup-content > h3 > a")
    timetags = soup.select("div.yt-lockup-thumbnail.contains-addto > a > div > span > span")
    results = []
    for i in range(0, len(atags)):
        atag = atags[i]
        title = atag.text
        href = atag["href"]
        vid_id = re.match(r'/watch\?v=(.{11})', href)
        duration = timetags[i].text
        results.append({
            "title": title,
            "id": vid_id,
            "duration": duration
        })
    return results


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
        # joins or moves to the users current voice channel
        super().register_command(Command("join", self.cmd_join, constants.LEVEL_USER))
        # pauses the player and leaves voice
        super().register_command(Command("leave", self.cmd_leave, constants.LEVEL_USER))
        # always: joins the users current channel
        # no args and paused: starts playback
        # link: queues video or all videos in playlist
        # search terms: returns top 5 search results, subsequent "!play X" plays/queues the given result
        super().register_command(Command("play", self.cmd_play, constants.LEVEL_USER))
        # stops playback, leaves voice, clears playlist
        super().register_command(Command("stop", self.cmd_stop, constants.LEVEL_USER))
        # pauses playback
        super().register_command(Command("pause", self.cmd_pause, constants.LEVEL_USER))
        # plays the next song in the playlist
        super().register_command(Command("skip", self.cmd_skip, constants.LEVEL_USER))
        # prints song currently playing
        super().register_command(Command("nowplaying", self.cmd_now_playing, constants.LEVEL_EVERYONE))

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

    def queue_song(self, server, song_id):
        session = self.get_session(server)
        session.playlist.put(song_id)

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
            args = message.content.split()
            session = self.get_session(message.server)
            should_search = True

            # join the users current voice channel if we arnt already in one
            if not client.is_voice_connected(message.server):
                await client.join_voice_channel(message.author.voice.voice_channel)

            # check if the arg is a youtube link
            if len(args) == 2:
                url = args[1]
                playlist_id = get_youtube_playlist_id(url)
                if playlist_id:
                    pl = pafy.get_playlist(playlist_id)
                    pl_len = len(pl)
                    for vid in pl["items"]:
                        video_id = vid["pafy"].id
                        self.queue_song(message.server, video_id)
                    should_search = False
                    await client.send_message(message.channel, "Music: Added {} song(s) to the server's "
                                                               "playlist".format(pl_len))
                else:
                    video_id = get_youtube_video_id(url)
                    if video_id:
                        self.queue_song(message.server, video_id)
                        should_search = False
                        await client.send_message(message.channel, "Music: Added song to the server's playlist")

            # check if we need to either resume the player or play a new song
            if session.player and not session.player.is_playing():
                # is the player paused?
                if session.current_song_id:
                    session.player.resume()
                    await self.send_now_playing(client, message.channel, session)
                    return
                # or do we need to get a new song from the list
                else:
                    voice = client.voice_client_in(message.server)
                    try:
                        next_song_id = session.playlist.get(block=False)
                    except queue.Empty:
                        await client.send_message(message.channel, "Music: Error: Playlist empty. "
                                                                   "Add songs with `!play <youtube-link>` or "
                                                                   "`!play <search-terms>")
                        return
                    session.player = voice.create_ffmpeg_player(constants.DOWNLOAD_DIR + next_song_id)
                    session.player.start()
                    session.current_song_id = next_song_id
                    await self.send_now_playing(client, message.channel, session)

            # check if the arguments are search terms
            if should_search:
                search_query = message.content[len("!play "):]
                message = await client.send_message(message.channel, "Searching YouTube for \"{}\"...".format(search_query))
                results = search_youtube(search_query)
                msg = "Select a track with !play n:\n"
                index = 1
                for result in results:
                    msg = "{}{}: {} ({})\n".format(msg, index, result["title"], result["duration"])
                    index += 1
                await client.edit_message(message, msg)

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
            # try and pause the player before we leave voice
            session = self.get_session(message.server)
            if session.player and session.player.is_playing():
                session.player.pause()
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
            youtube_id = get_youtube_video_id(args[1])
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
