import logging
import time

import slixmpp
from functools import cached_property
from slixmpp.plugins import xep_0203
from slixmpp.plugins.xep_0054.vcard_temp import XEP_0054
from slixmpp.plugins.xep_0203.delay import XEP_0203
from slixmpp.plugins.xep_0084.avatar import XEP_0084
from slixmpp.plugins.xep_0153.vcard_avatar import XEP_0153
from slixmpp.plugins.xep_0045.muc import XEP_0045
import re


from .configbot import ConfigBot

logger = logging.getLogger(__name__)
re_sp = re.compile(r"\s+")


class Message(slixmpp.stanza.Message):

    @classmethod
    def init(cls, msg: slixmpp.stanza.Message):
        msg.__class__ = cls
        new_msg: cls = msg
        if not isinstance(new_msg, cls):
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


class BaseBot(slixmpp.ClientXMPP):
    def __init__(self, config_path):
        self.config = ConfigBot.init(config_path)
        super().__init__(self.config.user, self.config.password)
        self.use_ipv6 = self.config.use_ipv6

    def run(self, loop=True):
        while True:
            self.connect()
            logger.info("Bot started.")
            self.loop.run_until_complete(self.disconnected)
            if not loop:
                return
            time.sleep(5)

    def connection_lost(self, *args, **kvargs):
        super().connection_lost(*args, **kvargs)
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
    def xep_0045(self) -> XEP_0045:
        return self['xep_0045']
