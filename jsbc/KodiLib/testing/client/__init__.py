# -*- coding: utf-8 -*-


class base():
    @classmethod
    def setUpClass(cls):
        #StartKodi(cls)
        pass

    @classmethod
    def tearDownClass(cls):
        #StopKodi(cls)
        pass

    #@classmethod
    #def jsonrpc(cls, method, params=[], result=True):
    #    result = cls.Kodi.jsonrpc.send(method, params if isinstance(params, (list, dict)) else [params], result)
    #    try:
    #        return result['result']
    #    except KeyError:
    #        raise AssertionError(json.dumps(result['error'], sort_keys=True, indent=4))


def CreateKodiVersionSpecificTests(base, globals=None):
    pass
