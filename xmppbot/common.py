import re


def to_tuple(s: str | list | set | tuple, *default) -> tuple[str]:
    if s is None:
        return default
    if isinstance(s, tuple):
        return s
    if isinstance(s, (list, set)):
        return tuple(s)
    if isinstance(s, str):
        arr = s.strip().split()
        return tuple(arr)
    raise TypeError(s)


def _split(s: str, *args):
    for r in args:
        m = re.search(r"^(.*)\s*"+r+r"\s*(.*)$", s, re.DOTALL)
        if m:
            left = m.group(1).rstrip()
            right = m.group(2).lstrip()
            return left, right
    return s, None


def iter_max(s: str, max_length: int):
    if not isinstance(s, str):
        return
    if max_length <= 0:
        yield s
        return
    while len(s) > max_length:
        s1 = s[:max_length]
        s2 = s[max_length:]
        if s1[-1] == "\n" and len(s2) > 0 and s2[0] == "\n":
            yield s1.strip()
            s = s2.strip()
            continue
        s1 = s1.strip()
        left, right = _split(s1, r"\n\s*\n\s*\n", r"\n\s*\n", r"\n", r"\s")
        if right is None:
            yield s1
            s = s2.strip()
        else:
            yield left
            s = (right + s2).strip()

    s = s.strip()
    if len(s) > 0:
        yield s
