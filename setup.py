#from distutils.core import setup
from setuptools import setup
META_DATA = dict(
    name            = "txweb",
    version         = '0.7.2013.11.16',
    author          = "David W.",
    author_email    = "txwebpypi@ominian.net",
    url             = "https://github.com/devdave/txWeb",
    packages        = ['txweb',"txweb.sugar","txweb.util"],
    package_data    = {
        'txweb': ['LICENSE.txt',
            'tests/test_data/a.txt',
            'tests/test_data/c.txt',
            'tests/test_data/subdir/b.txt'
            ]
        },
    license         = "MIT License",
    keywords = "twisted web alternative routing",
    description = "An alternative routing system for use with twisted.web",
    requires = ["decorator", "twisted"]
)

if __name__ == '__main__':
    setup(**META_DATA)