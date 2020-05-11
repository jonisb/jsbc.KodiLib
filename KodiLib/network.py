# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals, division, absolute_import

import os
import contextlib
try:
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError, URLError
except ImportError:
    from urllib2 import urlopen, Request, HTTPError, URLError
import time
try:
    import cPickle
except ImportError:
    import pickle as cPickle
import bz2

import logging
logger = logging.getLogger(__name__)

def init(settings):
    global Settings
    Settings = settings


def DownloadPage(URL, hdr):
    """ """ # TODO
    try:
        with contextlib.closing(urlopen(Request(URL, headers=hdr))) as Builtins:
            encoding = Builtins.headers['content-type'].split('charset=')[-1]
            Actions = Builtins.read()
            try:
                Actions = unicode(Actions, encoding)
            except LookupError:
                pass

    except (HTTPError, URLError) as err:
        if err.code == 304:
            Result = {'Code': err.code}
        else:
            print('{0}: Error: Can\'t connect to "{1}".'.format(Settings['client']['name'], URL)) # TODO
            raise
    else:
        Result = {'Code': Builtins.getcode(), 'Page': Actions, 'Cache-Expire': time.time() + int(next(x for x in Builtins.headers['Cache-Control'].split(',') if 'max-age' in x).split('=')[1])}
        try:
            Result['ETag'] = Builtins.headers['ETag']
        except:
            pass
        try:
            Result['Last-Modified'] = Builtins.headers['Last-Modified']
        except:
            pass

    return Result


def DownloadURL(URL, force=False, cached=False): # TODO
    """ """  # TODO
    try:
        DownloadURL.URLCache
    except AttributeError:
        try:
            with open(os.path.join(Settings['client']['cache path'], 'URLCache.bz2'), 'rb') as f:
                DownloadURL.URLCache = cPickle.loads(bz2.decompress(f.read()))
        except IOError:
            DownloadURL.URLCache = {}
    finally:
        URLCache = DownloadURL.URLCache

    hdr = {'User-Agent': Settings['client']['network']['User-Agent']}
    SaveCache = False
    try:
        from urlparse import urlparse
    except ImportError:
        from urllib.parse import urlparse

    if urlparse(URL).scheme in ('file', ''):
        with open(urlparse(URL).path, 'rb') as f:
            Actions = {'Page': f.read()}
    else:
        if cached and URL in URLCache:
            Actions = URLCache[URL]
        elif not force and URL in URLCache and 'Cache-Expire' in URLCache[URL]:
            if time.time() > URLCache[URL]['Cache-Expire']:
                try:
                    hdr['If-None-Match'] = URLCache[URL]['ETag']
                except KeyError:
                    pass
                try:
                    hdr['If-Modified-Since'] = URLCache[URL]['Last-Modified']
                except KeyError:
                    pass
                Actions = DownloadPage(URL, hdr)
                if Actions['Code'] == 304:
                    Actions = URLCache[URL]
                elif Actions['Code'] == 200:
                    SaveCache = True
                else:
                    print("Unknown code:", Actions['Code']) # TODO
            else:
                Actions = URLCache[URL]
        else:
            Actions = DownloadPage(URL, hdr)
            SaveCache = True

    if SaveCache:
        URLCache[URL] = Actions
        with open(os.path.join(Settings['client']['cache path'], 'URLCache.bz2'), 'wb') as f:
            f.write(bz2.compress(cPickle.dumps(URLCache)))

    return Actions['Page']
