from __future__ import annotations
import typing as T
from twisted.web import resource
from twisted.web.server import NOT_DONE_YET

from txweb.util.basic import sanitize_render_output

if T.TYPE_CHECKING:  # pragma: no cover
    from txweb.lib.str_request import StrRequest

NotDoneYet = T.TypeVar(int)

class ViewClassResource(resource.Resource):

    isLeaf: T.ClassVar[T.Union[bool, int]] = True

    # noinspection PyMissingConstructor
    def __init__(self, kls_view, instance=None):
        self.kls_view = kls_view
        self.instance = instance

    def render(self, request:StrRequest) -> T.Union[bytes, NotDoneYet]:
        """
            Relays the request to the wrapped class instance with some caveats.

            If the wrapped instance has a method named "prefilter", that is passed the request first

            If the wrapped instance doesn't have a method named "render", it looks for a method that matches
                "render_{Request.method}" (eg, render_GET or render_POST).

            Finally it looks for a postfilter method and passes both the output of the render method and the request
                so that changes can be made if necessary.

        Args:
            request: The Request object (requesting headers, args, client ip, etc)

        Returns:
            T.Union[bytes, NOT_DONE_YET]: Content to be sent to the client or if NOT_DONE_YET, hang the connection until
                the resource closes it.  (or it times out)
        """
        request_kwargs = getattr(request, "_view_args", {})
        request_method = getattr(request, "method").decode("utf-8").upper()

        if hasattr(self.instance, "prefilter"):
            prefilter = getattr(self.instance, "prefilter")
            prefilter_result = prefilter(request, self)
        else:
            prefilter_result = None

        # noinspection PyUnusedLocal
        render_target = None

        if hasattr(self.instance, "render"):
            render_target = getattr(self.instance, "render", None)
        else:
            render_target = getattr(self.instance, f"render_{request_method}", None)

        assert render_target is not None, \
            f"Unable to find render|render_{request_method} method for {self.kls_view} - {self.instance}"

        result = render_target(request, **request_kwargs)

        if hasattr(self.instance, "post_filter"):
            post_result = getattr(self.instance, "post_filter")(request, result)
            result = post_result
            assert post_result is not None, f"post_filter for {self.kls_view} must not return None"

        return sanitize_render_output(result)


    def __repr__(self): # pragma: no cover
        instance_repr = f"<{self.instance.__class__.__name__} {self.instance!r}/>"
        return f"<{self.__class__.__name__} at {id(self)!r} instance={instance_repr}/>"