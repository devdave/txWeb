import typing as T

from werkzeug.routing import BaseConverter

class DirectoryPath(BaseConverter): # pragma: no cover
    """
        Rule("/whatever/<directory:foo>") is a black hole rule in that
        whatever starts with /whatever will end up being caught by this rule.
    """
    regex = r"(.*)" #  Got to catch them all

    def __init__(self, url_map):
        super(DirectoryPath, self).__init__(url_map)

    def to_python(self, value):
        return value.split("/")

    def to_url(self, value: T.List[str]):
        if isinstance(value, str):
            value = [value]
        return "/".join(value)
