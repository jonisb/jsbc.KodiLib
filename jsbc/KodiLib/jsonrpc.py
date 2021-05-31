# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals, division, absolute_import

import socket
from threading import Thread, Event, Lock
from jsbc.compat.python3 import *
try:
    from queue import Queue, Empty
except ModuleNotFoundError:
    from Queue import Queue, Empty
import json
import logging
logger = logging.getLogger(__name__)
from jsbc.Toolbox import SettingsClass, DefaultSettings, settings
try:
    import regex
except ImportError:
    import re as regex

settingsDefaults = [
    ('client', [
        ('network', [
            ('jsonrpc', [
                ('enabled', False),
                ('buffersize', 4096),
                ('timeout', 1),
                ('retrys', 10),
                ('notifications', [
                    ('enabled', False),
                ]),
            ]),
        ]),
    ]),
    ('server', [
        ('network', [
            ('tcp', [
                ('port', 9090)
            ]),
        ]),
    ]),
]


class jsonrpc(object):
    def __init__(self, settings=settings, callback=None):
        logger.debug('jsonrpc init')
        self.settings = settings
        self.callback = callback
        self._NotificationsThread = None
        self._stopNotifications = Event()
        self._ReturnQueue = Queue()
        self._jsonrpc = '2.0'
        self._idLock = Lock()
        self._id = 0
        self._SendLock = Lock()
        logger.debug('jsonrpc init done')

    def connect(self):
        logger.debug('jsonrpc connecting')
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.settimeout(self.settings['client']['network']['jsonrpc']['timeout'])
        for retry in range(self.settings['client']['network']['jsonrpc']['retrys']):
            try:
                self._socket.connect((self.settings['server']['network']['ip'], self.settings['server']['network']['tcp']['port']))
            except (socket.timeout, ConnectionRefusedError, OSError, Exception):
                logger.exception('connect: %s, %s', self.settings['server']['network']['ip'], self.settings['server']['network']['tcp']['port'])
                continue
            break
        else:
            raise ConnectionError
        self._NotificationsThread = Thread(target=self.listen, args=(self._stopNotifications,))
        self._NotificationsThread.start()
        logger.debug('jsonrpc connected')

    def send(self, method='JSONRPC.Introspect', params=[], responce=True):
        try:
            message = {'jsonrpc': self._jsonrpc, 'method': method, 'params': params}
            if responce:
                with self._idLock:
                    self._id += 1
                    id = self._id
                message['id'] = id
            message = json.dumps(message)
            try:
                message = message.encode('utf-8')
            except AttributeError:
                pass
            logger.debug('jsonrpc.send: sending message')
            with self._SendLock:
                self._socket.send(message)
            message = None
            if responce:
                #while True:
                logger.debug('jsonrpc.send: pre while.')
                while not self._stopNotifications.isSet():
                    try:
                        #message = self._ReturnQueue.get(True, self.settings['client']['network']['jsonrpc']['timeout'])
                        message = self._ReturnQueue.get(True, 30)
                        logger.debug('jsonrpc.send: recived message')
                        if id == message['id']:
                            break
                        else:
                            logger.debug('jsonrpc.send: quing message')
                            self._ReturnQueue.put_nowait(message)
                    except Empty:
                        logger.warning('jsonrpc.send: empty.')
                        #continue
                        break
                    finally:
                        if message:
                            self._ReturnQueue.task_done()
                logger.debug('jsonrpc.send: post while.')
                return message
        except Exception:
            logger.exception('jsonrpc.send: send.')
            raise

    def listen(self, stopNotifications):
        message = ''
        while not stopNotifications.isSet():
            try:
                logger.debug('jsonrpc listen recv.')
                message += self._socket.recv(self.settings['client']['network']['jsonrpc']['buffersize']).decode('utf-8')
                logger.debug('jsonrpc listen recv done.')
                if not message:
                    break
                try:
                    Messages = [json.loads(message)]
                    #self.AvgMsgSize + len(message)
                    message = ''
                    #print(int(self.AvgMsgSize))
                except ValueError:
                    Messages, message = JSONSplit(message)
                for Message in Messages[:]:
                    if 'id' in Message:
                        self._ReturnQueue.put_nowait(Message)
                        Messages.remove(Message)
            except socket.timeout:
                logger.exception('jsonrpc.listen: timeout')
                continue
            except KeyboardInterrupt:
                break
            except:
                #import traceback
                #traceback.print_exc()
                logger.exception('jsonrpc.listen')
                break
            else:
                for Message in Messages:
                    if self.callback:
                        self.callback(Message)
                    #else:
                        #print(Message)

    def disconnect(self):
        logger.debug('jsonrpc disconnecting')
        self._stopNotifications.set()
        self._ReturnQueue.join()
        try:
            self._NotificationsThread.join()
        except AttributeError:
            pass
        self._socket.close()
        logger.debug('jsonrpc disconnected')

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.disconnect()


def JSONSplit(data):
    parts = []
    rest = ''
    match = regex.search(r"(?:(.*?})[\s\n]*(?={))*(.*)", data, regex.S)
    for part in match.captures(1):
        try:
            parts.append(json.loads(part))
        except ValueError:
            raise
    if match.group(2):
        try:
            parts.append(json.loads(match.group(2)))
        except ValueError:
            rest = match.group(2)
    return parts, rest




DefaultSettings(settingsDefaults)
