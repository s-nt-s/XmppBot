import os
from distutils.core import setup

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

REPO = 'https://github.com/s-nt-s/XmppBot'
VERSION = '2021.01.25'

setup(
    name='xmppbot',
    packages=['xmppbot'],
    version=VERSION,
    description='A framework for writing Jabber/XMPP bots',
    author='s-nt-s',
    author_email='santos82h@gmail.com',
    url=REPO,
    download_url='',
    download_url = REPO+'/tarball/'+VERSION,
    keywords=['xmpp', 'bot'],
    license='GPLv3',
    classifiers=[],
)
