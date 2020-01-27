Error handling
==============

There are two options for handling/interacting with application errors

* Total control
* Pass thru

The only difference between total and pass thru control of error handling is returning 
False from an error handler, saying that the handler didn't handle the error but instead
is letting it pass thru back to the Default or Debug handler for final processing.


## Total control

```python
    
    from twisted.web.util import redirectTo
    app = Application(__name__)
    myMagicRedirector = Magic() # you supply this
    
    @app.handle_error(404):
    def redirect_on_missing(request, reason):
        """
            A handler to redirect to an alternate page via
            the magic powers of some myMagicRedirector
            eg /user/edit/1 to /user/1/edit
        """
        global myMagicRedirector
        alternate_page_url = myMagicRedirector(request)
        if alternate_page_url is not None:
            body = redirectTo(alternate_page_url, request)
            # to have the client browser accept this as valid, the length must be set
            request.setHeader("Content-length", str(len(body)).encode("utf-8"))
            request.write(body)
            return
        else:
            # let the default error handler handle this - like pass thru below.
            return False        

        
        return
```

With total control, you are responsible for ensuring your error handler catches its 
own internal errors as well as ensuring it handles errors either definitively (eg HTTP 500 error code).

## Pass Thru
```python
    app = Application(__name__)
    bus = PubSub("my_error_reporter")

    @app.handle_error(500):
    def track_errors(request, reason):
        global bus
        try:
            # Perhaps send the error across another connection to a MessageQueue service
            bus.emit("error.event", f"{reason.type}:{reason.message}")
        finally:
            return False
```


