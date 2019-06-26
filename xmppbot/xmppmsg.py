import time
from os.path import expanduser

import sleekxmpp
from bs4 import BeautifulSoup, Tag

from .common import get_config, to_xep0393


class SendMsgBot(sleekxmpp.ClientXMPP):
    def __init__(self, config):
        self.config = get_config(config)
        sleekxmpp.ClientXMPP.__init__(
            self, self.config["user"], self.config["pass"])
        self.messages = []
        self.add_event_handler("session_start", self.start)

    def start(self, event):
        self.send_presence()
        self.get_roster()
        while self.messages:
            to, msg = self.messages.pop(0)
            self.send_message(mto=to,
                              mbody=msg,
                              mtype='chat')
            time.sleep(0.1)
        self.disconnect(wait=True)

    def run(self):
        if self.messages and self.connect():
            self.process(block=True)


class XmppMsg:
    def __init__(self, config=expanduser("~/.xmpp.yml"), to=None):
        self._config = None
        self._to = None
        self.config = config
        if to is not None:
            self.to = to

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, config):
        self._config = get_config(config)
        self.bot = SendMsgBot(self._config)
        self.to = self._config.get("to", self.to)

    @property
    def to(self):
        return self._to

    @to.setter
    def to(self, to):
        if to is None:
            self._to = None
        elif isinstance(to, str):
            self._to = to.strip().split()
        elif isinstance(to, (set, list, tuple)):
            self._to = to
        else:
            raise Exception("to must be a str, set, list or tuple")

    @property
    def msg(self):
        return self.bot.messages

    @msg.setter
    def msg(self, value):
        if value is None:
            self.bot.messages = []
            return
        if isinstance(value, (Tag, BeautifulSoup, str)):
            value = aux_to_xep0393(value)
        if isinstance(value, str):
            for to in self.to:
                self.bot.messages.append((to, value))
        elif isinstance(value, tuple):
            msg = aux_to_xep0393(value[-1])
            for tos in value[:-1]:
                for to in tos.strip().split():
                    self.bot.messages.append((to, msg))

    def send(self):
        self.bot.run()

    def reload(self, config=None):
        if config:
            self.config = config
        self.bot = SendMsgBot(self.config)


def aux_to_xep0393(msg):
    if isinstance(msg, (Tag, BeautifulSoup)):
        return to_xep0393(msg)
    if isinstance(msg, str):
        _msg = msg.strip()
        for tag in ("html", "p", "div", "body", "table"):
            if _msg.startswith("<"+tag+">") and _msg.endswith("</"+tag+">"):
                return to_xep0393(_msg)
    return msg
