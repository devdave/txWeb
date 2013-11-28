
#TODO terrible module name

#The following lambda's are common checks used to validating routing logic down the line
isExposed  = lambda entity : getattr(entity, "exposed", False)
#TODO should this be an instance check?
isResource = lambda entity : callable(getattr(entity, "render", None))
#TODO safe to assume if it's a resource that it should be exposed
isAction = lambda entity : ( isExposed(entity) and callable(entity) ) or ( isResource(entity) )
isEndpoint = isAction