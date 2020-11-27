Quick start
===========

```python
from twisted.internet import reactor
from txweb import Application


app = Application(__name__)

@app.route("/hello")
def hello_world(request):
    return "Hello World!"

listening = app.listenTCP(PORT, interface="0.0.0.0")
reactor.start()

```