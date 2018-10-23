

def fetch_first(self, src):
    val = self.fetch(src)
    if isinstance(val, list):
        val = val[0]

    return val
