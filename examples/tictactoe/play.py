"""
    Back to the basics

    Whenever I worked a new language, if I hadn't rage quit from trying to do "Hello World" the next step
    was to make tic-tac-toe.

"""

import webbrowser

import attr
from txweb import Site, expose
from txweb.sugar.smartcontroller import SmartController


from jinja2 import Environment, FileSystemLoader, select_autoescape

from twisted.web.static import File
from twisted.internet import reactor, defer
from twisted.web.server import NOT_DONE_YET


import game as TTT


 
 
 

class BaseController(metaclass=SmartController):

    def __init__(self):
        self.env = Environment(loader=FileSystemLoader("./templates"),
            autoescape=select_autoescape(["html"])
        )

    def render(self, template_name, context = None):
        context = context if context is not None else {}
        try:
            return self.env.get_template(template_name).render(**context)
        except Exception as ex:
            digest = "\n\t".join([f"{k}:`{repr(v)}`" for k,v in context.items()])

            NEXTLINE = "\n<br>"
            buffer = f"<pre>{NEXTLINE}"
            buffer += ("#" * 60) + NEXTLINE
            buffer += f"Exception on rendering `{template_name}`: {ex}{NEXTLINE}"
            buffer += digest + "\n<br>"
            buffer += "#" * 60 + "\n<br>"
            buffer += "</pre>"

            return buffer
 

def SafeStr(raw):
    if isinstance(raw, bytes):
        return raw.decode()
    elif raw is None:
        return None
    else:
        return str(raw)
        

class Root(BaseController):

    
  
    def action_index(self, request, a_box:int=None, a_state:SafeStr=None):
        
        if a_state in [None, "None"]:
            new_state = [0 for i in range(0,9)]
        else:
            new_state = [int(v) for v in a_state]
        
        
            
        flash = None
        game_map = TTT.Map(data=new_state)
        game = TTT.Rules(game_map)
        

        
        try:
                        
            if a_box is not None:
                game.move(a_box)
                
        except TTT.Error as issue:
            flash = issue.rule_error
        
        print(a_box, a_state, new_state, game_map)
        return self.render("index.html", context=dict(state=game_map, flash=flash))


def main(port=8080):

    site = Site(Root())
    reactor.listenTCP(port, site)
    print(f"Running tic-tac-toe on port {port}")
    reactor.run()

if __name__ == "__main__":
    main()


