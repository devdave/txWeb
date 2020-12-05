"""
    Texas web (txweb).

    ```python
        app = Application(__name__)

        @app.route("/foo")
        def bar(request):
            return "Hello World!"

        app.listenTCP(7070)

        reactor.run()
    ```

    curl http://127.0.0.1/foo
    Hello World!
"""
from twisted.web.server import NOT_DONE_YET
from txweb.application import Application

App = Application
Texas = Application
__all__ = ['NOT_DONE_YET', "App", "Application"]
