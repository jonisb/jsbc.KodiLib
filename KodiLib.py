# -*- coding: utf-8 -*-
"""
KodiLib:
"""
from __future__ import print_function, unicode_literals, division, absolute_import

import os
import ast
import urllib2
import xml.dom.minidom
import logging

import regex

from pythoncompat import OrderedDict
import network
from network import DownloadURL, DownloadPage
import eventserver

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
            ('eventclient', [
                ('enabled', True),
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
                ('udp', {
                    'port': 9777,
                }),
                ('http', {
                    'port': 8080,
                }),
                ('upnp', {
                    'id': '',
                }),
            ]),
        ]),
        ('commands', [
            ('actions', ''),
        ]),
    ], Data)

    URL = 'https://raw.githubusercontent.com/xbmc/xbmc/master/xbmc/input/ActionTranslator.cpp'
    Pattern = {
                        'Header': r"static const std::map<(?P<group>Action)Name, ActionID> ActionMappings =",
                        'Action': r'"(?P<action>.+)"(?:.*? // (?P<description>.*))?',
                        'End': "};",
                        'Category': r' // (?P<category>.+)'
                    }
    Settings['commands']['actions'] = "(('Code', {0}, {1}), ('HTML', 'http://kodi.wiki/view/Action_IDs', ['Action', 'Description']))".format(repr(URL), Pattern)

    return Settings


def XMLText(Node):
    """ """  # Todo
    text = ''
    try:
        for n in Node.childNodes:
            text += n.nodeValue+' ' if n.nodeName == '#text' else XMLText(n)
    except:
        print("Try:", Node.nodeValue, Node.nodeName)

    return text


class ActionBaseClass(OrderedDict):
    def __init__(self, Commands):
        super(ActionBaseClass, self).__init__()
        self['All'] = {}

        if isinstance(Commands[0], basestring):
            Commands = (Commands,)

        for Command in Commands:
            try:
                getattr(self, Command[0])(*Command[1:])
            except AttributeError:
                print("Command missing:", Command[0])
                logger.exception("")

            except Exception:
                print("Error:", Command[0])
                logger.exception("")

    def __call__(self, category='All'):
        return sorted(list(self[category][action]['action'] for action in self[category]), key=unicode.lower)

    def Code(self, URL, Pattern):
        Data = DownloadURL(URL)
        self.ParseActions(Pattern, Data)

    def ParseActions(self, Pattern, Data, Category=''):
        """ """  # Todo
        result = regex.search(Pattern['Header'], Data)
        try:
            Category = result.group("category")
        except IndexError: pass
        start = result.end()
        for line in Data[start:].splitlines(False):
            if Pattern['End'] == line:
                Category = ''
                break
            else:
                result = regex.search(Pattern['Action'], line)
                if result:
                    if Category not in self: self[Category] = {}
                    Action = result.groupdict()
                    if 'options' in Action:
                        Action['options'] = int(Action['options'])
                    Action['category'] = Category
                    for label in Action:
                        if not Action[label]:
                            Action[label] = ''
                    self[Category][Action['action'].lower()] = Action
                    self['All'][Action['action'].lower()] = Action

                else:
                    result = regex.search(Pattern['Category'], line) # Todo
                    if result and result.group("category"):
                        Category = result.group("category")

    def HTML(self, URL, Headers):
        Data = DownloadURL(URL)
        Data = self.GetHTML(Data, Headers)

        for action in self['All']:
            try:
                self['All'][action]['action'] = Data[action]['action']
            except: pass
            try:
                if len(self['All'][action]['description']) < len(Data[action]['description']):
                    self['All'][action]['description'] = Data[action]['description']
            except: pass
            try:
                self['All'][action]['syntax'] = Data[action]['syntax']
            except: pass

    def GetHTML(self, Data, Headers):
        """ GetDocumentation ...

        Args:
            Data (string): Document to parse

        Returns:
            dict: Command list
        """  # Todo
        ActionDict = {}
        ActionList = self.GetTable(xml.dom.minidom.parseString(Data.encode('utf-8')), Headers) # Todo

        for Action in ActionList:
            result = regex.search(r'(?P<action>[^<>]+)\s*<(?P<first>\d)-(?P<last>\d)>', Action[Headers[0]]) # Todo
            if result:
                actions = [result.group('action').strip() + str(i) for i in range(int(result.group('first')), int(result.group('last')) + 1)] # Todo
            else:
                actions = [Action[Headers[0]]] # Todo
            for action in actions:
                for Syntax in action.split('\n'):
                    Syntax = Syntax.strip()
                    action = Syntax.split('(')[0]
                    Description = Action[Headers[1]]
                    ActionDict[action.lower()] = {
                                            'action': action, 'syntax': Syntax, 'description': Description}

        return ActionDict

    def GetTable(self, XML, Headers):
        def ListTags(XML, Tag):
            """ """ # Todo
            Current = XML
            while Current:
                yield Current
                while True:
                    Current = Current.nextSibling
                    if Current == None or Current.nodeName == Tag:
                        break

        def TestTable(XML, Headers):
            try:
                th = ListTags(XML.getElementsByTagName("th")[0], "th")
            except IndexError:
                return False
            else:
                for header in Headers:
                    if XMLText(th.next()).strip() != header:
                        return False
                else:
                    return True

        def FindTable(XML, Headers):
            """ """ # Todo
            for Table in XML.getElementsByTagName("table"):
                for table in ListTags(Table, "table"):
                    if TestTable(table, Headers):
                        return table
                else:
                    continue
                break

        ActionList = []
        for table in ListTags(FindTable(XML, Headers), "table"):
            if TestTable(table, Headers):
                for tr in ListTags(table.getElementsByTagName("tr")[0], "tr"):
                    try:
                        td = list(ListTags(tr.getElementsByTagName("td")[0], "td"))
                    except IndexError: pass
                    else:
                        Dict = {}
                        for i, header in enumerate(Headers):
                            Dict[header] = XMLText(td[i]).strip()

                        ActionList.append(Dict)
        return ActionList


class kodi(object):
    def __init__(self, settings=DefaultSettings(), callback=None):  # TODO
        logger.debug('kodi init.')
        self.settings = settings
        global Settings
        Settings = settings
        network.init(settings)
        try:
            os.makedirs(settings['client']['cache path'], exist_ok=True)
        except TypeError:
            try:
                os.makedirs(settings['client']['cache path'])  # if "exist_ok" option is not supported
            except WindowsError:
                if not os.path.exists(settings['client']['cache path']):
                    raise
        if self.settings['client']['eventclient']['enabled']:
            self.eventclient = eventserver.eventclient(settings)

    def connect(self):
        try:
            self.eventclient.connect()
        except AttributeError:
            pass

    def GetCommands(self, Commands):
        return ActionBaseClass(ast.literal_eval(self.settings['commands'][Commands]))

    def disconnect(self):
        try:
            self.eventclient.close()
        except AttributeError:
            pass

    def close(self):
        self.disconnect()

    __del__ = close
