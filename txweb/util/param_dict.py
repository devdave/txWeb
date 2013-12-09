

class ParamDict(dict):

    def first(self, key, default = None):
        """
            Helper to provide request.args.get(key, [default])[0]

        """
        return self.get(key, [default])[0]


    def __getattr__(self, key):
        """
            Really can't help myself with shortcuts
        """
        return self.first(key)
