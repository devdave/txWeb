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
    This class of status code indicates the client must take additional action to complete the request.
    Many of these status codes are used in URL redirection.

    Arguments:
        redirect: either an absolute or relative URL to tell the client to redirect too
    """
    def __init__(self, code: int, redirect: T.Union[str, bytes], message: str = "3xx Choices"):
        self.redirect = redirect
        super().__init__(code, message=message)


class HTTP301(HTTP3xx):
    """
    301 Moved Permanently
    This and all future requests should be directed to the given URI
    """
    CODE = 301

    def __init__(self, redirect: T.Union[str, bytes]):
        super().__init__(self.CODE, redirect, "Moved Permanently")


class HTTP302(HTTP3xx):
    """
    302 Found (Previously "Moved temporarily")
    Tells the client to look at (browse to) another URL. 302 has been superseded by 303 and 307.
    This is an example of industry practice contradicting the standard. The HTTP/1.0 specification
     (RFC 1945) required the client to perform a temporary redirect (the original describing phrase
     was "Moved Temporarily"), but popular browsers implemented 302 with the functionality of a
     303 See Other. Therefore, HTTP/1.1 added status codes 303 and 307 to distinguish between the two behaviours.
      However, some Web applications and frameworks use the 302 status code as if it were the 303.
    """
    CODE = 302

    def __init__(self, redirect: T.Union[str, bytes]):
        super().__init__(self.CODE, redirect, "FOUND")


class HTTP303(HTTP3xx):
    """
    The response to the request can be found under another URI using the GET method.
    When received in response to a POST (or PUT/DELETE), the client should presume that
    the server has received the data and should issue a new GET request to the given URI.
    """
    CODE = 303

    def __init__(self, redirect: T.Union[str, bytes]):
        super().__init__(self.CODE, redirect, message="See Other")


class HTTP304(HTTP3xx):
    """
    304 Not Modified (RFC 7232)
    Indicates that the resource has not been modified since the version specified by the request headers
    If-Modified-Since or If-None-Match. In such case, there is no need to retransmit the resource since the client
    still has a previously-downloaded copy.
    """
    CODE = 304

    def __init__(self, redirect: T.Union[str, bytes]):
        super().__init__(self.CODE, redirect, "Not Modified")


class HTTP307(HTTP3xx):
    """
    307 Temporary Redirect (since HTTP/1.1)
    In this case, the request should be repeated with another URI; however, future requests should still use the
    original URI. In contrast to how 302 was historically implemented, the request method is not allowed to be changed
    when reissuing the original request. For example, a POST request should be repeated using another POST request.
    """
    CODE = 307

    def __init__(self, redirect: T.Union[str, bytes]):
        super().__init__(self.CODE, redirect, "Temporary Redirect")


class HTTP308(HTTP3xx):
    """
    308 Permanent Redirect (RFC 7538)
    The request and all future requests should be repeated using another URI. 307 and 308 parallel the behaviors of
    302 and 301, but do not allow the HTTP method to change. So, for example, submitting a form to a permanently
    redirected resource may continue smoothly.[
    """
    CODE = 308

    def __init__(self, redirect: T.Union[str, bytes]):
        super().__init__(self.CODE, redirect, "Permanent Redirect")


class HTTP4xx(HTTPCode):
    """
    Base Exception for 4xx HTTP codes

    This class of status code is intended for situations in which the error seems to have been caused by the client.
    """
    pass


class HTTP400(HTTP4xx):
    """
    400 Bad Request
    The server cannot or will not process the request due to an apparent client error
    (e.g., malformed request syntax, size too large, invalid request message framing, or deceptive request routing).
    """
    CODE = 400

    def __init__(self):
        super().__init__(self.CODE, "Bad Request")


class HTTP401(HTTP4xx):
    """
    Similar to 403 Forbidden, but specifically for use when authentication is required and has failed
        or has not yet been provided.
    """
    CODE = 401

    def __init__(self):
        super().__init__(self.CODE, "Unauthorized")


class HTTP403(HTTP4xx):
    """
    The request contained valid data and was understood by the server, but the server is refusing action.

    """
    CODE = 403

    def __init__(self):
        super().__init__(self.CODE, "Forbidden")


class HTTP404(HTTP4xx):
    """
    404 Not Found

    The requested resource could not be found but may be available in the future.
    Subsequent requests by the client are permissible.
    """
    CODE = 404

    def __init__(self, exc=None):
        super().__init__(self.CODE, "Resource not found", exc=exc)


class HTTP410(HTTP4xx):
    """
    410 Gone
    Indicates that the resource requested is no longer available and will not be available again.

    """
    CODE = 410

    def __init__(self):
        super().__init__(self.CODE, "Gone")


class HTTP405(HTTP4xx):
    """
    A request method is not supported for the requested resource;
    for example, a GET request on a form that requires data to be
     presented via POST, or a PUT request on a read-only resource.
    """
    CODE = 405

    def __init__(self, exc=None):
        super().__init__(self.CODE, "Method not allowed", exc=exc)


class HTTP5xx(HTTPCode):
    """
    The server failed to fulfill a request.[61]

    Response status codes beginning with the digit "5" indicate cases in which the server is aware that it has
    encountered an error or is otherwise incapable of performing the request.
    Except when responding to a HEAD request, the server should include an entity containing an explanation of the
     error situation, and indicate whether it is a temporary or permanent condition.
     Likewise, user agents should display any included entity to the user.
     These response codes are applicable to any request method.
    """
    pass


class HTTP500(HTTP5xx):
    """
    500 Internal Server Error
    A generic error message, given when an unexpected condition was encountered and no more specific message
    is suitable.
    """
    CODE = 500

    def __init__(self, message="Internal Server Error"):
        super().__init__(self.CODE, message)


class Unrenderable(EnvironmentError):
    """
    An class definition or view function's result cannot be rendered to the client.

    """
    pass
