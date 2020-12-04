
import json
import typing as T
from pathlib import Path
try:  # pragma: no cover
    import jinja2
except ImportError:  # pragma: no cover
    raise EnvironmentError("Jinja2 is not install: pip install jinja2 to use the templating utility")


from jinja2 import FileSystemLoader, Environment, BytecodeCache
from jinja2.bccache import Bucket

"""
    Utility to provide Jinja2 support for txweb enabled applications
    
    TODO: look into jinja2 returning bytes by default to cut down on post-processing
"""

# pragma: no cover
JINJA2_ENV = None  # type: Environment


class MyCache(BytecodeCache):  # pragma: no cover
    """
        To help allievate some of the hanging/processing time for rendering templates, this
         caches compiled byte cord versions of previously used templates.

         https://jinja.palletsprojects.com/en/2.11.x/api/#bytecode-cache
    """

    def __init__(self, directory: T.Union[str, Path]):
        self.directory = directory

    def load_bytecode(self, bucket: Bucket):
        filename = self.directory / bucket.key
        if filename.exists():
            with filename.open("rb") as my_file:
                bucket.load_bytecode(my_file)

    def dump_bytecode(self, bucket: Bucket):
        filename = self.directory / bucket.key
        with filename.open("wb") as my_file:
            bucket.write_bytecode(my_file)


def initialize_jinja2(template_dir: T.Union[Path, str, T.List[T.Union[Path, str]]], cache_dir: T.Optional[str, Path] = None):  # pragma: no cover
    """

    :param template_dir:  Can be either a string, Path object, or a list of string/path objects pointing to template directories
    :param cache_dir: optional absolute path to a cache dir intended for storing compiled templates
    :return:
    """
    global JINJA2_ENV

    env_kwargs = {}

    if cache_dir is not None:
        env_kwargs['bytecode_cache'] = MyCache(cache_dir)

    env_kwargs['loader'] = FileSystemLoader(template_dir)

    JINJA2_ENV = Environment(**env_kwargs)


def render(template_pathname, **template_args): # pragma: no cover
    if JINJA2_ENV is None:
        raise EnvironmentError("Jinja2 environment not initialized, call initialize_jinja2 first")

    return JINJA2_ENV.get_template(template_pathname).render(**template_args)




