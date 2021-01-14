
Short history
-------------

I started on TxWeb/Texas all the way back in early 2011 and have iterated and done major 
refactors of this project since then.

Generation one of TxWeb mimicked the original CherryPy in that a website was an object graph

```python
    class Widget():
    
        def index(self, request):
            return "I am the list of widgets"
        
        def create(self, request):
            pass
        
        def replace(self, request):
            pass
        
        def update(self, request):
            pass
        
        def delete(self, request):
            pass
    
    class Root():

        def index(self, request):
            return "Hello world"

        widgets = Widget()
```

That created a URL heirachy like

```python
    /
    /widgets/
    /widgets/create/
    /widgets/replace/
    /widgets/update/
    /widgets/delete/
```

I switched that out for my own URL parser which kind of worked but for anyone familiar
with werkzeug, is a massive project to itself.

In 2020, I gutted out my own URL parser in favor of using werkzeug (similar if not exactly like
Klein).
