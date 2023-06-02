def to_tuple(s, *default) -> tuple[str]:
    if s is None:
        return default
    if isinstance(s, tuple):
        return s
    if isinstance(s, (list, set)):
        return tuple(s)
    if isinstance(s, str):
        arr = s.strip().split()
        return tuple(arr)
    raise TypeError()
