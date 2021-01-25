The XmppBot framework is powered by (Slixmpp)[https://slixmpp.readthedocs.io/]
and allows you to easily write bots that use the XMPP protocol.
You can create commands by decorating functions in your subclass
or customize the bot’s operation completely. MUCs are also supported.

You can see some examples in `examples` folder.

You can install and unsintall with:

```
# install
pip3 install xmppbot
# uninstall
pip3 uninstall xmppbot
```

or

```
# install
python3 setup.py install --record files.txt
# uninstall
xargs rm -rf < files.txt
```
