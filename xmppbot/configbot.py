import logging
from os.path import expanduser, isfile
import yaml

from .common import to_tuple

logger = logging.getLogger(__name__)


class Avatar:
    @classmethod
    def init(cls, file: str):
        if file is None:
            return None
        try:
            return cls(file)
        except TypeError:
            logger.warning(
                "avatar can't load because of %s is not a str" %
                file)
        except FileNotFoundError:
            logger.warning(
                "avatar can't load because of file %s does not exist" %
                file)
        except BytesWarning:
            logger.warning(
                "avatar can't load because of file %s is empty" %
                file)
        except IOError:
            logger.warning(
                "avatar can't load because of file %s cant't be read" %
                file)
        return None

    def __init__(self, file: str):
        if not isinstance(file, str):
            raise TypeError()
        if not isfile(file):
            raise FileNotFoundError()
        self.file = file
        self.content = self.__load_content()
        if len(self.content) == 0:
            raise BytesWarning()
        extension = self.file.rsplit(".", 1)[-1]
        self.mtype = 'image/' + extension

    def __load_content(self):
        with open(self.file, 'rb') as avatar_file:
            return avatar_file.read()


class ConfigBot:
    DEFAULT_PLUGINS = (
        'xep_0030',  # Service Discovery
        'xep_0004',  # Data Forms
        'xep_0060',  # PubSub
        'xep_0199',  # XMPP Ping
    )
    DEFAULT_LISENT = (
        'chat',
        'normal'
    )

    @classmethod
    def init(cls, path: str):
        if isinstance(path, dict):
            return cls(**path)
        if isinstance(path, str):
            path = expanduser(path)
            if not isfile(path):
                raise Exception(path + " doesn't exist")
            with open(path, 'r') as f:
                data = yaml.load(f, Loader=yaml.FullLoader)
                return cls(**data)
        raise Exception("Config must be a str or dict")

    def __init__(
            self,
            user: str,
            password: str,
            vcard: dict = None,
            avatar: str = None,
            roster: str | list[str] = None,
            rooms: str | list[str] = None,
            plugins: str | list[str] = DEFAULT_PLUGINS,
            lisent: str | list[str] = DEFAULT_LISENT,
            to: str | list[str] = None,
            friendly: bool = False,
            use_ipv6: bool = True,
            img_to_oob: bool = False):
        self.user = user
        self.password = password
        self.friendly = friendly
        self.use_ipv6 = use_ipv6
        self.img_to_oob = img_to_oob
        self.vcard = vcard
        self.avatar = Avatar.init(avatar)
        self.roster = to_tuple(roster)
        self.rooms = to_tuple(rooms)
        self.plugins = to_tuple(plugins)
        self.lisent = to_tuple(lisent)
        self.to = to_tuple(to)
        self.__validate()
        self.__review_lisent()
        self.__review_plugins()

    def __validate(self):
        if not isinstance(self.user, str):
            raise ValueError("user must be a str")
        if not isinstance(self.password, str):
            raise ValueError("password must be a str")

    def __review_lisent(self):
        if self.rooms and 'groupchat' not in self.lisent:
            self.lisent = self.lisent + ('groupchat',)

    def __review_plugins(self):
        plugins = set(self.plugins)
        if self.vcard:
            plugins.add('xep_0054')
        if self.avatar:
            plugins.add('xep_0084')
            plugins.add('xep_0153')
        if self.rooms:
            plugins.add('xep_0045')  # Multi-User Chat
        if self.img_to_oob:
            plugins.add('xep_0066')  # OOB
        self.plugins = tuple(sorted(set(plugins)))
