from xmppbot.xmppmsg import XmppMsg
import sys

if len(sys.argv) < 2:
    sys.exit("Need xmpp address as argument")

xsend = XmppMsg()

xsend.to = tuple(sys.argv[1:])
xsend.msg = "hello"
xsend.send()
