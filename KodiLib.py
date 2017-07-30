# -*- coding: utf-8 -*-
"""
KodiLib:
"""
from __future__ import print_function, unicode_literals, division, absolute_import

import urllib2
import logging

from pythoncompat import OrderedDict

logger = logging.getLogger(__name__)

__version__ = '0.0.0'
__all__ = []


class SettingsClass(OrderedDict):
    def __init__(self, Default=[], Data={}):
        super(SettingsClass, self).__init__()
        self.Default = OrderedDict()
        self.addDefault(Default)
        self.addData(Data)

    def __getitem__(self, key):
        try:
            value = super(SettingsClass, self).__getitem__(key)
            if isinstance(value, dict) or self.Default[key] != value:
                return value
            else:
                del self[key]
        except KeyError:
            if isinstance(self.Default[key], SettingsClass):
                self[key] = self.Default[key]
        return self.Default[key]  # TODO Return copy?

    def __setitem__(self, key, value):
        try:
            if self.Default[key] != value:
                super(SettingsClass, self).__setitem__(key, value)
            else:
                try:
                    del self[key]
                except KeyError:  # TODO
                    pass
        except KeyError:  # TODO
            raise KeyError('Default key not defined', key)

    def addDefault(self, Default):
        for key, value in Default if isinstance(Default, list) else Default.iteritems():
            if isinstance(value, (list, dict)):
                try:
                    self.Default[key].addDefault(value)
                except KeyError:
                    try:
                        self.Default[key] = SettingsClass(value)
                    except ValueError:
                        pass
                    else:
                        continue
                else:
                    continue
            self.Default[key] = value

    def addData(self, Data):
        for key, value in Data.iteritems():
            if isinstance(value, dict):
                try:
                    self[key].addData(value)
                except ValueError:
                    pass
                else:
                    continue
            if self.Default[key] != value:
                self[key] = value
            else:
                del self[key]


def DefaultSettings(Data={}):
    """ """  # TODO

    Settings = SettingsClass([
        ('client', [
            ('name', 'KodiLib'),
            ('cache path', 'cache'),
            ('network', [
                ('User-Agent', "{0}/{1} {2}".format(__name__, __version__, urllib2.build_opener().addheaders[0][1])),
            ]),
            ('icon', [
                ('url', None),
                ('type', None),
            ]),
        ]),
        ('server', [
            ('friendlyName', 'Kodi'),
            ('name', 'Kodi'),
            ('version', ''),
            ('network', [
                ('ip', 'localhost'),
                ('http', {
                    'port': 8080,
                }),
                ('upnp', {
                    'id': '',
                }),
            ]),
        ]),
    ], Data)


    return Settings
