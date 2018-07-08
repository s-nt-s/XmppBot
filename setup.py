from distutils.core import setup
import os

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

setup(
  name = 'xmppbot',
  packages = ['xmppbot'],
  version = '0.2',
  description = 'A framework for writing Jabber/XMPP bots',
  author = 's-nt-s',
  author_email = '',
  url = 'https://github.com/s-nt-s/XmppBot',
  keywords = ['xmpp', 'bot'],
  license = 'GPLv3',
  classifiers = [],
)
