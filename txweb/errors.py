
class HTTPCode(RuntimeError):
    pass

class HTTP3xx(HTTPCode):
    def __init__(self, code, redirect):
        self.code = code
        self.redirect = redirect

class HTTP303(HTTP3xx):
    def __init__(self, redirect):
        self.code = 303
        self.redirect = redirect


class HTTP4xx(HTTPCode):
    def __init__(self, message):
        self.message = message

class HTTP404(HTTP4xx):
    def __init__(self):
        self.message = "Resource not found"


class HTTP5xx(HTTPCode):
    def __init__(self, message):
        self.message = message


class UnrenderableException(HTTP5xx):
    def __init__(self, message):
        self.message = message