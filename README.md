Twisted Web extension
=====================

   A routing extension to twisted.web.


Purpose & History
======

This project started a few months around when Klein did and if you want
a more complete web framework I would recommend that over txWeb.

TxWeb has been drastically refactored to provide a Web Resource for the 
stock/basic twisted web interface that cuts down on the amount of cruft needed.  


Usage
-----



Gotchas with chrome
-------------------
I have a simple txWeb service with endpoints:

* index
* say
* hear

Index prints `"hello world %s" % time.time()`

Say pushes `"hello %s" % time.time()` onto a 0MQ pub/sub socket

Hear waits for a message to happen on the 0MQ pub/sub socket and than publishes it.


Now say I've got 4 browser windows open: 1 called index, 2 are blocking on hear, and finally I call say.

I expected both hears to end their blocking state and print the same "hello 1234" message BUT instead the first hear returns while the second one stays blocking.

This took me a bit to debug BUT what happens is that the first /hear blocks on its call to the server while the second is QUEUED INSIDE CHROME and never calls the server.  It's only after the first one completes ( timeout or success ) that the second one calls the server.