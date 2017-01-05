# -*- coding: utf-8 -*-
"""
KodiLib:
"""
from __future__ import print_function, unicode_literals, division, absolute_import

import logging

logger = logging.getLogger(__name__)

__version__ = '0.0.0'
__all__ = [] # "echo", "surround", "reverse"

logger.info('Importing "OrderedDict" module.')
try:
    from collections import OrderedDict
except ImportError:
    logger.warning('Failed to import "OrderedDict" module, trying local module.')
    try:
        from ordereddict import OrderedDict
    except ImportError:
        logger.exception('Failed to import local "OrderedDict" module, aborting.')
        raise
logger.info('Importing "OrderedDict" module, done.')


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
                #super(SettingsClass, self).__delitem__(key)
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
    return SettingsClass([
        ('client', [
            ('name', 'KodiLib'),
        ]),
    ], Data)
    """
        ('client', [
            ('name', 'KodiLib'),
            ('network', [
                ('useragent', "UserAgent"),
                ('tcp', {
                    'timeout': 1,
                    'buffersize': 4096,
                }),
            ]),
            ('jsonrpc', [
                ('enabled', True),
                ('notifications', {
                    'enabled': True,
                }),
            ]),
        ]),
    ])
    """
