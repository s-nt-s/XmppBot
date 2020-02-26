import logging

import slixmpp
import time

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

    def run(self):
        try:
            self.connect()
            self.log.info("Bot started.")
            self.process()
        except ConnectionLost:
            time.sleep(5)
            self.run()

    def connection_lost(self, *args, **kargv):
        super().connection_lost(*args, **kargv)
        raise ConnectionLost()
