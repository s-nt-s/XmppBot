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
        logging.basicConfig(level=self.config.get(
            'LOG', logging.INFO), format='%(levelname)-8s %(message)s')
        self.log = logging.getLogger()

    def run(self, loop=True):
        while True:
            self.connect()
            self.log.info("Bot started.")
            self.process()
            if not loop:
                return
            time.sleep(5)

    def connection_lost(self, *args, **kargv):
        super().connection_lost(*args, **kargv)
        self.disconnect()
