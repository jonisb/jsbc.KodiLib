# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals, division, absolute_import

import unittest


class test_Kodi_object(unittest.TestCase):
    def test_object_create(self):
        from jsbc import KodiLib
        Kodi = KodiLib.kodi()
        assert type(Kodi) == KodiLib.kodi

    def test_object_connect(self):
        from jsbc import KodiLib
        Kodi = KodiLib.kodi()
        assert None == Kodi.connect()

    def test_object_close(self):
        from jsbc import KodiLib
        Kodi = KodiLib.kodi()
        assert None == Kodi.close()

    def test_KodiLib_Settings_init(self):
        from jsbc import KodiLib
        Kodi = KodiLib.kodi()
        assert Kodi.settings['client']['name'] == 'KodiLib'


class test_KodiInfo(unittest.TestCase):
    def test_KodiInfo(self):
        from jsbc.KodiLib.KodiInfo import KodiInfo
        info = KodiInfo()
        assert info[18]['name'] == 'Kodi'
        assert info[18]['codename'] == 'Leia'
        assert len(info[18]['build']['32bit']) == 1
        assert len(info[18]['build']['64bit']) == 1

        import semantic_version
        assert info[18]['addon'].match(semantic_version.Version('12.0.0'))
        assert info[18]['addon'].match(semantic_version.Version('18.7.0'))
        assert info[18]['gui'].match(semantic_version.Version('5.14.0'))
        assert info[18]['metadata'].match(semantic_version.Version('1.0.0'))
        assert info[18]['metadata'].match(semantic_version.Version('2.1.0'))
        assert info[18]['python'].match(semantic_version.Version('2.1.0'))
        assert info[18]['python'].match(semantic_version.Version('2.26.0'))


from jsbc.KodiLib.testing.client import CreateKodiVersionSpecificTests, base as testbase


class base(testbase):
    def test_eventclient_connect(self):
        from jsbc import KodiLib
        #Kodi = KodiLib.kodi({'client': {'network': {'jsonrpc': {'enabled': False}}}})
        Kodi = KodiLib.kodi()
        Kodi.connect()
        Kodi.disconnect()


CreateKodiVersionSpecificTests(base, globals())
