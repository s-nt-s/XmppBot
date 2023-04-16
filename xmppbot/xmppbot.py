# -*- coding: utf-8 -*-
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

"""
A framework for writing Jabber/XMPP bots.
The XmppBot framework allows you to easily write bots
that use the XMPP protocol. You can create commands by
decorating functions in your subclass or customize the
bot's operation completely.
"""

import logging
import re
from functools import cached_property
from slixmpp.exceptions import XMPPError

from .cmdbot import CmdBot
from .basebot import BaseBot, Message

logger = logging.getLogger(__name__)

re_sp = re.compile(r"\s+", re.MULTILINE | re.UNICODE)
url_img = re.compile(r"(https?://\S+\.(gif|png|jpe?g)\S*)", re.IGNORECASE)


class XmppBot(BaseBot):
    MSG_ERROR_OCCURRED = "ERROR!!"

    def __init__(self, config_path):
        super().__init__(config_path)
        self.commands = self.__get_commands()
        self.__validate()

        self.nick = self.config.user.split("@")[0]

        self.auto_reconnect = True
        if self.config.friendly:
            self.auto_authorize = True
            self.auto_subscribe = True

        if 'xep_0203' not in self.config.plugins and self.allow_delay:
            # XMPP Delayed messages
            self.config.plugins = self.config.plugins + ('xep_0203', )

        for plugin in self.config.plugins:
            self.register_plugin(plugin)

        self.add_event_handler("session_start", self.start)
        self.add_event_handler("message", self.read_message)
        self.add_event_handler("groupchat_subject", self.groupchat_subject)

    def __get_commands(self):
        commands: list[CmdBot] = []
        for k, v in self.__class__.__dict__.items():
            cmd = getattr(v, 'cmd', None)
            if isinstance(cmd, CmdBot):
                commands.append(cmd)
        commands = sorted(commands, key=lambda x: x.index)
        for c in commands:
            logger.info(f'Registered {c.index}º command: ' + " ".join(c.names))
        return tuple(commands)

    def __validate(self):
        if not self.config.lisent:
            raise Exception("This bot need lisent != None")
        if not self.commands:
            raise Exception("This bot need commands")

    @cached_property
    def allow_delay(self) -> bool:
        for c in self.commands:
            if c.delay is True:
                return True
        return False

    async def start(self, event):
        self.send_presence()
        await self.get_roster()
        await self.__set_vcard()
        await self.__set_avatar()
        self.__join_rooms()

    async def __set_vcard(self):
        if self.config.vcard is None:
            return
        vcard = self.xep_0054.stanza.VCardTemp()
        vcard['JABBERID'] = self.boundjid.bare
        for k, v in self.config.vcard.items():
            vcard[k] = v
            if k.upper() == 'NICKNAME':
                self.nick = v
        await self.xep_0054.publish_vcard(vcard)

    async def __set_avatar(self):
        if self.config.avatar is None:
            return
        avatar = self.config.avatar
        avatar_metadata = {
            'id': self.xep_0084.generate_id(avatar.content),
            'type': avatar.mtype,
            'bytes': len(avatar.content)
        }

        used_xep84 = False
        result = await self.xep_0084.publish_avatar(avatar.content)
        if isinstance(result, XMPPError):
            logger.debug('Could not publish XEP-0084 avatar')
        else:
            used_xep84 = True

        result = await self.xep_0153.set_avatar(
            avatar=avatar.content,
            mtype=avatar.mtype
        )
        if isinstance(result, XMPPError):
            logger.debug('Could not set vCard avatar')

        if used_xep84:
            result = await self.xep_0084.publish_avatar_metadata(
                items=[avatar_metadata]
            )
            if isinstance(result, XMPPError):
                logger.debug('Could not publish XEP-0084 metadata')

        # Wait for presence updates to propagate...
        # self.schedule('end', 5, self.disconnect, kwargs={'wait': True})

    def __join_rooms(self):
        for room in self.config.rooms:
            self.xep_0045.join_muc(room, self.nick)
            msg = self.joined_room(room)
            if msg:
                self.send_message(mto=room, mbody=msg, mtype='groupchat')

    def joined_room(self, room):
        pass

    def groupchat_subject(self, data):
        pass

    def read_message(self, msg):
        msg: Message = Message.init(msg)
        if self.__discard_message(msg):
            return
        cmd = self.__get_command(msg)
        if cmd is None:
            logger.debug(f"Unknown command from {msg.sender}: {msg.text}")
            return
        logger.debug(f"Command from {msg.sender}: {msg.text}")

        try:
            reply = cmd.run(self, msg)
        except Exception as error:
            logger.exception(
                'An error happened while processing the message: ' +
                msg.text)
            reply = self.command_error(msg, error)
        if reply:
            self.reply_message(msg, reply)

    def __discard_message(self, msg):
        if self.__is_weird_message(msg):
            return True
        if self.__is_from_me(msg):
            return True
        if not self.__is_in_my_inbox(msg):
            return True
        return False

    def __is_weird_message(self, msg):
        if not msg['body'] or (msg['from'] is None or not str(msg['from'])):
            return True
        txt = re_sp.sub(" ", msg['body']).strip()
        if len(txt) == 0:
            return True
        return False

    def __is_from_me(self, msg):
        if msg['type'] == 'groupchat' and msg['from'].resource.lower(
        ) == self.nick.lower():
            return True
        user = msg['from'].bare
        if user == self.boundjid.bare:
            return True
        return False

    def __is_in_my_inbox(self, msg):
        if msg['type'] not in self.config.lisent:
            return False
        user = msg['from'].bare
        if self.config.roster and user not in self.config.roster:
            return False
        return True

    def __get_command(self, msg) -> CmdBot:
        for cmd in self.commands:
            if cmd.is_for_me(msg):
                return cmd
        return None

    def command_error(self, msg, error):
        return self.MSG_ERROR_OCCURRED

    def tune_reply(self, txt):
        return txt

    def reply_message(self, msg, txt):
        reply = self.tune_reply(txt)
        msgreply = msg.reply(reply)
        msgreply.send()
        if self.config.img_to_oob:
            imgs = set([i[0] for i in url_img.findall(txt)])
            for i in imgs:
                imgreply = msg.reply()
                imgreply['oob']['url'] = i
                imgreply.send()
