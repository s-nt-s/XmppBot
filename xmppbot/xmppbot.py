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
import sys

import slixmpp

from .basebot import BaseBot

sp = re.compile(r"\s+", re.MULTILINE | re.UNICODE)
url_img = re.compile(r"(https?://\S+\.(gif|png|jpe?g)\S*)", re.IGNORECASE)

if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf8')

creator_order = 0


def botcmd(*args, **kwargs):
    """Decorator for bot command functions"""
    global creator_order

    def decorate(func, creator_order, name=None, names=None, delay=False, fromuser=None, regex=None, rg_mode="match"):
        setattr(func, '_command', True)
        setattr(func, '_command_names', names or [name or func.__name__])
        setattr(func, '_command_delay', delay)
        setattr(func, '_command_fromuser', fromuser)
        setattr(func, '_command_regex', regex)
        setattr(func, '_command_rg_mode', rg_mode)
        setattr(func, '_command_order', creator_order)
        return func

    creator_order += 1

    if len(args):
        return decorate(args[0], creator_order, **kwargs)
    else:
        return lambda func: decorate(func, creator_order, **kwargs)


class XmppBot(BaseBot):
    MSG_ERROR_OCCURRED = "ERROR!!"

    def __init__(self, config_path):
        super().__init__(config_path)
        self.use_ipv6 = self.config.get("use_ipv6", True)
        self.delay = False
        self.commands = []
        rg_commands = []
        plugins = set(self.config.get("plugins", "").split())

        commands = inspect.getmembers(self, inspect.ismethod)
        commands = filter(lambda x: getattr(x[1], '_command', False), commands)
        commands = sorted(
            commands, key=lambda x: getattr(x[1], '_command_order'))

        for name, value in commands:
            names = getattr(value, '_command_names')
            order = getattr(value, '_command_order', 0)
            self.log.info('Registered %dº command: %s' %
                          (order, " ".join(names)))
            self.commands.append(value)
            self.delay = self.delay or getattr(value, '_command_delay', False)

        self.nick = self.config['user'].split("@")[0]

        self.auto_reconnect = True
        if self.config.get("auto", False):
            self.auto_authorize = True
            self.auto_subscribe = True

        plugins.add('xep_0030')  # Service Discovery
        plugins.add('xep_0004')  # Data Forms
        plugins.add('xep_0060')  # PubSub
        plugins.add('xep_0199')  # XMPP Ping
        if self.delay:
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

    def start(self, event):
        self.send_presence()
        self.get_roster()
        if self.config.get('vcard', None):
            vcard = self['xep_0054'].stanza.VCardTemp()
            vcard['JABBERID'] = self.boundjid.bare
            for f in self.config['vcard']:
                vcard[f] = self.config['vcard'][f]
                if f.upper() == 'NICKNAME':
                    self.nick = self.config['vcard'][f]
            self['xep_0054'].publish_vcard(vcard)
        if self.config.get('avatar', None):
            avatar_data = None
            try:
                with open(self.config['avatar'], 'rb') as avatar_file:
                    avatar_data = avatar_file.read()
            except IOError:
                logging.debug('Could not load avatar')
            if avatar_data:
                ext = os.path.splitext(self.config['avatar'])[1][1:]
                mtype = 'image/' + ext
                avatar_id = self['xep_0084'].generate_id(avatar_data)
                info = {
                    'id': avatar_id,
                    'type': mtype,
                    'bytes': len(avatar_data)
                }
                self['xep_0084'].publish_avatar(avatar_data)
                self['xep_0084'].publish_avatar_metadata(items=[info])
                self['xep_0153'].set_avatar(avatar=avatar_data, mtype=mtype)

        for room in self.config.get('rooms', []):
            self.plugin['xep_0045'].joinMUC(room,
                                            self.nick,
                                            wait=True)
            msg = self.joined_room(room)
            if msg:
                self.send_message(mto=room, mbody=msg, mtype='groupchat')

        return None

    def joined_room(self, room):
        pass

    def groupchat_subject(self, data):
        pass

    def get_match(self, regex, mode, text):
        if mode == "findall":
            return regex.findall(text)
        m = None
        if mode == "match":
            m = regex.match(text)
        elif mode == "search":
            m = regex.search(text)
        if m:
            return m.groups()
        return None

    def get_cmd(self, msg, user, text):
        delay = self.is_delay(msg)
        cmd = text.split(' ', 1)[0].lower()
        for c in self.commands:
            if delay and not c._command_delay:
                continue
            if c._command_fromuser and user not in c._command_fromuser:
                continue
            if c._command_regex:
                arg = self.get_match(
                    c._command_regex, c._command_rg_mode, text)
                if arg is not None and len(arg) > 0:
                    return c, arg
            elif cmd in c._command_names:
                return c, text.split(' ')[1:]
        return None, None

    def read_message(self, msg):
        if msg['type'] not in self.config['lisent'] or not msg['body'] or not msg['from']:
            return
        if msg['type'] == 'groupchat' and msg['from'].resource.lower() == self.nick.lower():
            return

        user = msg['from'].bare
        if user == self.boundjid.bare or (self.custom_roster and user not in self.custom_roster):
            return

        text = sp.sub(" ", msg['body']).strip()
        if len(text) == 0:
            return

        cmd, args = self.get_cmd(msg, user, text)
        if not cmd:
            self.log.debug("Unknown command from %s: %s" % (user, text))
            return

        self.log.debug("*** Command from %s: %s" % (user, text))

        if msg['type'] == 'groupchat':
            user = msg['from'].resource

        try:
            reply = cmd(*args, user=user, text=text, msg=msg)
        except Exception as error:
            self.log.exception('An error happened while processing '
                               'the message: %s' % text)
            reply = self.command_error(
                error, *args, user=user, text=text, msg=msg)
        if reply:
            self.reply_message(msg, reply, *args, **msg)

    def command_error(self, *args, **kwargs):
        return self.MSG_ERROR_OCCURRED

    def tune_reply(self, txt):
        return txt

    def reply_message(self, msg, txt, *args, **kwargs):
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

    def is_delay(self, msg):
        return self.delay and bool(msg['delay']._get_attr('stamp'))
