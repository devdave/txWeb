# twisted imports
from twisted.internet import defer
from twisted.web.server import NOT_DONE_YET
from twisted.web import resource

# stdlib
import typing


def sanitize_render_output(output: typing.Any) -> typing.Union[int, typing.ByteString]:
    """
        Attempt to sanitize output and return a value safe for twisted.web.server.Site to process

    :param output: the result of calling either a ViewClassResource or ViewFunctionResources render method
    :return:
    """

    returnValue = None
    import warnings

    if isinstance(output, defer.Deferred):
        returnValue = NOT_DONE_YET
    elif output is NOT_DONE_YET:
        returnValue = NOT_DONE_YET
    elif isinstance(output, str):
        returnValue = output.encode("utf-8")
    elif isinstance(output, int):
        returnValue = str(output).encode("utf-8")
    elif isinstance(output, bytes):
        returnValue = str(output).encode("utf-8")
    else:
        raise RuntimeError(f"render outputted {type(output)}, expected bytes,str,int, or NOT_DONE_YET")

    assert isinstance(returnValue, bytes) or returnValue == NOT_DONE_YET, f"Bad response data {type(returnValue)}-{returnValue!r}"

    return returnValue


class ViewClassResource(resource.Resource):

    isLeaf: typing.ClassVar[typing.Union[bool, int]] = True

    def __init__(self, kls_view, instance=None):
        self.kls_view = kls_view
        self.instance = instance # TODO is this needed?

    def getChildWithDefault(self, path, request):
        if hasattr(self.instance, "prefilter"):
            return self.instance.pre_filter(request, path, self)
        else:
            return self

    def render(self, request)->bytes:
        str_request_kwargs = request.path.decode()

        request_kwargs = getattr(request, "_view_args", {})
        request_method = getattr(request, "method").decode("utf-8").toupper()

        prefilter_result = getattr(self.instance, "prefilter", lambda r,v: None)(request, self)

        render_target = None

        if isinstance(prefilter_result, resource.Resource):
            render_target = getattr(prefilter_result, "render")
        elif hasattr(self.instance, "render"):
            render_target = getattr(self.instance, "render", None)
        else:
            render_target = getattr(self.instance, f"render_{request_method}", None)

        assert render_target is not None, f"Unable to find render|render_{request_method} method for {self.kls_view} - {self.instance}"

        result = render_target(request, **request_kwargs)

        if hasattr(self.instance, "post_filter"):
            post_result = getattr(self.instance, "post_filter")(request, result)
            result = post_result
            assert post_result is not None, f"post_filter for {self.kls_view} must not return None"

        return sanitize_render_output(result)


class ViewFunctionResource(resource.Resource):

    isLeaf: typing.ClassVar[typing.Union[bool, int]] = True

    def __init__(self, func: typing.Callable):
        self.func = func # rework to callable

    def render(self, request):

        request_view_kwargs = getattr(request, "route_args", {})

        result = self.func(request, **request_view_kwargs)


        return sanitize_render_output(result)


    def getChild(self, child_name, request):
        return self

