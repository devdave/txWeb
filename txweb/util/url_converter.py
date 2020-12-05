"""
    URL converter for adding twisted.web.static.File resources into the routing map.

"""
import typing as T

from werkzeug.routing import BaseConverter


class DirectoryPath(BaseConverter):  # pragma: no cover
    """
        Rule("/whatever/<directory:foo>") is a black hole rule in that
        whatever starts with /whatever will end up being caught by this rule.
    """
    regex = r"(.*)"  # Got to catch them all

    def to_python(self, value) -> T.List[str]:
        """
            Convert the url segment to a list object

        :param value:
        :return:
        """
        return value.split("/")

    def to_url(self, value: T.List[str]) -> str:
        """
        Join a list of strs into a directory path string

        :param value:
        :return:
        """
        if isinstance(value, str):
            value = [value]
        return "/".join(value)
