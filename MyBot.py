#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import re
import yaml
import os
import logging
import subprocess
import re
import ipgetter
from urlparse import urlparse

from xmppbot import botcmd, Bot

if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf8')
else:
    raw_input = input


class MyBot(Bot):

    def is_torrent(self, url):
        parse = urlparse(url)
        if parse.scheme == "magnet":
            return True
        if len(parse.path) > 8 and parse.path[-8:] == ".torrent":
            return True
        if parse.netloc == "cuelgame.net":
            return True
        return False

    @botcmd(rg_mode="findall", delay=True, regex=re.compile(r'(?:https?://|magnet:\?xt=urn:btih:)(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'))
    def urls(self, user, txt, urls):
        out = []
        for url in urls:
            if is_torrent(url):
                # transmission or something like that
                out.append(self.shell("trm \"" + url + "\""))
            else:
                # read it later, bookmark or something like that
                out.append(self.shell("ril \"" + url + "\""))
        return "\n".join(out)

    @botcmd(delay=True)
    def ip(self, user, cmd, args):
        return ipgetter.myip()

    @botcmd(names=["whoami", "last"])
    def command(self, user, cmd, args):
        return self.shell(cmd)

    @botcmd(regex=re.compile(r'^(start|stop|status)\s+(tor|sshd|shellinabox|sslh)$'), rg_mode="match")
    def service(self, user, ser, args):
        return self.shell("service " + args[1] + " " + args[0])

if __name__ == '__main__':
    path = os.path.dirname(os.path.realpath(__file__))
    os.chdir(path)
    xmpp = BusBot("config.yml")
    xmpp.run()
