#from distutils.core import setup
from setuptools import setup, find_packages
META_DATA = dict(
    name            = "txweb"
    , version         = '0.11.2020'
    , author          = "David W."
    , author_email    = "devdave@ominian.net"
    , url             = "https://github.com/devdave/txWeb"
    , packages        = find_packages(include=["txweb", "txweb.*"])
    , package_data    = {
        'txweb': ['LICENSE.txt']
        }
    , license         = "MIT License"
    , keywords = "twisted web alternative routing"
    , description = "An alternative routing system for use with twisted.web"
    , install_requires = ["decorator", "twisted", "werkzeug"]
    , tests_require = ["pytest", "pytest-catchlog"]
    , extras_require = {
        "development": ["pytest", "jinja2", "pytest-catchlog", "pytest-cov", "coverage"]
    }
)

if __name__ == '__main__':
    setup(**META_DATA)
