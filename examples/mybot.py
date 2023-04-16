#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import subprocess
from urllib.parse import urlparse
import logging
import sys

from xmppbot import XmppBot, CmdBot, CmdFindAll, CmdMatch


class MyBot(XmppBot):

    def is_torrent(self, url):
        parse = urlparse(url)
        if parse.scheme == "magnet":
            return True
        if len(parse.path) > 8 and parse.path[-8:] == ".torrent":
            return True
        if parse.netloc == "cuelgame.net":
            return True
        return False

    def shell(self, cmd):
        output = subprocess.check_output(cmd.split())
        output = output.decode(sys.stdout.encoding)
        return output.strip()

    @CmdFindAll(
        r'(?:https?://|magnet:\?xt=urn:btih:)(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
        delay=True)
    def urls(self, *args, user=None, text=None, msg=None):
        out = []
        for url in args:
            if self.is_torrent(url):
                # transmission or something like that
                out.append(self.shell("trm \"" + url + "\""))
            else:
                # read it later, bookmark or something like that
                out.append(self.shell("ril \"" + url + "\""))
        return "\n".join(out)

    @CmdBot("whoami", "last")
    def command(self, cmd, user=None, text=None, msg=None):
        return self.shell(cmd)

    @CmdMatch(r'^(start|stop|status)\s+(tor|sshd|shellinabox|sslh)$')
    def service(self, command, service):
        return self.shell("service " + service + " " + command)

    @CmdBot()
    def ping(self, *args, **kvargs):
        return "pong"


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    path = os.path.realpath(__file__)
    path = os.path.dirname(path)
    os.chdir(path)
    xmpp = MyBot("rec/mybot.yml")
    xmpp.run()
