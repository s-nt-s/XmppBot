import slixmpp
import logging

from .common import get_config

class BaseBot(slixmpp.ClientXMPP):
    def __init__(self, config_path):
        self.config = get_config(config_path)
        super().__init__(self.config['user'], self.config['pass'])
        logging.basicConfig(level=self.config.get(
            'LOG', logging.INFO), format='%(levelname)-8s %(message)s')
        self.log = logging.getLogger()

    def run(self):
        self.connect()
        self.log.info("Bot started.")
        self.process()
