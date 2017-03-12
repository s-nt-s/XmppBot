#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import re
import yaml
import os
import logging
import subprocess
import sleekxmpp
import inspect
import yaml

sp = re.compile(r"\s+", re.MULTILINE | re.UNICODE)

if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf8')
else:
    raw_input = input


def botcmd(*args, **kwargs):
    """Decorator for bot command functions"""

    def decorate(func, name=None, names=None, delay=False, fromuser=None, regex=None, rg_mode="match"):
        setattr(func, '_command', True)
        setattr(func, '_command_names', names or [name or func.__name__])
        setattr(func, '_command_delay', delay)
        setattr(func, '_command_fromuser', fromuser)
        setattr(func, '_command_regex', regex)
        setattr(func, '_command_rg_mode', rg_mode)
        return func

    if len(args):
        return decorate(args[0], **kwargs)
    else:
        return lambda func: decorate(func, **kwargs)


class XmppBot(sleekxmpp.ClientXMPP):
    MSG_ERROR_OCCURRED = "ERROR!!"

    def __init__(self, config_path):
        sefl.delay = False
        self.commands = []
        for name, value in inspect.getmembers(self, inspect.ismethod):
            if getattr(value, '_command', False):
                names = getattr(value, '_command_names')
                self.log.info('Registered command: %s' % " ".join(names))
                self.commands.append(value)
                sefl.delay = sefl.delay or getattr(
                    value, '_command_delay', False)

        with file(config_path, 'r') as f:
            self.config = yaml.load(f)

        sleekxmpp.ClientXMPP.__init__(
            self, self.config['user'], self.config['pass'])
        self.register_plugin('xep_0030')  # Service Discovery
        self.register_plugin('xep_0004')  # Data Forms
        self.register_plugin('xep_0060')  # PubSub
        self.register_plugin('xep_0199')  # XMPP Ping
        if sefl.delay:
            self.register_plugin('xep_0203')  # XMPP Delayed messages
        if self.config.get('vcard', None):
            self.register_plugin('xep_0054')
        if self.config.get('avatar', None):
            if os.path.isfile(self.config['avatar']):
                self.register_plugin('xep_0084')
                self.register_plugin('xep_0153')
            else:
                del self.config['avatar']

        self.add_event_handler("session_start", self.start)
        self.add_event_handler("message", self.read_message)

        logging.basicConfig(level=self.config.get(
            'LOG', logging.INFO), format='%(levelname)-8s %(message)s')
        self.log = logging.getLogger()

        self.custom_roster = self.config.get('roster')

    def start(self, event):
        self.send_presence()
        self.get_roster()
        if self.config.get('vcard', None):
            vcard = self['xep_0054'].stanza.VCardTemp()
            vcard['JABBERID'] = self.boundjid.bare
            for f in self.config['vcard']:
                vcard[f] = self.config['vcard'][f]
            self['xep_0054'].publish_vcard(vcard)
        if self.config.get('avatar', None):
            avatar_data = None
            try:
                with open(self.config['avatar'], 'rb') as avatar_file:
                    avatar_data = avatar_file.read()
            except IOError:
                logging.debug('Could not load avatar')
            if avatar_data:
                mtype = 'image/' + os.path.splitext(self.config['avatar'])[1]
                avatar_id = self['xep_0084'].generate_id(avatar_data)
                info = {
                    'id': avatar_id,
                    'type': mtype,
                    'bytes': len(avatar_data)
                }
                self['xep_0084'].publish_avatar(avatar_data)
                self['xep_0084'].publish_avatar_metadata(items=[info])
                self['xep_0153'].set_avatar(
                    avatar=avatar_data, mtype=mtype)

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

    def get_cmd(self, msg):
        text = sp.sub(" ", msg['body']).strip()
        if not text:
            return None, None
        user = msg['from'].bare
        if self.custom_roster and user not in self.custom_roster:
            return None, None
        delay = sefl.is_delay(msg)
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
        if msg['type'] in ('chat', 'normal') and msg['body'] and msg['from']:
            user = msg['from'].bare
            text = sp.sub(" ", msg['body']).strip()
            if user != self.boundjid.bare and len(txt) > 0:
                cmd, args = self.get_cmd(msg)
                if not cmd:
                    self.log.debug("Unknown command: %s" % text)
                    return

                self.log.debug("*** cmd = %s" % cmd)
                try:
                    reply = cmd(user, text, args)
                except Exception, e:
                    self.log.exception('An error happened while processing '
                                       'the message: %s' % text)
                    reply = self.MSG_ERROR_OCCURRED
                if reply:
                    msg.reply(reply).send()

    def format_message(self, txt):
        return None

    def send_message(self, msg, txt):
        msgreply, formated = msg.reply(txt)
        if not formated:
            formated = self.format_message(txt)
        if formated:
            msgreply["html"]["body"] = formated
        msgreply.send()

    def is_delay(sefl, msg):
        return self.is_delay and bool(msg['delay']._get_attr('stamp'))

    def shell(self, cmd):
        p = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        out, err = p.communicate()
        return out.strip()

    def run(self):
        if self.connect():
            self.log.info("Bot started.")
            self.process(block=True)
        else:
            self.log.info("Unable to connect.")
