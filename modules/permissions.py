from modules._base_ import BaseModule, Command, get_perm_level, set_perm_level, InsufficientPrivilegesException
import logging_helper
import asyncio
import discord
import sqlite3
import constants



class PermissionsModule(BaseModule):
    def __init__(self):
        BaseModule.__init__(self)
        self.logger = logging_helper.init_logger(PermissionsModule.__name__)
        super().register_command(Command("set-level", self.cmd_set_level, constants.LEVEL_MOD))
        super().register_command(Command("get-level", self.cmd_get_level, constants.LEVEL_EVERYONE))


    async def cmd_set_level(self, client, message):
        '''
        Sets a users permission level
        '''
        try:
            # parse arguments
            args = message.content.split()
            target = message.mentions[0]
            level = int(args[2])
            # update the db
            try:
                self.logger.debug("BEFORE SET PERM")
                set_perm_level(message.server, message.author, level, message.author)
                self.logger.debug("DONE")
                self.logger.debug("BEFORE SEND MSG")
                await client.send_message(message.channel, "Permissions: User {} now has permission :binking: level ~~{}~~ ➜ {}".format(target.mention, level))
                self.logger.debug("DONE")
            except InsufficientPrivilegesException as ipe:
                await client.send_message(message.channel, "Permissions: {}".format(ipe.msg))
        except Exception as e:
            self.logger.error("Error setting user level (server: {}): {}".format(message.server.id, e))
            await client.send_message(message.channel, "Usage: `!set-level <user-mention> <level>`\n"\
                                                       "Where level is {} (everyone), {} (user), {} (moderator), {} (admin)".format(
                                                       constants.LEVEL_EVERYONE, constants.LEVEL_USER, constants.LEVEL_MOD, constants.LEVEL_ADMIN))


    async def cmd_get_level(self, client, message):
        '''
        Gets a users permission level
        '''
        try:
            if len(message.mentions) == 0:
                target_user = message.author
            elif len(message.mentions) == 1:
                target_user = message.mentions[0]
            else:
                raise Exception
            level = get_perm_level(message.server, target_user)
            await client.send_message(message.channel, "User {} has permission level {}".format(target_user.mention, level))
        except Exception as e:
            self.logger.error("Error getting user level (server: {}): {}".format(message.server.id, e))
            await client.send_message(message.channel, "Usage: `!get-level <user-mention>")
