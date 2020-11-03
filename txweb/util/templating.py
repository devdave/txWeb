import typing as T
from pathlib import Path

from jinja2 import FileSystemLoader, Environment, BytecodeCache
from jinja2.bccache import Bucket




class MyCache(BytecodeCache):

    def __init__(self, directory:T.Union[str, Path]):
        self.directory = directory

    def load_bytecode(self, bucket:Bucket):
        filename = self.directory / bucket.key
        if filename.exists():
            with filename.open("rb") as my_file:
                bucket.load_bytecode(my_file)

    def dump_bytecode(self, bucket:Bucket):
        filename = self.directory / bucket.key
        with filename.open("wb") as my_file:
            bucket.write_bytecode(my_file)

import json

JINJA2_ENV = None

def initialize_jinja2(template_dir:T.Union[Path, str], cache_dir=None):
    global JINJA2_ENV

    env_kwargs = {}

    if cache_dir is not None:
        env_kwargs['bytecode_cache'] = MyCache(cache_dir)

    env_kwargs['loader'] = FileSystemLoader(template_dir)

    JINJA2_ENV = Environment(**env_kwargs)



def render(template_pathname, **template_args):
    return JINJA2_ENV.get_template(template_pathname).render(**template_args)




