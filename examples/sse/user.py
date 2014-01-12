
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
        """
            :param session: http://twistedmatrix.com/documents/current/api/twisted.web.server.Session.html
        """
        self.session = session
        self.user_count += 1 #Housekeeping/debugging metric - also demonstrates that a lot of
        # twisted can/is memory resident through the life of the system.
        """
            Instead of self.name, you might bind a reference to a
                UserAccount object and refer to that in WebUser's code.

            All concerns about XSS, session fixiation/hijacking apply
                as twisted relies on COOKIES and doesn't do any additional checks
                like is session.user_ip == request.client_ip
                Plus side, they are session cookies so they expire on client window close.

            That said, for just example purposes.  If session.name is None, assume
            this is a new user.

        """
        self.name = None

        """
            Stock twisted Session's can generally hold anything in them without
             concern of serialization/state trainwrecks as they're stored in
             twisted Site.sessions which is a dict.

            Downside is that more so then ever you need to pay attention to Python's
             by-reference mechanism to avoid epic memory leaks or worse ( who's modified this? Who needs this?
             ah god what is this? ).

            Saving grace is that twisted is a single process/async framework so you don't need
             to deal with locks BUT that doesn't mean you shouldn't worry about context fights where:
             User connects to /endpoint1 which calls expensive deferred thing and in the middle
             User connects to /endpoint2 which changes something /endpoint1 was relying on before
              /endpoint1 regains context and tries to cleanup.

            Generally grab everything you need for a context and keep it in disposable/GC friendly
             variables and then make sure assumptions are still correct in between deferred's

        """
        self.messages = []
        self.client_socket = None

        """
            Generally you always want to bind to notifyOnExpire so you can
                do house keeping and such.
        """

        self.session.notifyOnExpire( self.shutdown )

    @property
    def uid(self):
        return self.session.uid if self.session else "-1"

    def addSocket(self, socket):
        self.client_socket = socket

    def addMessage(self, message):
        self.messages.append(message)

    #def __len__ - can be conveniant for checking on messages BUT be careful with this
    # as `if self.my_session` will == False even if its not if messages is empty

    def shutdown(self):
        if self.client_socket:
            self.client_socket.shutdown()
        print "Session %s has died, long live the session" % self.uid



registerAdapter(WebUser, Session, IWebUser)