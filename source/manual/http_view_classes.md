HTTP View classes
============

View classes are a code style for organizing common http endpoints into one class.   Some caveats apply.



```python
import my_app as app
from txweb.lib.str_request import StrRequest

@app.add_class("/widget")
class Widget:
    
    def __init__(self):
        self.counter = 0
        
    def add_widget(self):
        self.counter += 1
        
    def delete_widget(self):
        self.counter = max(0, self.counter - 1)
    
    @app.expose("/add")
    def add(self, request: StrRequest):
        self.add_widget()
        return f"There are {self.counter} widgets."
    
    @app.expose("/delete")
    def delete(self, request: StrRequest):
        self.delete_widget()
        return f"One widget was deleted, there are now {self.counter}"

```

URLS added to the routing map
-----------------------------

Above would add two new URLS to the map.

1. `/widget/add`
2. `/widget/delete`

Both endpoints default to only accept GET and HEAD requests.

Warning
-------

Though the above example uses `self.counter` as a class persistent variable, care should be taken
on a couple counts:

1. class variables are not persistent between restarts/reloads of the application.

2. You can create memory leaks if you are not careful to manage variables.

3. For more complex applications where a request yields to the reactor while waiting on an 
    expensive/blocking resource, the view class variable can be changed by another request that runs
    while the first request is yielded.