#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import subprocess
import urllib.parse as urlparse
import sys

import yaml

from xmppbot import XmppBot, botcmd


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
        p = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        out, err = p.communicate()
        return out.strip()

    @botcmd(rg_mode="findall", delay=True, regex=re.compile(r'(?:https?://|magnet:\?xt=urn:btih:)(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'))
    def urls(self, *args, user=None, text=None, msg=None):
        out = []
        for url in args:
            if is_torrent(url):
                # transmission or something like that
                out.append(self.shell("trm \"" + url + "\""))
            else:
                # read it later, bookmark or something like that
                out.append(self.shell("ril \"" + url + "\""))
        return "\n".join(out)

    @botcmd(names=["whoami", "last"])
    def command(self, cmd, user=None, text=None, msg=None):
        return self.shell(cmd)

    @botcmd(regex=re.compile(r'^(start|stop|status)\s+(tor|sshd|shellinabox|sslh)$'), rg_mode="match")
    def service(self, *args, user=None, text=None, msg=None):
        return self.shell("service " + args[1] + " " + args[0])

    @botcmd
    def ping(self, *args, **kargv):
        return "pong"


if __name__ == '__main__':
    conf = sys.argv[1] if len(sys.argv)==2 else "mybot.yaml"
    path = os.path.dirname(os.path.realpath(__file__))
    os.chdir(path)
    print("Configuración:", conf)
    xmpp = MyBot(conf)
    xmpp.run()
