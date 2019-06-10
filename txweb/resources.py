def sanitize_render_output(output: typing.Any) -> typing.Union[int, typing.ByteString]:
    """
        Attempt to sanitize output and return a value safe for twisted.web.server.Site to process

    :param output: the result of calling either a ViewClassResource or ViewFunctionResources render method
    :return:
    """

    returnValue = None
    import warnings

    if isinstance(output, defer.Deferred):
        result = NOT_DONE_YET
    elif output is NOT_DONE_YET:
        pass
    elif isinstance(output, str):
        result = output.encode("utf-8")
    elif isinstance(output, bytes):
        result = str(output).encode("utf-8")
    else:
        raise RuntimeError(f"render outputted {type(output)}, expected bytes,str,int, or NOT_DONE_YET")

    return returnValue
