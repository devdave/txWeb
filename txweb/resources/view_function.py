from txweb.util.basic import sanitize_render_output

from twisted.web import resource
import typing as T

class ViewFunctionResource(resource.Resource):

    isLeaf: T.ClassVar[T.Union[bool, int]] = True

    # noinspection PyMissingConstructor
    def __init__(self, func: T.Callable):
        self.func = func

    @classmethod
    def Wrap(cls, func):
        return cls(func)

    def render(self, request) -> T.Union[int, T.ByteString]:

        request_view_kwargs = getattr(request, "route_args", {})

        result = self.func(request, **request_view_kwargs)

        return sanitize_render_output(result)

    def __repr__(self):
        return f"<{self.__class__.__name__} at {id(self)!r} func={self.func!r}/>"

