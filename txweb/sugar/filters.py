

from decorator import decorator
from twisted.web.server import NOT_DONE_YET
import json
import inspect

def _json_out(func, *args, **kwargs):
    """
        Assumes args[0] == Request instance!

        :param func: the target for decoration
        :param args: args splat
        :param kwargs: dictionary splat
    """

    if len(args) > 0 and hasattr(args[0], 'setHeader'):
        request = args[0]
    elif len(args) > 1 and hasattr(args[1], 'setHeader'):
        request = args[1]
    else:
        raise ValueError("Expected position #0 or #1 to be type Request, got %s for %s" % (args, func))

    request.setHeader("content-type", "application/json")
    try:
        x = func(*args, **kwargs)
    except Exception as e:
        #TODO - It could be/is a HUGE security issue to blindly trx Exception info
        x = {
                "success": False,
                "error": str(e),
                "error_type": ".".join(
                    [
                        e.__class__.__module__,
                        e.__class__.__name__
                    ]
                )
            }


    if x == NOT_DONE_YET:
        return NOT_DONE_YET
    else:
        #TODO note to use -o to optimize asserts out
        assert isinstance(x, dict), "Expected return from %s to be dict, got %s" % (func, x,)
        #TODO is this goofy?
        x['success'] = x.get('success', True)
        return json.dumps(x)

json_out = decorator(_json_out)