# -*- coding: utf-8 -*-
"""
Python compatiblity library
"""  # TODO
from __future__ import print_function, unicode_literals, division, absolute_import

import logging

logger = logging.getLogger(__name__)

__version__ = '0.0.0'
__all__ = ["OrderedDict"]

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
