# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals, division, absolute_import

import platform

try:
    from bs4 import BeautifulSoup
except ImportError:
    from BeautifulSoup4 import BeautifulSoup
import regex
import semantic_version

from jsbc import network

from collections import defaultdict
ArchMap = defaultdict(lambda: '32bit', {'x64': '64bit'})


def GetLinkList(URL, pattern='.exe'):
    try:
        response = network.DownloadURL(URL)
    except Exception:
        raise
        return []

    soup = BeautifulSoup(response, 'html.parser')
    Links, Dirs = [], []
    for link in soup('a'):
        try:
            link['title']
            if link['title']:
                if link.string.endswith('/'):
                    Dirs.append(URL + link.string)
                else:
                    if link.string.endswith(pattern):
                        Links.append((URL, link.string))
        except Exception:
            pass
    for URL in Dirs:
        Links.extend(GetLinkList(URL))

    return Links


def GetKodiEXEList(List, build):
    Vers = []
    for base, filename in List:
        if build == 'release':
            result = regex.match(r"kodi-(\d{1,3}\.\d{1,3})-(.+?)(?:[-_](x(?:86|64)))?.exe", filename)
            if result:
                #ver = semantic_version.Version(result.group(1), partial=True)
                ver = semantic_version.Version.coerce(result.group(1))
                if ver.major not in Vers:
                    Vers.append(ver.major)
                    yield ver, result.group(2), ArchMap[result.group(3)], base + filename
                continue
        else:
            result = regex.match(r"KodiSetup-(?:\d{{8}})-(?:.+?)-{build}(?:[-_](x(?:86|64)))?.exe".format(build=build), filename)
            if result:
                if build == 'master':
                    ver = 18
                elif build == 'feature_python3':
                    ver = 19
                else:
                    raise TypeError
                yield ver, build, ArchMap[result.group(1)], base + filename
                break


def KodiInfo(Ver=None, CachePath=None):
    try:
        info = KodiInfo.info
        codename_map = KodiInfo.codename_map
    except AttributeError:
        info = {}
        host = "mirrors.kodi.tv"
        repository = 'https://github.com/xbmc/xbmc/'
        buildtypes = ("releases",) # , "nightlies", "test-builds"
        if platform.system() == 'Windows':
            Platform = "windows"
        else:
            raise Exception('Platform not supported: {0}'.format(platform.system()))
        if platform.machine() == 'AMD64':
            bitness = ("win64", "win32")
        else:
            bitness = ("win32",)
        for buildtype in buildtypes:
            for bits in bitness:
                URL = "http://{host}/{buildtype}/{Platform}/{bits}/".format(host=host, buildtype=buildtype, Platform=Platform, bits=bits)
                Links = GetLinkList(URL)
                for ver, codename, bits, URL in GetKodiEXEList(Links, 'release'):
                    try:
                        info[ver.major]['version'] = ver
                    except Exception:
                        info[ver.major] = {'version': ver, 'codename': codename, 'build': {}}
                    else:
                        info[ver.major]['codename'] = codename
                    info[ver.major]['build'][bits] = {'URL': URL}

        branch = 'master'
        URL = repository + "raw/{branch}/".format(branch=branch) + 'version.txt'
        try:
            response = network.DownloadURL(URL)
        except Exception:
            raise
        else:
            for line in response.splitlines():
                #if line.startswith(b'APP_NAME'):
                    #name = line.partition(b' ')[2].decode('ascii')
                #elif line.startswith(b'VERSION_MAJOR'):
                #    version_major = int(line.partition(b' ')[2])
                #elif line.startswith(b'VERSION_MINOR'):
                #    version_minor = int(line.partition(b' ')[2])
                #elif line.startswith(b'VERSION_TAG'):
                #    version_tag = line.partition(b' ')[2].decode('ascii')
                #elif line.startswith(b'ADDON_API'):
                #    version = line.partition(b' ')[2].decode('ascii')
                if line.startswith('APP_NAME'):
                    name = line.partition(' ')[2]
                elif line.startswith('VERSION_MAJOR'):
                    version_major = int(line.partition(' ')[2])
                elif line.startswith('VERSION_MINOR'):
                    version_minor = int(line.partition(' ')[2])
                elif line.startswith('VERSION_TAG'):
                    version_tag = line.partition(' ')[2]
                elif line.startswith('ADDON_API'):
                    version = line.partition(' ')[2]

            info[version_major] = {'codename': 'master'}
            info[version_major]['name'] = name
            #info[version_major]['version'] = semantic_version.Version('{version_major}.{version_minor}-{version_tag}'.format(version_major=version_major, version_minor=version_minor, version_tag=version_tag), partial=True)
            info[version_major]['version'] = semantic_version.Version.coerce('{version_major}.{version_minor}-{version_tag}'.format(version_major=version_major, version_minor=version_minor, version_tag=version_tag))

        buildtypes = ("nightlies",) # , "test-builds"
        info[version_major]['build'] = {}
        for buildtype in buildtypes:
            for bits in bitness:
                URL = "http://{host}/{buildtype}/{Platform}/{bits}/".format(host=host, buildtype=buildtype, Platform=Platform, bits=bits)
                Links = GetLinkList(URL)
                for _, _, bits, URL in GetKodiEXEList(Links, 'master'):
                    info[version_major]['build'][bits] = {'URL': URL}

        for ver in info:
            for plugin in ('xbmc.python', 'xbmc.gui', 'xbmc.metadata'):
                URL = repository + "raw/{0}/".format(info[ver]['codename']) + 'addons/{plugin}/addon.xml'.format(plugin=plugin)
                try:
                    response = network.DownloadURL(URL)
                except Exception:
                    raise
                else:
                    soup = BeautifulSoup(response, 'html.parser')
                    #info[ver][plugin.partition('.')[2]] = semantic_version.Spec(">={0}".format(soup.addon.find('backwards-compatibility')['abi']), "<={0}".format(soup.addon['version']))
                    info[ver][plugin.partition('.')[2]] = semantic_version.SimpleSpec(">={0},<={1}".format(soup.addon.find('backwards-compatibility')['abi'], soup.addon['version']))

        for ver in info:
            URL = repository + "raw/{0}/".format(info[ver]['codename']) + 'version.txt'
            try:
                response = network.DownloadURL(URL)
            except Exception:
                raise
            else:
                for line in response.splitlines():
                    #if line.startswith(b'APP_NAME'):
                    #    name = line.partition(b' ')[2].decode('ascii')
                    #if line.startswith(b'ADDON_API'):
                    #    version = line.partition(b' ')[2].decode('ascii')
                    if line.startswith('APP_NAME'):
                        name = line.partition(' ')[2]
                    if line.startswith('ADDON_API'):
                        version = line.partition(' ')[2]
                info[ver]['name'] = name

                plugin = 'xbmc.addon'
                URL = repository + "raw/{0}/".format(info[ver]['codename']) + 'addons/{0}/addon.xml.in'.format(plugin)
                try:
                    response = network.DownloadURL(URL)
                except Exception:
                    raise
                else:
                    soup = BeautifulSoup(response, 'html.parser')
                    backwards = soup.addon.find('backwards-compatibility')['abi']

                try:
                    #version = semantic_version.Version(version, partial=True)
                    version = semantic_version.Version.coerce(version)
                except ValueError:
                    from distutils.version import LooseVersion, StrictVersion
                    #version = semantic_version.Version(str(StrictVersion(version)), partial=True)
                    #version = semantic_version.Version(str(StrictVersion(version)))
                    version = semantic_version.Version.coerce(version)
                    #Version.coerce('0.1')
                #info[ver]['addon'] = semantic_version.Spec(">={backwards}".format(backwards=backwards), "<={0}".format(version))
                #info[ver]['addon'] = semantic_version.SimpleSpec(">={backwards}".format(backwards=backwards), "<={0}".format(version))
                #info[ver]['addon'] = semantic_version.Spec(">={backwards},<={version}".format(backwards=backwards, version=version))
                info[ver]['addon'] = semantic_version.SimpleSpec(">={backwards},<={version}".format(backwards=backwards, version=version))

        codename_map = {v['codename'].lower(): k for k, v in info.items()}
        KodiInfo.info = info
        KodiInfo.codename_map = codename_map
    if Ver:
        try:
            return info[Ver]
        except KeyError:
            return info[codename_map[Ver.lower()]]

    return info