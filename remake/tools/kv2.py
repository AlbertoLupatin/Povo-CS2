"""Minimal reader/writer for Valve DMX keyvalues2 text (the text form of .vmap).

An element is an `Element(cls, attrs)` with `attrs` an ordered list of
`[name, type, value]`. Values:
  - scalar types: the raw string
  - inline element (type is the element class): an Element
  - "element": a uuid string reference
  - "*_array": a list; element_array items are Element or ('ref', uuid)
"""

import re

TOKEN = re.compile(r'"((?:[^"\\]|\\.)*)"|([{}\[\],])|<!--.*?-->', re.S)


class Element:
    __slots__ = ('cls', 'attrs')

    def __init__(self, cls, attrs=None):
        self.cls = cls
        self.attrs = attrs if attrs is not None else []

    def get(self, name, default=None):
        for n, _t, v in self.attrs:
            if n == name:
                return v
        return default

    def set(self, name, value, type_='string'):
        for a in self.attrs:
            if a[0] == name:
                a[2] = value
                return
        self.attrs.append([name, type_, value])

    def __repr__(self):
        return f'<{self.cls} {self.get("id")}>'


def _tokens(text):
    for m in TOKEN.finditer(text):
        if m.group(1) is not None:
            yield ('s', m.group(1))
        elif m.group(2):
            yield ('p', m.group(2))


def parse(text):
    """Return (header line, list of top-level Elements).

    The first non-prefix element is the map root; later top-level elements
    are targets of ("ref", uuid) items and must be written back.
    """
    header = text.split('\n', 1)[0]
    toks = list(_tokens(text.split('\n', 1)[1]))
    pos = 0

    def element(cls):
        nonlocal pos
        assert toks[pos] == ('p', '{'), toks[pos]
        pos += 1
        el = Element(cls)
        while toks[pos] != ('p', '}'):
            name = toks[pos][1]
            type_ = toks[pos + 1][1]
            pos += 2
            if type_.endswith('_array'):
                assert toks[pos] == ('p', '['), (name, toks[pos])
                pos += 1
                items = []
                while toks[pos] != ('p', ']'):
                    if toks[pos] == ('p', ','):
                        pos += 1
                        continue
                    if type_ == 'element_array':
                        if toks[pos][1] == 'element' and toks[pos + 1][0] == 's':
                            items.append(('ref', toks[pos + 1][1]))
                            pos += 2
                        else:
                            c = toks[pos][1]
                            pos += 1
                            items.append(element(c))
                    else:
                        items.append(toks[pos][1])
                        pos += 1
                pos += 1
                el.attrs.append([name, type_, items])
            elif toks[pos] == ('p', '{'):
                el.attrs.append([name, type_, element(type_)])
            else:
                el.attrs.append([name, type_, toks[pos][1]])
                pos += 1
        pos += 1
        return el

    roots = []
    while pos < len(toks):
        cls = toks[pos][1]
        pos += 1
        roots.append(element(cls))
    return header, roots


def root_of(roots):
    return next(r for r in roots if r.cls != '$prefix_element$')


def _q(s):
    return '"' + s + '"'


def emit(header, roots):
    out = [header]

    def element_body(el, depth, trailer=''):
        ind = '\t' * depth
        out.append(ind + '{')
        for name, type_, value in el.attrs:
            pre = ind + '\t' + _q(name) + ' ' + _q(type_)
            if isinstance(value, Element):
                out.append(pre)
                element_body(value, depth + 1)
                out.append('')
            elif type_.endswith('_array'):
                out.append(pre + ' ')
                out.append(ind + '\t[')
                for i, item in enumerate(value):
                    comma = ',' if i < len(value) - 1 else ''
                    if type_ == 'element_array':
                        if isinstance(item, tuple):
                            out.append(ind + '\t\t"element" ' + _q(item[1]) + comma)
                        else:
                            out.append(ind + '\t\t' + _q(item.cls))
                            element_body(item, depth + 2, comma)
                    else:
                        out.append(ind + '\t\t' + _q(item) + comma)
                out.append(ind + '\t]')
            else:
                out.append(pre + ' ' + _q(value))
        out.append(ind + '}' + trailer)

    for el in roots:
        out.append(_q(el.cls))
        element_body(el, 0)
    return '\n'.join(out) + '\n'


def walk(el):
    """Yield every Element below (and including) el."""
    yield el
    for _n, _t, v in el.attrs:
        if isinstance(v, Element):
            yield from walk(v)
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, Element):
                    yield from walk(item)
