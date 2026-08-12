#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import logging
from xmppbot import XmppBot, CmdSearch, CmdBot, CmdFindAll, CmdMatch
import time


class PingBot(XmppBot):
    """Example bot"""

    @CmdBot()
    def ping(self, *args, **kwargs):
        return "ping args={} kwargs={}".format(args, kwargs)

    @CmdBot("pingSleep")
    def pingSleep(self, *args, **kwargs):
        time.sleep(int(args[0]) if args else 1)
        return "pingSleep args={} kwargs={}".format(args, kwargs)

    @CmdBot("pingX", "pingY")
    def ping1(self, *args, **kwargs):
        return "ping1 args={} kwargs={}".format(args, kwargs)

    @CmdMatch(r"(match)(?P<ping>ping)")
    def ping2(self, *args, **kwargs):
        return "ping2 args={} kwargs={}".format(args, kwargs)

    @CmdSearch(r"(search)(?P<ping>ping)")
    def ping3(self, *args, **kwargs):
        return "ping3 args={} kwargs={}".format(args, kwargs)

    @CmdFindAll(r"findallping.?", flags=re.IGNORECASE)
    def ping4(self, *args, **kwargs):
        return "ping4 args={} kwargs={}".format(args, kwargs)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    import sys

    path = os.path.realpath(__file__)
    path = os.path.dirname(path)
    os.chdir(path)
    path = "rec/ping.yml"
    if sys.argv[1:]:
        path = sys.argv[1]
    xmpp = PingBot(path)
    xmpp.run()
