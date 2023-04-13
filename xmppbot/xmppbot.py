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

import inspect
import os
import re
import asyncio
from functools import cache, cached_property
from slixmpp.exceptions import XMPPError

from .botcmd import CmdBot
from .basebot import BaseBot, Message

re_sp = re.compile(r"\s+", re.MULTILINE | re.UNICODE)
url_img = re.compile(r"(https?://\S+\.(gif|png|jpe?g)\S*)", re.IGNORECASE)

class XmppBot(BaseBot):
    MSG_ERROR_OCCURRED = "ERROR!!"

    def __init__(self, config_path):
        super().__init__(config_path)
        self.commands = self._get_commands()
        self.use_ipv6 = self.config.get("use_ipv6", True)
        self.delay = False
        self.nick = self.config['user'].split("@")[0]

        self.auto_reconnect = True
        if self.config.get("auto", False):
            self.auto_authorize = True
            self.auto_subscribe = True

        plugins = set(self.config.get("plugins", "").split())
        plugins.add('xep_0030')  # Service Discovery
        plugins.add('xep_0004')  # Data Forms
        plugins.add('xep_0060')  # PubSub
        plugins.add('xep_0199')  # XMPP Ping
        if self.allow_delay:
            plugins.add('xep_0203')  # XMPP Delayed messages
        if self.config.get('vcard', None):
            plugins.add('xep_0054')
        if self.config.get('avatar', None):
            if os.path.isfile(self.config['avatar']):
                plugins.add('xep_0084')
                plugins.add('xep_0153')
            else:
                del self.config['avatar']

        if self.config.get('rooms', None):
            plugins.add('xep_0045')  # Multi-User Chat

        if self.config.get('img_to_oob', False):
            plugins.add('xep_0066')  # OOB

        for plugin in plugins:
            self.register_plugin(plugin)

        self.add_event_handler("session_start", self.start)
        self.add_event_handler("message", self.read_message)
        self.add_event_handler("groupchat_subject", self.groupchat_subject)

        self.custom_roster = self.config.get('roster')

        if not self.config.get('lisent'):
            self.config['lisent'] = ['chat', 'normal']
            if self.config.get('rooms', None):
                self.config['lisent'].append('groupchat')

    def _get_commands(self):
        commands = []
        for k, v in self.__class__.__dict__.items():
            if isinstance(getattr(v, 'cmd', None), CmdBot):
               commands.append(getattr(self, k))
        commands = sorted(commands, key=lambda x: x.cmd.index)
        for command in commands:
            self.log.info('Registered %dº command: %s' %
                          (command.cmd.index, " ".join(command.cmd.names)))
        return tuple(commands)

    @cached_property
    def allow_delay(self) -> bool:
        for c in self.commands:
            if c.cmd.delay is True:
                return True
        return False

    async def start(self, event):
        self.send_presence()
        await self.get_roster()
        await self.set_vcard()
        await self.set_avatar()
        self.join_rooms()
    
    async def set_vcard(self):
        if self.config.get('vcard', None) is None:
            return
        vcard = self['xep_0054'].stanza.VCardTemp()
        vcard['JABBERID'] = self.boundjid.bare
        for f in self.config['vcard']:
            vcard[f] = self.config['vcard'][f]
            if f.upper() == 'NICKNAME':
                self.nick = self.config['vcard'][f]
        await self['xep_0054'].publish_vcard(vcard)

    async def set_avatar(self):
        if self.config.get('avatar', None) is None:
            return
        avatar = None
        try:
            with open(self.config['avatar'], 'rb') as avatar_file:
                avatar = avatar_file.read()
        except IOError:
            self.log.debug('Could not load avatar')
            return
        ext = os.path.splitext(self.config['avatar'])[1][1:]
        avatar_type = 'image/' + ext
        avatar_id = self['xep_0084'].generate_id(avatar)
        avatar_metadata = {
            'id': avatar_id,
            'type': avatar_type,
            'bytes': len(avatar)
        }

        used_xep84 = False
        result = await self['xep_0084'].publish_avatar(avatar)
        if isinstance(result, XMPPError):
            self.log.debug('Could not publish XEP-0084 avatar')
        else:
            used_xep84 = True

        result = await self['xep_0153'].set_avatar(avatar=avatar, mtype=avatar_type)
        if isinstance(result, XMPPError):
            self.log.debug('Could not set vCard avatar')

        if used_xep84:
            result = await self['xep_0084'].publish_avatar_metadata(items=[avatar_metadata])
            if isinstance(result, XMPPError):
                self.log.debug('Could not publish XEP-0084 metadata')

        # Wait for presence updates to propagate...
        # self.schedule('end', 5, self.disconnect, kwargs={'wait': True})

    def join_rooms(self):
        for room in self.config.get('rooms', []):
            self.plugin['xep_0045'].joinMUC(room, self.nick, wait=True)
            msg = self.joined_room(room)
            if msg:
                self.send_message(mto=room, mbody=msg, mtype='groupchat')

    def joined_room(self, room):
        pass

    def groupchat_subject(self, data):
        pass

    def read_message(self, msg):
        if self.discard_message(msg):
            return
        msg.__class__ = Message

        cmd = self.get_command(msg)
        if cmd is None:
            self.log.debug("Unknown command from %s: %s" % (msg.sender, msg.text))
            return

        self.log.debug("Command from %s: %s" % (msg.sender, msg.text))

        try:
            reply = cmd(msg)
        except Exception as error:
            self.log.exception('An error happened while processing the message: %s' % msg.text)
            reply = self.command_error(msg, error)
        if reply:
            self.reply_message(msg, reply)

    def discard_message(self, msg):
        if msg['type'] not in self.config['lisent'] or not msg['body'] or not msg['from']:
            return True
        if msg['type'] == 'groupchat' and msg['from'].resource.lower() == self.nick.lower():
            return True

        user = msg['from'].bare
        if user == self.boundjid.bare or (self.custom_roster and user not in self.custom_roster):
            return True

        txt = re_sp.sub(" ", msg['body']).strip()
        if len(txt) == 0:
            return True
        
        return False
    
    def get_command(self, msg):
        for c in self.commands:
            if c.cmd.is_for_me(msg):
                return c
        return None

    def command_error(self, msg, error):
        return self.MSG_ERROR_OCCURRED

    def tune_reply(self, txt):
        return txt

    def reply_message(self, msg, txt):
        msgreply = msg.reply(self.tune_reply(txt))
        _to = msgreply['to']
        msgreply.send()
        if self.config.get('img_to_oob', False):
            imgs = set([i[0] for i in url_img.findall(txt)])
            for i in imgs:
                imgreply = msg.reply()
                imgreply['to'] = _to
                imgreply['oob']['url'] = i
                imgreply.send()

