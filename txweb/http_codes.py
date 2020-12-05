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
        super().__init__(message)

        self.code = code
        self.message = message
        self.exc = exc


class HTTP3xx(HTTPCode):
    """
    Arguments:
        redirect: either an absolute or relative URL to tell the client to redirect too
    """
    def __init__(self, code: int, redirect: T.Union[str, bytes], message: str = "3xx Choices"):
        self.redirect = redirect
        super().__init__(code, message=message)


class HTTP301(HTTP3xx):
    CODE = 301

    def __init__(self, redirect: T.Union[str, bytes]):
        super().__init__(self.CODE, redirect, "Moved Permanently")


class HTTP302(HTTP3xx):
    CODE = 302

    def __init__(self, redirect: T.Union[str, bytes]):
        super().__init__(self.CODE, redirect, "FOUND")


class HTTP303(HTTP3xx):
    CODE = 303

    def __init__(self, redirect: T.Union[str, bytes]):
        super().__init__(self.CODE, redirect, message="See Other")


class HTTP304(HTTP3xx):
    CODE = 304

    def __init__(self, redirect: T.Union[str, bytes]):
        super().__init__(self.CODE, redirect, "Not Modified")


class HTTP307(HTTP3xx):
    CODE = 307

    def __init__(self, redirect: T.Union[str, bytes]):
        super().__init__(self.CODE, redirect, "Temporary Redirect")


class HTTP308(HTTP3xx):
    CODE = 308

    def __init__(self, redirect: T.Union[str, bytes]):
        super().__init__(self.CODE, redirect, "Permanent Redirect")


class HTTP4xx(HTTPCode):
    pass


class HTTP400(HTTP4xx):
    CODE = 400

    def __init__(self):
        super().__init__(self.CODE, "Bad Request")


class HTTP401(HTTP4xx):
    CODE = 401

    def __init__(self):
        super().__init__(self.CODE, "Unauthorized")


class HTTP403(HTTP4xx):
    CODE = 403

    def __init__(self):
        super().__init__(self.CODE, "Forbidden")


class HTTP404(HTTP4xx):
    CODE = 404

    def __init__(self, exc=None):
        super().__init__(self.CODE, "Resource not found", exc=exc)


class HTTP410(HTTP4xx):
    CODE = 410

    def __init__(self):
        super().__init__(self.CODE, "Gone")


class HTTP405(HTTP4xx):
    CODE = 405

    def __init__(self, exc=None):
        super().__init__(self.CODE, "Method not allowed", exc=exc)


class HTTP5xx(HTTPCode):
    pass


class HTTP500(HTTP5xx):
    CODE = 500

    def __init__(self, message="Internal Server Error"):
        super().__init__(self.CODE, message)


class Unrenderable(HTTP5xx):
    pass
