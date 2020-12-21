Routing static assets
=====================

Texas can expose both individual static files and entire directory assets.


Static files and directories
----------------------------

## Exposing static files

```python
from pathlib import Path
from txweb import Texas

app = Texas(__name__)

app.route_file("/my_file", Path(__file__).parent / "path" / "too" / "my_file.txt")

```

The snippet above would make `./path/too/my_file.txt` accessible to a client browser at
the URI "/my_file" via GET.   Internally this uses `twisted.web.static.File` which does its
best to determine the correct MIME type of the file being served, BUT it defaults to `text/html`
if it cannot.   

In that scenario you can set a default content type via

`app.add_file("/my_file", "foo/bar.txt", defaultType="application/jsonp")`

## Exposing static directories

```python
from pathlib import Path
from txweb import Texas

app = Texas(__name__)

app.route_directory("/my_file", Path(__file__).parent / "path" / "too" / "my_static_dir")

```

Similar to `app.add_file` this uses `twisted.web.static.File` but if provided a directory path
it will recursively expose all subdirectories as well which should be noted.
