import discord
import asyncio
import logging
import sqlite3
import os
import constants
import logging_helper



logger = logging_helper.init_logger("PermissionsModule")
dev_ids = [
    "202130533713575936",
    "313663820822216705"
]

# load/create levels database
perm_conn = sqlite3.connect("{}permissions{}".format(constants.DATA_DIR, constants.DATA_EXT))
perm_conn.cursor().execute('''
CREATE TABLE IF NOT EXISTS levels (
    user_id INTEGER NOT NULL, 
    server_id INTEGER NOT NULL,
    level INTEGER NOT NULL,
    PRIMARY KEY (user_id, server_id));
''')


class InsufficientPrivilegesException(Exception):
    def __init__(self, msg):
        self.msg = msg


def get_perm_level(server, user):
    # try and get the users level
    c = perm_conn.cursor()
    c.execute("SELECT level FROM levels WHERE user_id = ? AND server_id = ?", (user.id, server.id))
    res = c.fetchone()
    # if the user doesnt have a level, give them one
    if res is None:
        level = constants.LEVEL_EVERYONE
        if user.id in dev_ids:
            # if the user is a dev, give them the dev level
            level = constants.LEVEL_DEV
        elif server.owner == user:
            # if the user is the server owner, give them the owner level
            level = constants.LEVEL_OWNER
        c.execute("INSERT INTO levels VALUES (?, ?, ?)", (user.id, server.id, level))
        perm_conn.commit()
        logger.info("Added new permission level entry: User: '{}', Server: '{}', Level: '{}'".format(user.name, server.name, level))
        return level
    return res[0]
    
    
def set_perm_level(server, target_user, level, current_user):
    current_user_level = get_perm_level(server, current_user)
    target_user_level = get_perm_level(server, target_user)
    # dont let a user promote another user to their current level or above
    if level > current_user_level:
        raise InsufficientPrivilegesException("Desired level ({}) must be less than your level ({})".format(level, current_user_level))
    # dont let users be promoted to/above the server owner
    if level >= constants.LEVEL_OWNER:
        raise InsufficientPrivilegesException("You cannot promote a user to/above the server owner ({})".format(constants.LEVEL_OWNER))
    # set the users level
    perm_conn.cursor().execute("UPDATE levels SET level = ? WHERE user_id = ? AND server_id = ?", (level, target_user.id, server.id))
    perm_conn.commit()
    logger.info("Updated permission level entry: User: '{}', Server: '{}', Level: '{}'".format(target_user.name, server.name, level))


class Command():
    def __init__(self, trigger, func, level):
        self.trigger = trigger
        self.func = func
        self.level = level
    
    async def run(self, client, message):
        if get_perm_level(message.server, message.author) >= self.level:
            await self.func(client, message)
        else:
            raise InsufficientPrivilegesException("Insufficient Privileges. Requires level {}, you have level {}".format(self.level, get_perm_level(message.server, message.author)))


class BaseModule():
    def __init__(self):
        self.commands = []
        
    def register_command(self, command):
        self.commands.append(command)
        
    async def try_run_command(self, prefix, client, message):
        res = False
        for cmd in self.commands:
            if message.content.startswith("{}{}".format(prefix, cmd.trigger)):
                res = True
                await cmd.run(client, message)
        return res
