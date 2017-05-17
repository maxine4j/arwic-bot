import discord
import asyncio
import logging
import sqlite3


logger = logging.getLogger("arwicbot")

LEVEL_DEV = 4
LEVEL_OWNER = 3
LEVEL_MOD = 2
LEVEL_USER = 1
LEVEL_EVERYONE = 0

dev_ids = [
    "202130533713575936"
]

# load/create levels database
conn = sqlite3.connect("permissions.db")
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS levels (
    user_id INTEGER NOT NULL, 
    server_id INTEGER NOT NULL,
    level INTEGER NOT NULL,
    PRIMARY KEY (user_id, server_id));
''')


def _get_level(server, user):
    # try and get the users level
    c = conn.cursor()
    c.execute("SELECT level FROM levels WHERE user_id = ? AND server_id = ?", (user.id, server.id))
    res = c.fetchone()
    # if the user doesnt have a level, give them one
    if res is None:
        level = LEVEL_EVERYONE
        if user.id in dev_ids:
            # if the user is a dev, give them the dev level
            level = LEVEL_DEV
        elif server.owner == user:
            # if the user is the server owner, give them the owner level
            level = LEVEL_OWNER
        c.execute("INSERT INTO levels VALUES (?, ?, ?)", (user.id, server.id, level))
        conn.commit()
        logger.info("Added new permission entry: User: '{}', Server: '{}', Level: '{}'".format(user.name, server.name, level))
        return level
    return res[0]


def has_permission(server, user, level):
    return _get_level(server, user) >= level


async def cmd_set_level(client, message):
    '''
    Sets a users permission level
    '''
    try:
        # parse arguments
        args = message.split()
        level = args[1]
        # update the db
        c = conn.cursor()
        c.execute("SELECT level FROM levels WHERE user_id = ? AND server_id = ?", (user.id, server.id))
        res = c.fetchone()
    except Exception as e:
        logger.error("Error setting user level (server: {}): {}".format(message.server.id, e))
        await client.send_message(message.channel, "Usage: `!set-level <user-mention> <level>` where level is 0 (everyone), 1 (user), 2 (moderator)")


async def cmd_get_level(client, message):
    '''
    Gets a users permission level
    '''
    try:
        logger.debug("Mentions = {}".format(message.mentions))
        if len(message.mentions) == 0:
            target_user = message.author
        elif len(message.mentions) == 1:
            target_user = message.mentions[0]
        else:
            raise Exception
        level = _get_level(message.server, target_user)
        await client.send_message(message.channel, "User @{}#4477 has permission level {}".format(message.author.name, level))
    except Exception as e:
        logger.error("Error getting user level (server: {}): {}".format(message.server.id, e))
        await client.send_message(message.channel, "Usage: `!get-level <user-mention>")
