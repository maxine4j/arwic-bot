from modules._base_ import BaseModule, Command, get_perm_level, set_perm_level, InsufficientPrivilegesException
import logging_helper
import discord
import constants
import sqlite3


role_conn = sqlite3.connect("{}admin{}".format(constants.DATA_DIR, constants.DATA_EXT))
role_conn.cursor().execute('''
CREATE TABLE IF NOT EXISTS potential_roles (
    server_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    PRIMARY KEY (server_id, role_id));
''')


class AdminModule(BaseModule):
    def __init__(self):
        BaseModule.__init__(self)
        self.logger = logging_helper.init_logger(AdminModule.__name__)
        super().register_command(Command("role potential add", self.cmd_potential_add, constants.LEVEL_ADMIN))
        super().register_command(Command("role potential remove", self.cmd_potential_remove, constants.LEVEL_ADMIN))
        super().register_command(Command("role list", self.cmd_role_list, constants.LEVEL_EVERYONE))
        super().register_command(Command("role add", self.cmd_role_add, constants.LEVEL_EVERYONE))
        super().register_command(Command("role remove", self.cmd_role_remove, constants.LEVEL_EVERYONE))

    async def cmd_potential_add(self, client, message):
        try:
            server_id = message.server.id
            if len(message.role_mentions) < 1:
                await client.send_message(message.channel, "Admin: Error: No role @mentioned")
                return
            role_id = message.role_mentions[0].id
            role_name = message.role_mentions[0].name
            role_conn.cursor().execute("INSERT INTO potential_roles VALUES (?, ?)", (server_id, role_id,))
            role_conn.commit()
            await client.send_message(message.channel, "Potential role added: {}".format(role_name))
        except:
            await client.send_message(message.channel, "Admin: Error adding potential role")

    async def cmd_potential_remove(self, client, message):
        try:
            server_id = message.server.id
            if len(message.role_mentions) < 1:
                await client.send_message(message.channel, "Admin: Error: No role @mentioned")
                return
            role_id = message.role_mentions[0].id
            role_name = message.role_mentions[0].name
            role_conn.cursor().execute("DELETE FROM potential_roles WHERE server_id=? AND role_id=?", (server_id, role_id,))
            role_conn.commit()
            await client.send_message(message.channel, "Potential role removed: {}".format(role_name))
        except:
            await client.send_message(message.channel, "Admin: Error removing potential role")

    async def cmd_role_list(self, client, message):
        try:
            server_id = message.server.id
            db_roles = role_conn.cursor().execute("SELECT role_id FROM potential_roles WHERE server_id=?", (server_id,)).fetchall()
            final_message = "Potential roles:\n```\n"
            role_names = []
            for server_role in message.server.role_hierarchy:
                for db_role in db_roles:
                    if int(server_role.id) == db_role[0]:
                        role_names.append(server_role.name)
                        final_message = final_message + server_role.name + "\n"
            final_message = final_message + "```"
            await client.send_message(message.channel, final_message)
        except:
            await client.send_message(message.channel, "Admin: Error removing potential role")

    async def cmd_role_add(self, client, message):
        try:
            if len(message.role_mentions) < 1:
                await client.send_message(message.channel, "Admin: Error: No role @mentioned")
                return
            if len(message.role_mentions) != 1:
                await client.send_message(message.channel, "Admin: Error: You may only @mention one role")
                return
            role = message.role_mentions[0]
            server_id = message.server.id
            db_res = role_conn.cursor().execute(
                "SELECT role_id FROM potential_roles WHERE server_id=? AND role_id=? LIMIT 1", (server_id, role.id,)).fetchall()
            if len(db_res) != 1:
                await client.send_message(message.channel, "Admin: Error: Role not assignable: {}".format(role.name))
                return
            await client.add_roles(message.author, role)
            await client.send_message(message.channel, "Admin: Role added: {}".format(role.name))
        except:
            await client.send_message(message.channel, "Admin: Error adding role")

    async def cmd_role_remove(self, client, message):
        try:
            if len(message.role_mentions) < 1:
                await client.send_message(message.channel, "Admin: Error: No role @mentioned")
                return
            if len(message.role_mentions) != 1:
                await client.send_message(message.channel, "Admin: Error: You may only @mention one role")
                return
            role = message.role_mentions[0]
            server_id = message.server.id
            db_res = role_conn.cursor().execute(
                "SELECT role_id FROM potential_roles WHERE server_id=? AND role_id=? LIMIT 1", (server_id, role.id,)).fetchall()
            if len(db_res) != 1:
                await client.send_message(message.channel, "Admin: Error: Role not assignable: {}".format(role.name))
                return
            await client.remove_roles(message.author, role)
            await client.send_message(message.channel, "Admin: Role removed: {}".format(role.name))
        except:
            await client.send_message(message.channel, "Admin: Error removing role")
