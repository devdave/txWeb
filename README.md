Twisted Web extension
=====================

   A routing extension to twisted.web
   
Status
======
Super beta

Major issues
============
Error handling needs to be drastically improved/refactored


Purpose & History
======

This project started a few months around when Klein did and if you want
a more complete web framework I would recommend that over txWeb.

TxWeb is an overlay above the twisted.web module/package along with providing a routing resource mechanism.

```python

from txweb import Application

app = Application(__name__)

@app,route("/hello")
def provide_hello(request):
    return "Hello World"


@app.route("/args")
def provide_arguments(request):
    who = request.args.get("who", default="No body")
    says = request.args.get("says", default="Nothing")
    #Python 3.8
    return f"{who} said {says}"
# would output "DevDave said Hello" given /args?who=DevDave&says=Hello
# would output "No body said Nothing" give /args

@app.route("/process_form")
def handle_form(request):
    input1 = request.form.get("input1")
    return ""

 


    
```

