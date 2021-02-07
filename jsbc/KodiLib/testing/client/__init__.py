# -*- coding: utf-8 -*-
import unittest

from jsbc.KodiLib.KodiInfo import KodiInfo


def StartKodi(cls):
    #KodiDir = SetupKodi(cls)
    #cls.KodiProc = RunKodi(KodiDir)
    #ssdp.waitForDevice(id=UUID[cls.Version][cls.Bitness])
    #import time
    #time.sleep(5)
    #cls.Kodi = ConnectKodi()
    pass


def StopKodi(cls):
    """
    try:
        cls.Kodi.jsonrpc.send("Application.Quit")
        del cls.Kodi
    except AttributeError:
        cls.KodiProc.terminate()
    while True:
        try:
            cls.KodiProc.wait(timeout=30)
            break
        except TypeError:
            if not cls.KodiProc.poll():
                import time
                time.sleep(1)
                continue
            else:
                break
        except subprocess.TimeoutExpired:
            print("\nKill, kill")
            cls.KodiProc.terminate()
    """


class base():
    @classmethod
    def setUpClass(cls):
        StartKodi(cls)

    @classmethod
    def tearDownClass(cls):
        StopKodi(cls)

    #@classmethod
    #def jsonrpc(cls, method, params=[], result=True):
    #    result = cls.Kodi.jsonrpc.send(method, params if isinstance(params, (list, dict)) else [params], result)
    #    try:
    #        return result['result']
    #    except KeyError:
    #        raise AssertionError(json.dumps(result['error'], sort_keys=True, indent=4))


def CreateKodiVersionSpecificTests(base, globals=None):
    TestClassDict = {}
    info = KodiInfo()
    for ver in info:
        if 'build' in info[ver]:
            for bits in info[ver]['build']:
                classname = str('Test_kodi{ver}_{bits}'.format(ver=ver, bits=bits))
                TestClassDict[classname] = type(classname,(base, unittest.TestCase), {'Version': ver, 'Bitness': bits, 'KodiInfo': info[ver]})
    if globals:
        globals.update(TestClassDict)
    return TestClassDict
