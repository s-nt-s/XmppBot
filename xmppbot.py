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

class Bot(sleekxmpp.ClientXMPP):
    MSG_ERROR_OCCURRED = "ERROR!!"

    def __init__(self, config_path=None, namebot="xmppbot"):
        config_path = self.get_config(config_path, namebot)
        with file(config_path, 'r') as f:
            self.config = yaml.load(f)
        if "namebot" not in self.config:
            self.config['namebot'] = namebot
        sleekxmpp.ClientXMPP.__init__(self, self.config['user'], self.config['pass'])
        self.register_plugin('xep_0030') # Service Discovery
        self.register_plugin('xep_0004') # Data Forms
        self.register_plugin('xep_0060') # PubSub
        self.register_plugin('xep_0203') # XMPP Delayed messages
        self.register_plugin('xep_0199') # XMPP Ping
        self.add_event_handler("session_start", self.start)
        self.add_event_handler("message", self.read_message)
        logging.basicConfig(level=self.config.get('LOG',logging.INFO), format='%(levelname)-8s %(message)s')
        self.log = logging.getLogger()
        self.custom_roster = self.config.get('roster')
        self.name = self.config.get('namebot')

        self.commands = []
        for name, value in inspect.getmembers(self, inspect.ismethod):
            if getattr(value, '_command', False):
                names = getattr(value, '_command_names')
                self.log.info('Registered command: %s' % " ".join(names))
                self.commands.append(value)

    def get_config(self, config_path, namebot):
        if config_path:
            return config_path
        file=namebot+".yaml"
        paths=[
            os.getcwd()+"/"+file,
            "~/"+file,
            "/etc/"+file
        ]
        for f in paths:
            if os.path.isfile(f):
                return f
        return None

    def start(self, event):
        self.send_presence()
        self.get_roster()

    def get_match(self, regex, mode, text):
        if mode == "findall":
            return regex.findall(text)
        m=None
        if mode == "match":
            m=regex.match(text)
        elif mode == "search":
            m=regex.search(text)
        if m:
            return m.groups()
        return None

    def get_cmd(self, msg):
        text = msg['body'].strip()
        if not text:
            return None, None
        user = msg['from'].bare
        if self.custom_roster and user not in self.custom_roster:
            return None, None
        delay = bool(msg['delay']._get_attr('stamp'))
        cmd = text.split(' ', 1)[0].lower()
        for c in self.commands:
            if delay and not c._command_delay:
                continue
            if c._command_fromuser and user not in c._command_fromuser:
                continue
            if c._command_regex:
                arg=self.get_match(c._command_regex, c._command_rg_mode, text)
                if arg is not None and len(arg)>0:
                    return c, arg
            elif cmd in c._command_names:
                return c, text.split(' ')[1:]
        return None, None

    def read_message(self, msg):
        if msg['type'] in ('chat', 'normal') and msg['body'] and msg['from']:
            text = msg['body'].strip()
            cmd, args = self.get_cmd(msg)
            if not cmd:
                self.log.debug("Unknown command: %s" % text)
                return

            self.log.debug("*** cmd = %s" % cmd)
            try:
                reply = cmd(text, args)
            except Exception, e:
                self.log.exception('An error happened while processing '\
                    'the message: %s' % text)
                reply = self.MSG_ERROR_OCCURRED
            if reply:
                msg.reply(reply).send()

    def write_message(msg, to=None, tp='chat'):
        if to is None:
            to=self.config.get("sendto")
        if not to or len(to)==0:
            return
        for t in to:
            self.send_message(mto=t,
                              mbody=msg,
                              mtype=tp)

    def is_delay(sefl, msg):
        return bool(msg['delay']._get_attr('stamp'))

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