# from __future__ import annotations
#
# import typing as T
# from twisted.web.resource import Resource
#
# from ..errors import HTTPCode
# from ..lib import StrRequest
#
# if T.TYPE_CHECKING:
#     from twisted.python.failure import Failure
#
# class Error(Resource):
#
#     def __init__(self, reason: Failure, verbose:bool = False):
#         self.reason = reason
#         self.verbose = verbose
#         self.request = None
#         self.code = 500
#
#     def make_traceback(self, stack: T.List):
#         pass
#
#     def render(self, request:StrRequest):
#         self.request = request
#
#         if isinstance(self.reason.type, HTTPCode):
#             httpExc = self.reason.value  # type: HTTPCode
#             self.code = httpExc.code
#             if self.code >= 500:
#                 return self.render_error()
#             elif self.code >= 400:
#                 return self.render_bad_resource()
#             elif self.code >= 300:
#                 # TODO we shouldn't reach here
#                 return self.render_redirect()
#             else:
#                 raise Exception("Mishandled error")
#         else:
#             return self.render_error()
#
#
#     def render_error(self):
#         if self.verbose is False:
#             return f"Error {self.code}".encode("UTF-8")
#         else:
#             pass
#
#
