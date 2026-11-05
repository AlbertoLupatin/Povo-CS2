"""Locate VMAP delimiters by scanning tokens instead of every character in Python."""
import re

_QUOTED = r'"(?:[^"\\]|\\.)*"'
_BRACES = re.compile(_QUOTED + r'|([{}])|(")', re.DOTALL)
_BRACKETS = re.compile(_QUOTED + r'|([\[\]])|(")', re.DOTALL)


def _matching(text, opening, left, right, tokens, message, error_type):
    if opening < 0 or opening >= len(text) or text[opening] != left:
        raise error_type(message)
    depth = 0
    for match in tokens.finditer(text, opening):
        delimiter = match[1]
        if delimiter == left:
            depth += 1
        elif delimiter == right:
            depth -= 1
            if depth == 0:
                return match.start()
        elif match[2]:
            raise error_type(message)  # The fallback quote starts an unterminated string.
    raise error_type(message)


def matching_brace(text, opening, *, error_type=ValueError):
    return _matching(text, opening, '{', '}', _BRACES, 'Unbalanced entity block in VMAP text', error_type)


def matching_bracket(text, opening, *, error_type=ValueError):
    return _matching(text, opening, '[', ']', _BRACKETS, 'Unbalanced element array in VMAP text', error_type)
