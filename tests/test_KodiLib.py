# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals, division, absolute_import

import unittest

class test_testing(unittest.TestCase):
    def test_KodiLib_Settings_init(self):
        #import jsbc.KodiLib as KodiLib
        import KodiLib as KodiLib
        Kodi = KodiLib.kodi()
        assert type(Kodi) == KodiLib.kodi
        assert Kodi.settings['client']['name'] == 'KodiLib'
