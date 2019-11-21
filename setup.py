#from distutils.core import setup
from setuptools import setup
META_DATA = dict(
    name            = "txweb",
    version         = '0.11.2019',
    author          = "David W.",
    author_email    = "devdave@ominian.net",
    url             = "https://github.com/devdave/txWeb",
    packages        = ['txweb',"txweb.util"],
    package_data    = {
        'txweb': ['LICENSE.txt']
        },
    license         = "MIT License",
    keywords = "twisted web alternative routing",
    description = "An alternative routing system for use with twisted.web",
    requires = ["decorator", "twisted", "werkzeug"]
)

if __name__ == '__main__':
    setup(**META_DATA)
