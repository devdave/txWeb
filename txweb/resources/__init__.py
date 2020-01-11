"""
    Fundamental resources of Texas Web

    RoutingResource should be considered special and not used again.   You could concievably
    nest a RoutingResource inside of another RoutingResource but I have no ideq what that would do and
    I think it would blow up in strange ways.
"""
from .view_class import ViewClassResource
from .view_function import ViewFunctionResource
from .simple_file import SimpleFile
from .routing import RoutingResource
from .directory import Directory

__ALL__ = ["ViewClassResource", "ViewFunctionResource", "SimpleFile", "Directory", "RoutingResource"]

