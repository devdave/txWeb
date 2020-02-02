"""
    Should be self-explanatory.   These are used to bubble up various server conditions: errors, missing, I am a teapot
    , and 3xx redirect directives for the application to handle.

    `HTTPCode` is the base class for all over codes
    refer to https://en.wikipedia.org/wiki/List_of_HTTP_status_codes
"""
import typing as T

class HTTPCode(RuntimeError):
    """
    Arguments:
        code: a valid numeric HTTP code
        message: the message to be displayed to the remote client
        exc: optionally attach the exception associated with the HTTPCode.  Useful for debugging various 500
        errors
    """
    def __init__(self, code:int, message:str, exc:T.Optional[Exception]=None):
        self.code = code
        self.message = message
        self.exc = exc

class HTTP3xx(HTTPCode):
    """
    Arguments:
        redirect: either an absolute or relative URL to tell the client to redirect too
    """
    def __init__(self, code, redirect, message="3xx Choices"):
        self.redirect = redirect
        super().__init__(code, message=message)

class HTTP302(HTTP3xx):
    def __init__(self, redirect):
        super().__init__(302, redirect, "FOUND")

class HTTP303(HTTP3xx):
    def __init__(self, redirect):
        super(HTTP303, self).__init__(303, redirect, message="See Other")


class HTTP4xx(HTTPCode):
    pass

class HTTP404(HTTP4xx):
    def __init__(self, exc=None):
        super().__init__(404, "Resource not found", exc=exc)

class HTTP405(HTTP4xx):
    def __init__(self, exc=None):
        super().__init__(405, "Method not allowed", exc=exc)


class HTTP5xx(HTTPCode):
    pass

class HTTP500(HTTP5xx):
    def __init__(self, message="Internal Server Error"):
        super().__init__(message)


class UnrenderableException(HTTP5xx):
    def __init__(self, message):
        super().__init__(500, message)