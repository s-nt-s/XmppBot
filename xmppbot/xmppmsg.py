import time
from os.path import expanduser

from .basebot import BaseBot
from .timeout import timeout


class SendMsgBot(BaseBot):
    def __init__(self, config_path):
        super().__init__(config_path)
        if self.config.rooms:
            self.register_plugin('xep_0045')  # Multi-User Chat
        self.messages = []
        self.add_event_handler("session_start", self.start)

    async def start(self, event):
        await self.get_roster()
        self.send_presence()
        rooms = set(
            self.config.rooms).intersection(
            tm[0] for tm in self.messages)

        for room in rooms:
            await self.xep_0045.join_muc(room, self.config.user.split("@")[0])
            time.sleep(0.1)
        while self.messages:
            to, msg = self.messages.pop(0)
            mtype = 'chat'
            if to in rooms:
                mtype = 'groupchat'
            self.send_message(mto=to,
                              mbody=msg,
                              mtype=mtype)
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
        self.to = self.bot.config.to or self.to

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
        if isinstance(value, str):
            for to in self.to:
                self.bot.messages.append((to, value))

    def send(self):
        self.bot.run()

    def reload(self, config=None):
        self.bot = SendMsgBot(config or self.bot.config)
