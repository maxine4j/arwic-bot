from modules._base_ import BaseModule, Command, get_perm_level, set_perm_level, InsufficientPrivilegesException
import logging_helper
import discord
import constants
import shlex


class EmbedModule(BaseModule):
    def __init__(self):
        BaseModule.__init__(self)
        self.logger = logging_helper.init_logger(EmbedModule.__name__)
        super().register_command(Command("embed", self.cmd_embed, constants.LEVEL_MOD))

    async def cmd_embed(self, client, message):
        # !embed <channel> "<title>" "<desc>" <image-url> ["<field-name>" "<field-value>" <field-inline>]+
        try:
            args = shlex.split(message.content)
            # channel_name, title, desc
            if len(args) < 4:
                await client.send_message(message.channel, 'Embed: Usage: `!embed <channel> "<title>" "<desc>" <image-url>`')
                return
            channel_name = args[1]
            title = args[2]
            desc = args[3]
            em = discord.Embed(title=title, description=desc, color=discord.Color.red())
            em.set_author(name=message.author.display_name, icon_url=message.author.avatar_url)
            # channel_name, title, desc, image
            if len(args) == 5:
                em.set_image(url=args[4])
            channel = None
            for c in message.server.channels:
                if c.name == channel_name and c.type == discord.ChannelType.text:
                    channel = c
            await client.send_message(channel or message.channel, embed=em)
        except Exception as e:
            import pprint
            pprint.pprint(e)
            self.logger.error("Error creating embedded message (server: {}): {}".format(message.server.id, e))
            await client.send_message(message.channel,
                'Embed: Usage: `!embed <channel> "<title>" "<desc>" <image-url>`')
