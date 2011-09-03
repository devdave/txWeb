from distutils.core import setup
setup(name="txweb"
      , version='0.01'
      , author = "David W."
      , author_email = "txwebpypi@ominian.net"
      , url = "https://github.com/devdave/txWeb"
      , packages=['txweb']
      , package_data={'txweb': ['LICENSE.txt', 'tests/test_data/a.txt', 'tests/test_data/c.txt', 'tests/test_data/subdir/b.txt'  ]}
      , license = "MIT License"
      , keywords = "twisted web alternative routing"
      , description = "An alternative routing system for use with twisted.web"
)