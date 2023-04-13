import logging
import time

import slixmpp
from functools import cache, cached_property
from slixmpp.plugins.xep_0203.stanza import Delay
import re

from .common import get_config

re_sp = re.compile(r"\s+")

class ConnectionLost(Exception):
    pass

class Message(slixmpp.stanza.Message):

    @cached_property
    def sender(self):
        if self['type'] == 'groupchat':
            return self['from'].resource
        return self['from'].bare
    
    @cached_property
    def text(self):
        return re_sp.sub(" ", self['body']).strip()
    
    @cached_property
    def is_delay(self):
        return isinstance(self['delay'], Delay) and bool(self['delay']._get_attr('stamp'))



class BaseBot(slixmpp.ClientXMPP):
    def __init__(self, config_path):
        self.config = get_config(config_path)
        super().__init__(self.config['user'], self.config['pass'])
        self.log = logging.getLogger(__name__)
        self.log.setLevel(self.config.get('LOG', logging.INFO))

    def run(self, loop=True):
        while True:
            self.connect()
            self.log.info("Bot started.")
            self.loop.run_until_complete(self.disconnected)
            if not loop:
                return
            time.sleep(5)

    def connection_lost(self, *args, **kvargs):
        super().connection_lost(*args, **kvargs)
        self.disconnect()
