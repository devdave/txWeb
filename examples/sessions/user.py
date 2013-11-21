
from zope.interface import Interface, Attribute, implements
from twisted.python.components import registerAdapter
from twisted.web.server import Session
from functools import partial

"""
    FYI Twisted uses zope.interface

    The short explanation is that twisted web's session object can be
    polymorpheus ( It can quack like a dog and bark like a duck ) so having
    interfaces allows for fairly complex user session objects.

    To explain, imagine you have a User object that points to Bob Smith's identity
    and therefore his privileges.  Life is good and all is well until one day
    you get a logical error that only seems to exist with Bob Smith.

    Super sane approach would be to have a staging/dev authenticator that allows Alice
    the developer to login to Bob's account using a sha1 digest but we didn't do that.
    Instead, when Alice authenticated she was given an AdminUser session which is a subclass
    of WebUser but with the ability to masquerade as Bob when she requests it.

    Now ideally Alice could repeat the steps Bob provided ( if he provided any ) to reproduce
    the bug he's experiencing and Alice can percieve the application as Bob.

    FYI I am pretty bad at giving good examples as the problem Bob's experiencing might
    just be in his session object that aren't apparent with a subclass ( as it might fix the problem)

"""
class IWebUser(Interface):
    uid = Attribute("The session user's id")
    name = Attribute("The name of the user")

    #Perhaps a ClientMailbox might be more appropriate instead of packing
    # it all into the session?
    messages = Attribute("A list of messages in a FiFo stack like list")
    client_socket = Attribute("A ZMQ client subscriber socket")


class WebUser(object):
    implements(IWebUser)
    user_count = 0

    def __init__(self, session):
        self.session = session
        self.user_count += 1
        self.name = "NewUser%s" % self.user_count
        self.messages = []
        self.client_socket = None

        self.session.notifyOnExpire( self.shutdown )

    @property
    def uid(self):
        return self.session.uid if self.session else "-1"

    def addSocket(self, socket):
        self.client_socket = socket


    def shutdown(self):
        if self.client_socket:
            self.client_socket.shutdown()
        print "Session %s has died, long live the session" % self.uid



registerAdapter(WebUser, Session, IWebUser)