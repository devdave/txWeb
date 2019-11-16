
# twisted imports
from twisted.web import resource

from txweb.util.basic import sanitize_render_output
# stdlib
import typing as T


class ViewClassResource(resource.Resource):

    isLeaf: T.ClassVar[T.Union[bool, int]] = True

    # noinspection PyMissingConstructor
    def __init__(self, kls_view, instance=None):
        self.kls_view = kls_view
        self.instance = instance  # TODO is this needed?

    def getChildWithDefault(self, path, request):
        if hasattr(self.instance, "prefilter"):
            return self.instance.pre_filter(request, path, self)
        else:
            return self

    def render(self, request) -> T.Union[bytes, int]:
        request_kwargs = getattr(request, "_view_args", {})
        request_method = getattr(request, "method").decode("utf-8").toupper()

        prefilter_result = getattr(self.instance, "prefilter", lambda r, v: None)(request, self)

        # noinspection PyUnusedLocal
        render_target = None

        if isinstance(prefilter_result, resource.Resource):
            render_target = getattr(prefilter_result, "render")
        elif hasattr(self.instance, "render"):
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


class ViewFunctionResource(resource.Resource):

    isLeaf: T.ClassVar[T.Union[bool, int]] = True

    # noinspection PyMissingConstructor
    def __init__(self, func: T.Callable):
        self.func = func

    def render(self, request) -> T.Union[int, T.ByteString]:

        request_view_kwargs = getattr(request, "route_args", {})

        result = self.func(request, **request_view_kwargs)

        return sanitize_render_output(result)

    def getChild(self, child_name, request):
        return self
