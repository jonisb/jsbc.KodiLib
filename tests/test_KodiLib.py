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
