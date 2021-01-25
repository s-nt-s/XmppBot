import os
from setuptools import find_packages, setup
from pkg_resources import parse_requirements

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

def read(fl):
    with open(fl, "r") as f:
        txt = f.read()
        txt = txt.strip()
        return txt

def reqs(fl):
    rqs=set()
    with open(fl, "r") as f:
        for r in parse_requirements(f):
            rqs.add(r.name)
    return sorted(rqs)

setup(
    name='slixmppbot',
    packages=find_packages(),
    version='1.0.4',
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    description='A framework for writing Jabber/XMPP bots',
    author='s-nt-s',
    author_email='santos82h@gmail.com',
    url='https://github.com/s-nt-s/XmppBot',
    keywords=['xmpp', 'bot'],
    license='GPLv3',
    install_requires=reqs("requirements.txt"),
    classifiers=[
        "Programming Language :: Python :: 3",
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.5'
)
