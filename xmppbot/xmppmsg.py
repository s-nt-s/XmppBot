import time
from os.path import expanduser

from bs4 import BeautifulSoup, Tag

from .basebot import BaseBot
from .common import to_xep0393
from .timeout import timeout


class SendMsgBot(BaseBot):
    def __init__(self, config_path):
        super().__init__(config_path)
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
        self.disconnect()

    def run(self):
        if not self.messages:
            return
        with timeout(seconds=10):
            try:
                super().run(loop=False)
            except TimeoutError:
                pass


class XmppMsg:
    def __init__(self, config=expanduser("~/.xmpp.yml"), to=None):
        self._to = None
        self.bot = None
        self.set_to(to)
        self.set_config(config)

    @property
    def config(self):
        if self.bot is None:
            return None
        return self.bot.config

    @config.setter
    def config(self, config):
        self.set_config(config)

    def set_config(self, config):
        if config is None:
            self.bot = None
            self.to = None
            return
        self.bot = SendMsgBot(config)
        self.to = self.bot.config.get("to", self.to)

    @property
    def to(self):
        return self._to

    @to.setter
    def to(self, to):
        self.set_to(to)

    def set_to(self, to):
        if to is None:
            self._to = None
        elif isinstance(to, str):
            self._to = tuple(to.strip().split())
        elif isinstance(to, (set, list, tuple)):
            self._to = tuple(to)
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
            value = msg_to_xep0393(value)
        if isinstance(value, str):
            for to in self.to:
                self.bot.messages.append((to, value))
        elif isinstance(value, tuple):
            msg = msg_to_xep0393(value[-1])
            for tos in value[:-1]:
                for to in tos.strip().split():
                    self.bot.messages.append((to, msg))

    def send(self):
        self.bot.run()

    def reload(self, config=None):
        self.bot = SendMsgBot(config or self.bot.config)


def msg_to_xep0393(msg):
    if isinstance(msg, (Tag, BeautifulSoup)):
        return to_xep0393(msg)
    if isinstance(msg, str):
        _msg = msg.strip().lower()
        for tag in ("html", "p", "div", "body", "table"):
            if _msg.startswith("<"+tag+">") and _msg.endswith("</"+tag+">"):
                return to_xep0393(msg)
    return msg
