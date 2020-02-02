from __future__ import annotations
from txweb.util.basic import sanitize_render_output


from twisted.web import resource
import typing as T


PrefilterFunc = T.NewType("PrefilterFunc", T.Callable[["StrRequest"], None])
PostFilterFunc = T.NewType("PostFilterFunc", T.Callable[["StrRequest", T.Union[str, bytes]], T.Union[str,bytes]])


class ViewFunctionResource(resource.Resource):

    isLeaf: T.ClassVar[T.Union[bool, int]] = True

    # noinspection PyMissingConstructor
    def __init__(self, func: T.Callable, prefilter:T.Union[PrefilterFunc, None]=None, postfilter:T.Union[PostFilterFunc, None]=None):
        self.func = func
        self.prefilter = prefilter
        self.postfilter = postfilter


    @classmethod
    def Wrap(cls, func):
        return cls(func)

    def render(self, request) -> T.Union[int, T.ByteString]:

        request_view_kwargs = getattr(request, "route_args", {})

        if self.prefilter:
            self.prefilter(request)

        func = self.func
        result_body = func(request, **request_view_kwargs)

        if self.postfilter:
            result_body = self.postfilter(request, result_body)

        return sanitize_render_output(result_body)

    def __repr__(self):
        return f"<{self.__class__.__name__} at {id(self)!r} func={self.func!r}/>"

