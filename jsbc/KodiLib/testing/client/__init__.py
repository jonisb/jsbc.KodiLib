# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals, division, absolute_import

import os
import requests
import subprocess
from bs4 import BeautifulSoup
import logging
import unittest

from jsbc.compat.python3 import *
from jsbc.compat.pathlib import pathlib
from jsbc.compat.urllib.urlparse import urlparse
from jsbc.Toolbox import SettingsClass, DefaultSettings, settings
from jsbc import network
from ...KodiInfo import KodiInfo
from .... import KodiLib
logger = logging.getLogger(__name__)

settingsDefaults = [
    ('client', [
        ('name', 'KodiLib.testing'),
        #('version', __version__),
        #('cache path', None),
        #('cache path', '.'),
    ]),
    ('servers', [
        (str, []),
    ]),
]


def SetupKodi(cls):
    logger.debug("SetupKodi starting")
    Version = cls.Version
    Bitness = cls.Bitness
    KodiInfo = cls.KodiInfo
    URL = KodiInfo['build'][Bitness]['URL']

    #KodiDir = SetupDir / f'Kodi{Version}_{Bitness}'
    KodiDir = SetupDir / 'Kodi{0}_{1}'.format(Version, Bitness)
    filename = CacheDir / pathlib.Path(urlparse(URL).path).name
    if not filename.exists():
        response = requests.get(URL)
        filename.write_bytes(response.content)
        del response

    dstdir = KodiDir / 'portable_data'
    #if not dstdir.exists():
    if not KodiDir.exists():
        #SevenZip = ['7z.exe', 'x', '-y', str(filename), f'-o{KodiDir}']
        SevenZip = ['7z.exe', 'x', '-y', str(filename), '-o{KodiDir}'.format(KodiDir=KodiDir)]
        #proc = subprocess.run(SevenZip, stdout=subprocess.PIPE)
        proc = subprocess.call(SevenZip, stdout=subprocess.PIPE)
    logger.debug("SetupKodi KodiDir.exists() = %s", KodiDir.exists())

    dstdir = dstdir / r"userdata\guisettings.xml"
    if not dstdir.exists():
        dstdir.parent.mkdir(parents=True, exist_ok=True)
        guisettings =  """\
<settings>
    <general>
        <settinglevel>3</settinglevel>
    </general>
    <services>
        <upnprenderer>true</upnprenderer>
        <upnpannounce>false</upnpannounce>
    </services>
    <viewstates>
    </viewstates>
</settings>
"""
        guisettings = BeautifulSoup(guisettings, 'html.parser')
        if Version < 18:
            guisettings.settings.general.append(guisettings.new_tag("addonupdates"))
            guisettings.settings.general.addonupdates.string = str(2)
            guisettings.settings.services.append(guisettings.new_tag("esallinterfaces"))
            guisettings.settings.services.esallinterfaces.string = 'true'
        else:
            guisettings.settings['version'] = str(2)
            tag = guisettings.new_tag("setting")
            tag['id'] = "general.addonupdates"
            tag.string = str(2)
            guisettings.settings.append(tag)
            tag = guisettings.new_tag("setting")
            tag['id'] = "services.esallinterfaces"
            tag.string = 'true'
            guisettings.settings.append(tag)
            tag = guisettings.new_tag("setting")
            tag['id'] = "services.upnp"
            tag.string = 'true'
            guisettings.settings.append(tag)
        #dstdir.write_text(str(guisettings), 'utf-8')
        try:
            dstdir.write_text(unicode(guisettings), 'utf-8')
        except NameError:
            dstdir.write_text(str(guisettings), 'utf-8')

    #dstdir = KodiDir / 'portable_data' / r"userdata\upnpserver.xml"
    dstdir = KodiDir / 'portable_data' / "userdata/upnpserver.xml"
    if not dstdir.exists():
    #      upnpserver =  f"""\
#  <upnpserver>
    #  <UUIDRenderer>{UUID[Version][Bitness]}</UUIDRenderer>
#  </upnpserver>
#  """
        try:
            UUID[str(Version)]
        except KeyError:
            UUID[str(Version)] = {}

        try:
            UUID[str(Version)][Bitness]
        except KeyError:
            import uuid
            UUID[str(Version)][Bitness] = str(uuid.uuid4())
            settings.save()
        upnpserver =  """\
<upnpserver>
    <UUIDRenderer>{0}</UUIDRenderer>
</upnpserver>
""".format(UUID[str(Version)][Bitness])
        dstdir.write_text(upnpserver, 'utf-8')

    logger.debug("SetupKodi ending")
    return KodiDir


def RunKodi(KodiDir):
    try:
        KodiCmd = [unicode(KodiDir / 'kodi.exe'), '-p']
    except NameError:
        KodiCmd = [str(KodiDir / 'kodi.exe'), '-p']
    return subprocess.Popen(KodiCmd)


def ConnectKodi():
    logger.debug("ConnectKodi starting")
    Kodi = KodiLib.kodi()
    Kodi.connect()
    logger.debug("ConnectKodi ending")
    return Kodi


def StartKodi(cls):
    logger.debug("StartKodi starting")
    KodiDir = SetupKodi(cls)
    cls.KodiProc = RunKodi(KodiDir)
    logger.debug("RunKodi: %s", cls.KodiProc.poll())
    #ssdp.waitForDevice(id=UUID[cls.Version][cls.Bitness])
    settings['client']['network']['eventclient']['enabled'] = True
    settings['client']['network']['jsonrpc']['enabled'] = True
    import time
    time.sleep(10)
    cls.Kodi = ConnectKodi()
    logger.debug("StartKodi ending")


def StopKodi(cls):
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
                try:
                    TestClassDict[classname] = type(classname,(base, unittest.TestCase), {'Version': ver, 'Bitness': bits, 'KodiInfo': info[ver]})
                except TypeError:
                    TestClassDict[classname] = type(bytes(classname),(base, unittest.TestCase), {'Version': ver, 'Bitness': bits, 'KodiInfo': info[ver]})
    if globals:
        globals.update(TestClassDict)
    return TestClassDict

DefaultSettings(settingsDefaults)
try:
    settings.load()
except FileNotFoundError:
    pass
UUID = settings['servers']
CacheDir = pathlib.Path(os.path.expandvars(str(settings['client']['cache path'])))
#CacheDir.mkdir(parents=True, exist_ok=True)
SetupDir = CacheDir / "TestInstall"
SetupDir.mkdir(parents=True, exist_ok=True)
