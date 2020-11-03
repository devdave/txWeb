#from distutils.core import setup
from setuptools import setup, find_packages
META_DATA = dict(
    , packages        = find_packages(include=["txweb", "txweb.*"])
    , package_data    = {
        'txweb': ['LICENSE.txt']
        }
    , license         = "MIT License"
    , keywords = "twisted web alternative routing"
    , description = "An alternative routing system for use with twisted.web"
    , install_requires = ["decorator", "twisted", "werkzeug"]
    , setup_requires=["pytest-runner"]
    , tests_require = ["pytest", "pytest-catchlog"]
    , extras_require = {
        "development": ["pytest", "jinja2", "pytest-catchlog", "pytest-cov", "coverage"]
    }
)

if __name__ == '__main__':
    setup(**META_DATA)
