from twisted.web import resource
import typing as T

class GenericError(resource.Resource):

    isLeaf: T.ClassVar[T.Union[bool, int]] = True

    # noinspection PyMissingConstructor
    def __init__(self, message: str, error_code: T.Optional[int] = 500):
        self.message = message  # type: typing.Text
        self.error_code = error_code  #type: int

    def render(self):
        raise NotImplementedError("TODO")