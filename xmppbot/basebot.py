import logging
import time

from functools import cached_property
from slixmpp.plugins import xep_0203
from slixmpp.plugins.xep_0054.vcard_temp import XEP_0054
from slixmpp.plugins.xep_0203.delay import XEP_0203
from slixmpp.plugins.xep_0084.avatar import XEP_0084
from slixmpp.plugins.xep_0153.vcard_avatar import XEP_0153
from slixmpp.plugins.xep_0045.muc import XEP_0045
from slixmpp.plugins.xep_0085.chat_states import XEP_0085
from slixmpp.stanza import Message as sliMessage
from slixmpp import ClientXMPP
import re


from .configbot import ConfigBot

logger = logging.getLogger(__name__)
re_sp = re.compile(r"\s+")


class Message(sliMessage):

    @staticmethod
    def init(msg: sliMessage):
        msg.__class__ = Message
        new_msg: Message = msg
        if not isinstance(new_msg, Message):
            return None
        return new_msg

    @cached_property
    def sender(self) -> str:
        if self['type'] == 'groupchat':
            return self['from'].resource
        return self['from'].bare

    @cached_property
    def text(self):
        return re_sp.sub(" ", self['body']).strip()

    @cached_property
    def is_delay(self):
        return isinstance(
            self['delay'], xep_0203.Delay) and bool(
            self['delay']._get_attr('stamp'))


class BaseBot(ClientXMPP):
    def __init__(self, config_path: str):
        self.config = ConfigBot.init(config_path)
        super().__init__(self.config.user, self.config.password)
        self.use_ipv6 = self.config.use_ipv6
        self.__auth_failed = False
        self.add_event_handler('failed_auth', self._on_failed_auth)
        self.add_event_handler('auth_failed', self._on_failed_auth)

    def run(self, loop=True):
        while True:
            self.connect()
            logger.info("Bot started.")
            self.loop.run_until_complete(self.disconnected)
            if self.__auth_failed:
                logger.error('Authentication failed: stopping retries.')
                return
            if not loop:
                return
            time.sleep(20)

    def _on_failed_auth(self, *args, **kwargs):
        self.__auth_failed = True
        logger.error('Received failed authentication event')

    def connection_lost(self, *args, **kwargs):
        super().connection_lost(*args, **kwargs)
        self.disconnect()

    @property
    def xep_0203(self) -> XEP_0203:
        return self['xep_0203']

    @property
    def xep_0054(self) -> XEP_0054:
        return self['xep_0054']

    @property
    def xep_0084(self) -> XEP_0084:
        return self['xep_0084']

    @property
    def xep_0153(self) -> XEP_0153:
        return self['xep_0153']

    @property
    def xep_0085(self) -> XEP_0085:
        return self['xep_0085']

    @property
    def xep_0045(self) -> XEP_0045:
        return self['xep_0045']
