import functools
import re

re_sp = re.compile(r"\s+")

class NotForMeException(Exception):
    pass

def botcmd(*args, **kwargs):
    """Decorator for bot command functions"""
    global creator_order

    def decorate(func, creator_order, name=None, names=None, delay=False, fromuser=None, regex=None, rg_mode="match"):
        setattr(func, '_command', True)
        setattr(func, '_command_names', names or [name or func.__name__])
        setattr(func, '_command_delay', delay)
        setattr(func, '_command_fromuser', fromuser)
        setattr(func, '_command_regex', regex)
        setattr(func, '_command_rg_mode', rg_mode)
        setattr(func, '_command_order', creator_order)
        return func

    creator_order += 1

    if len(args):
        return decorate(args[0], creator_order, **kwargs)
    else:
        return lambda func: decorate(func, creator_order, **kwargs)

class CMD:
    def __init__(self, delay:bool=False, users:list[str]=None):
        self.func = None
        self.delay = delay
        self.users = users
        self.func = None

    def isForMe(self, msg) -> bool:
        if not callable(self.func):
            raise Exception("func is not callable")
        if not(self.delay) and bool(msg['delay']._get_attr('stamp')):
            return False
        if self.users and msg['from'].bare not in self.users:
            return False
        try:
            self.extract_args(msg)
        except NotForMeException:
            return False
        return True
        
    def extract_args(self, msg):
        raise NotForMeException()
    
    def callCache(self, slf, msg):
        args, kvargs = self.extract_args(msg)
        return self.func(slf, *args, **kvargs)

    def __call__(self, func):
        functools.update_wrapper(self, func)
        global creator_order
        creator_order += 1
        setattr(func, '_command', True)
        setattr(func, '_command_order', creator_order)
        self.func = func
        return lambda *args, **kvargs: self.callCache(*args, **kvargs)

class NameCmd(CMD):
    def __init__(self, *args, alias:str|list[str]=None, **kvargs):
        super().__init__(*args, **kvargs)
        self.alias = None
        if isinstance(alias, str):
            self.alias = [alias]
        elif isinstance(alias, list):
            self.alias = alias

    @property
    def names(self):
        if self.alias is not None:
            return self.alias
        return [self.func.__name__]
    
    def extract_args(self, msg) -> bool:
        txt = re_sp.sub(" ", msg['body']).strip()
        cmd = txt.split(' ', 1)[0].lower()
        if cmd not in self.names:
            raise NotForMeException()
        return tuple(txt.split(' ')[1:]), None