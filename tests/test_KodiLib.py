# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals, division, absolute_import

import unittest

class test_Kodi_object(unittest.TestCase):
    def test_object_create(self):
        import KodiLib as KodiLib
        Kodi = KodiLib.kodi()
        assert type(Kodi) == KodiLib.kodi

    def test_object_connect(self):
        import KodiLib as KodiLib
        Kodi = KodiLib.kodi()
        assert None == Kodi.connect()

    def test_object_close(self):
        import KodiLib as KodiLib
        Kodi = KodiLib.kodi()
        assert None == Kodi.close()

    def test_KodiLib_Settings_init(self):
        #import jsbc.KodiLib as KodiLib
        import KodiLib as KodiLib
        Kodi = KodiLib.kodi()
        assert Kodi.settings['client']['name'] == 'KodiLib'

class test_SettingsClass(unittest.TestCase):
    def test_object_create(self):
        import KodiLib as KodiLib
        Settings = KodiLib.SettingsClass()
        assert type(Settings) == KodiLib.SettingsClass


class test_eventserver_actions(unittest.TestCase):
    def test_object_create(self):
        import KodiLib as KodiLib
        Settings = KodiLib.DefaultSettings()
        Settings['server']['network']['ip'] = '192.168.1.102'

        Kodi = KodiLib.kodi(Settings)
        Kodi.connect()

        actions = Kodi.GetCommands('actions')
        assert list(actions.keys()) == ['All', '', '3D movie playback/GUI', 'PVR actions', 'Mouse actions', 'Touch', 'Voice', 'Do nothing / error action']

        Kodi.close()