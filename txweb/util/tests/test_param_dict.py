
from txweb.util.param_dict import ParamDict

def test_no_syntax_errors():
    x = ParamDict()

def test_handles_defaults():

    x = ParamDict()
    assert "bar" == x.first("foo", "bar")


def test_grabs_actual_first():
    x = ParamDict()
    x['foo'] = [1,2,3,5]
    assert x.first("foo", 7) == 1
    assert x.first("foo") == 1

def test_provides_none_on_bad_key():
    x = ParamDict()
    assert x.first("foo") is None

def test_subsumes_old_dict():

    z = {"foo":"bar", "numbers":(1,2,3), "numbahs":[1,2,3]}
    y = dict(z.items())
    x = ParamDict(y)
    for k in z.keys():
        assert k in x
        assert x[k] == z[k]


def test_getattr_nones():
    x = ParamDict()
    assert x.name == None

def test_getattr_returns_first():
    v = "bob"
    x = ParamDict(name = [v])
    assert x.name == v