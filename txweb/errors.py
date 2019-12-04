
class HTTPCode(RuntimeError):
    def __init__(self, code, message):
        self.code = code
        self.message = message

class HTTP3xx(HTTPCode):
    def __init__(self, code, redirect):
        self.code = code
        self.redirect = redirect

class HTTP303(HTTP3xx):
    def __init__(self, redirect):
        super(HTTP303, self).__init__(303, redirect)


class HTTP4xx(HTTPCode):
    pass

class HTTP404(HTTP4xx):
    def __init__(self):
        super().__init__(404, "Resource not found")

class HTTP405(HTTP4xx):
    def __init__(self):
        super().__init__(405, "Method not allowed")


class HTTP5xx(HTTPCode):
    pass



class UnrenderableException(HTTP5xx):
    def __init__(self, message):
        super().__init__(500, message)
