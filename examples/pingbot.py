#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import logging
from xmppbot import XmppBot, CmdSearch, CmdBot, CmdFindAll, CmdMatch


class PingBot(XmppBot):
    """Example bot"""

    @CmdBot()
    def ping(self, *args, **kvargs):
        return "ping args={} kvargs={}".format(args, kvargs)

    @CmdBot(name="pingX pingY")
    def ping1(self, *args, **kvargs):
        return "ping1 args={} kvargs={}".format(args, kvargs)

    @CmdMatch(r"(match)(?P<ping>ping)")
    def ping2(self, *args, **kvargs):
        return "ping2 args={} kvargs={}".format(args, kvargs)

    @CmdSearch(r"(search)(?P<ping>ping)")
    def ping3(self, *args, **kvargs):
        return "ping3 args={} kvargs={}".format(args, kvargs)

    @CmdFindAll(r"findallping.?", flags=re.IGNORECASE)
    def ping4(self, *args, **kvargs):
        return "ping4 args={} kvargs={}".format(args, kvargs)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    path = os.path.realpath(__file__)
    path = os.path.dirname(path)
    os.chdir(path)
    xmpp = PingBot("rec/ping.yml")
    xmpp.run()
