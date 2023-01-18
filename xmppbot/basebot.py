import logging
import time

import slixmpp

from .common import get_config


class ConnectionLost(Exception):
    pass


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
            self.process()
            if not loop:
                return
            time.sleep(5)

    def connection_lost(self, *args, **kvargs):
        super().connection_lost(*args, **kvargs)
        self.disconnect()
