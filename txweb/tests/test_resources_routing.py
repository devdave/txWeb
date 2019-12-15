from txweb.resources import RoutingResource


def test_instantiates_without_error():

    class FakeSite():
        pass

    fake_site = FakeSite()

    resource = RoutingResource(fake_site)
