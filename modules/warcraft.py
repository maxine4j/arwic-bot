from modules._base_ import BaseModule, Command, get_perm_level, set_perm_level, InsufficientPrivilegesException
import logging_helper
import asyncio
import discord
import sqlite3
import constants



class WarcraftModule(BaseModule):
    def __init__(self):
        BaseModule.__init__(self)
        self.logger = logging_helper.init_logger(WarcraftModule.__name__)
        self.db = sqlite3.connect("{}warcraft{}".format(constants.DATA_DIR, constants.DATA_EXT))
        self.db.cursor().execute('''
            CREATE TABLE IF NOT EXISTS config (
                server_id INTEGER NOT NULL,
                default_realm TEXT NOT NULL DEFAULT "frostmourne",
                default_region TEXT NOT NULL DEFAULT "us",
                PRIMARY KEY (server_id));
        ''')
        self.db.commit()
        super().register_command(Command("log link", self.cmd_log_link, constants.LEVEL_EVERYONE))

    def get_config(self, server, var):
        c = self.db.cursor()
        # try get the var
        try:
            c.execute('''
                SELECT {} FROM config WHERE server_id = ?;
            '''.format(var), (server.id,))
            res = c.fetchone()
            return res[0]
        except:
            # insert a new tuple with default values
            c.execute('''
                INSERT INTO config (server_id) VALUES (?);
            ''', (server.id,))
            self.db.commit()
            return self.get_config(server, var)

    async def cmd_log_link(self, client, message):
        '''
        !log link arwic frostmourne us
        '''
        try:
            args = message.content.split()
            if len(args) == 2:
                await client.send_message(message.channel, "Warcraft: Usage `!log link <name> [realm] [region]`")
                return
            elif len(args) == 3:  # !log link arwic
                name = args[2]
                realm = self.get_config(message.server, "default_realm")
                region = self.get_config(message.server, "default_region")
            elif len(args) == 4:  # !log link arwic frostmourne
                name = args[2]
                realm = args[3]
                region = self.get_config(message.server, "default_region")
            else:  # !log link arwic frostmourne us
                name = args[2]
                realm = args[3]
                region = args[4]
            url = "https://www.warcraftlogs.com/character/{}/{}/{}".format(region, realm, name)
            em = discord.Embed(title="Warcraft Logs",
                               description="{} @ {}-{}".format(name.capitalize(), realm.capitalize(), region.capitalize()),
                               url=url,
                               color=constants.COLOR_WARCRAFTLOGS_GREY)
            em.set_thumbnail(url=constants.ICON_WARCRAFTLOGS)
            await client.send_message(message.channel, embed=em)
        except Exception as e:
            self.logger.error("Warcraft: Internal Error: {}".format(e.with_traceback()))
            await client.send_message(message.channel, "Warcraft: Internal Error")
