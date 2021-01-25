import os
from setuptools import find_packages, setup

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()
long_description = long_description.strip()

setup(
    name='slixmppbot',
    packages=find_packages(),
    version='1.0.2',
    long_description=long_description,
    long_description_content_type="text/markdown",
    description='A framework for writing Jabber/XMPP bots',
    author='s-nt-s',
    author_email='santos82h@gmail.com',
    url='https://github.com/s-nt-s/XmppBot',
    keywords=['xmpp', 'bot'],
    license='GPLv3',
    classifiers=[
        "Programming Language :: Python :: 3",
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
