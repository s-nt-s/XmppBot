#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import time
from daemon import runner
import os
from optparse import OptionParser
import sys

import MyBot

class App():
    def __init__(self):
        self.name=os.path.splitext(os.path.basename(__file__))[0]
        self.stdin_path = '/dev/null'
        self.stdout_path = '/dev/tty'
        self.stderr_path = '/dev/tty'
        self.pidfile_path = '/var/run/'+self.name+'.pid'
        self.pidfile_timeout = 5
        self.bot = MyBot.MyBot()

    def getpid(self):
        if os.path.exists(self.pidfile_path):
            with open(self.pidfile_path,'r') as f:
                return int(f.read())
        return None

    def run(self):
        self.bot.run()

if __name__ == '__main__':
    app = App()

    if len(sys.argv)>1:
        arg=sys.argv[1]
        if arg=="status":
            pid=app.getpid()
            if pid:
                print "Started with pid "+str(pid)
            else:
                print "Stopped"
            sys.exit(0)
        elif arg=="send":
            sendmsg.send('Sender: ', message=" ".join(sys.argv))
            sys.exit(0)

    handler = logging.FileHandler("/var/log/"+app.bot.name+".log")
    app.bot.log.addHandler(handler)

    # Se ejecuta el demonio llamando al objeto app
    daemon_runner = runner.DaemonRunner(app)

    # Esto evita que el archivo log no se cierre durante la ejecución del demonio
    daemon_runner.daemon_context.files_preserve = [handler.stream]

    # Ejecuta el método run del objeto app
    daemon_runner.do_action()
