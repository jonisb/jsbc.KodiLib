# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals, division, absolute_import

import logging
logger = logging.getLogger(__name__)

__version__ = '0.0.0'
__all__ = []

from socket import *
from struct import pack
from threading import Thread, Event
import time
from .network import *

KEY_VKEY  = 0xF000  # a virtual key/functional key e.g. cursor left
KEY_ASCII = 0xF100  # a printable character in the range of TRUE ASCII (from 0 to 127)

ES_FLAG_UNICODE = 0x80000000  # new 16bit key flag to support real unicode over EventServer

MAX_PACKET_SIZE  = 1024
HEADER_SIZE      = 32
MAX_PAYLOAD_SIZE = MAX_PACKET_SIZE - HEADER_SIZE
UNIQUE_IDENTIFICATION = (int)(time.time())

PT_HELO          = 0x01
PT_BYE           = 0x02
PT_BUTTON        = 0x03
#PT_MOUSE         = 0x04
PT_PING          = 0x05
#PT_BROADCAST     = 0x06
PT_NOTIFICATION  = 0x07
PT_BLOB          = 0x08
#PT_LOG           = 0x09
PT_ACTION        = 0x0A
#PT_DEBUG         = 0xFF

ICON_NONE = 0x00
ICON_JPEG = 0x01
ICON_PNG  = 0x02
ICON_GIF  = 0x03

BT_USE_NAME   =  0x01
BT_DOWN       =  0x02
BT_UP         =  0x04
BT_USE_AMOUNT =  0x08
BT_QUEUE      =  0x10
BT_NO_REPEAT  =  0x20
BT_VKEY       =  0x40
BT_AXIS       =  0x80
BT_AXISSINGLE = 0x100
BT_UNICODE    = 0x200

#MS_ABSOLUTE = 0x01

#LOGDEBUG   = 0x00
#LOGINFO    = 0x01
#LOGNOTICE  = 0x02
#LOGWARNING = 0x03
#LOGERROR   = 0x04
#LOGSEVERE  = 0x05
#LOGFATAL   = 0x06
#LOGNONE    = 0x07

ACTION_EXECBUILTIN = 0x01
ACTION_BUTTON      = 0x02


def get_icon_type(icon_file):
    if icon_file:
        if icon_file.lower()[-3:] == "png":
            return ICON_PNG
        elif icon_file.lower()[-3:] == "gif":
            return ICON_GIF
        elif icon_file.lower()[-3:] == "jpg":
            return ICON_JPEG
    return ICON_NONE


class eventclient(object):
    def __init__(self, settings, uid=UNIQUE_IDENTIFICATION):
        self.settings = settings

        self.name = settings['client']['name']
        self.ip = settings['server']['network']['ip']
        self.port = settings['server']['network']['udp']['port']
        self.addr = (self.ip, self.port)
        self.uid = uid
        self.socket = socket(AF_INET,SOCK_DGRAM)
        self._stopPing = Event()

    def connect(self):
        icon_file = DownloadURL(self.settings['client']['icon']['url'])
        icon_type = get_icon_type(self.settings['client']['icon']['type'])

        self.send(Packet_HELO(uid=self.uid, device_name=self.name, iconfile=icon_file, icontype=icon_type))
        self._PingThread = Thread(target=self.keepalive, args=(self._stopPing,))
        self._PingThread.daemon = True
        self._PingThread.start()
        logger.debug('eventclient: connect: thread started: %s', self._PingThread.name)

    def keepalive(self, stopPing):
        logger.debug('keepalive: started.')
        while not (stopPing.wait(60.0) or stopPing.isSet()):  #TODO: Time
            logger.debug('keepalive: gonna ping.')
            self.ping()
        logger.debug('keepalive: ending.')

    def send(self, data):
        for packet in data.getpacket():
            self.socket.sendto(packet, self.addr)

    def close(self):
        logger.debug('eventclient: close')
        self._stopPing.set()
        logger.debug('eventclient: close: after set')
        self._PingThread.join(10.0)  #TODO: Time
        if self._PingThread.isAlive():
            logger.debug('eventclient: close: alive after join: %s', self._PingThread.name)
        self.send(Packet_BYE(self.uid))
        logger.debug('eventclient: closed')

    def send_notification(self, title="", message="", icontype=ICON_NONE, iconfile=None):
        icon_file = iconfile or DownloadURL(self.settings['client']['icon']['url'])
        icon_type = icontype or get_icon_type(self.settings['client']['icon']['type'])
        self.send(Packet_NOTIFICATION(uid=self.uid, caption=title, message=message, iconfile=icon_file, icontype=icon_type))

    def send_button(self, map='', name='', code=0, amount=None, button_down=True, queue=False, repeat=True, virtual_key=False, axis=0):
        if isinstance(code, unicode) and len(code) > 0:
            for unichar in code:
                self.send(Packet_BUTTON(uid=self.uid, button_code=unichar, queue_event=True))
            else:
                self.send(Packet_BUTTON(uid=self.uid, button_code='\n'))
        else:
            self.send(Packet_BUTTON(uid=self.uid, device_map=map, button_name=name, button_code=code, button_down=button_down, queue_event=queue, amount=amount, repeat=repeat, virtual_key=virtual_key, axis=axis))

    def send_action(self, actionmessage):
        self.send(Packet_ACTION(uid=self.uid, message=actionmessage))

    def send_function(self, functionmessage):
        self.send(Packet_ACTION(uid=self.uid, message=functionmessage, action_type=ACTION_EXECBUILTIN))

    def ping(self):
        """Send a PING packet"""
        self.send(Packet_PING(uid=self.uid))


#class eventserver(object):
#    def send_button_state(self, map="", button="", down=0, repeat=1, amount=0, axis=0):
#        if axis:
#            if amount == 0:
#                down = 0
#            else:
#                down = 1
#
#        packet = xbmcclient.PacketBUTTON(map_name=map.encode('UTF-8'), button_name=button.encode('UTF-8'), repeat=repeat, amount=amount, down=down, queue=1, axis=axis)
#        return packet.send(self.sock, self.addr, self.uid)
#
#    def send_universal_remote_button(self, button=None):
#        if not button:
#            return
#        return self.send_button(map="R2".encode('UTF-8'), button=button.encode('UTF-8'))

class Packet(object):
    """Base class that implements a single event packet.

    - Generic packet structure (maximum 1024 bytes per packet)
    - Header is 32 bytes long, so 992 bytes available for payload
    - large payloads can be split into multiple packets using H4 and H5
    H5 should contain total no. of packets in such a case
    - H6 contains length of P1, which is limited to 992 bytes
    - if H5 is 0 or 1, then H4 will be ignored (single packet msg)
    - H7 must be set to zeros for now

        -----------------------------
        | -H1 Signature ("XBMC")    | - 4  x CHAR                4B
        | -H2 Version (eg. 2.0)     | - 2  x UNSIGNED CHAR       2B
        | -H3 PacketType            | - 1  x UNSIGNED SHORT      2B
        | -H4 Sequence number       | - 1  x UNSIGNED LONG       4B
        | -H5 No. of packets in msg | - 1  x UNSIGNED LONG       4B
        | -H6 Payload size          | - 1  x UNSIGNED SHORT      2B
        | -H7 Client's unique token | - 1  x UNSIGNED LONG       4B
        | -H8 Reserved              | - 10 x UNSIGNED CHAR      10B
        |---------------------------|
        | -P1 payload               | -
        -----------------------------
    """
    def __init__(self, uid):
        self.sigature = b"XBMC"
        self.version = (2, 0)
        #self.packet_type = PT_HELO
        self.sequence_number = 1
        self.sequence_max = 1
        #self.payload_size = 0
        self.unique_token = uid
        #self.reserved = b"\0" * 10
        #self.payload = b""

    def getheader(self):
        header = pack(b"!4s2BHLLHL10x", self.sigature, self.version[0], self.version[1], self.packet_type, self.sequence_number, self.sequence_max, self.payload_size, self.unique_token)
        return header

    def getpayload(self):
        self.payload_size = 0
        return b""

    def getpacket(self):
        payload = self.getpayload()
        self.sequence_max = -(-len(payload) // MAX_PAYLOAD_SIZE)
        if self.sequence_max > 1:
            self.payload_size = MAX_PAYLOAD_SIZE
        for i in range(self.sequence_max):
            self.sequence_number = i + 1
            if self.sequence_number == self.sequence_max:
                self.payload_size = len(payload) % MAX_PAYLOAD_SIZE
            yield self.getheader() + payload[i*MAX_PAYLOAD_SIZE:(i+1)*MAX_PAYLOAD_SIZE]
            self.packet_type = PT_BLOB


class Packet_HELO(Packet):
    """
        Payload format
        %s - device name (max 128 chars)
        %c - icontype ( 0=>NOICON, 1=>JPEG , 2=>PNG , 3=>GIF )
        %s - my port ( 0=>not listening )
        %d - reserved1 ( 0 )
        %d - reserved2 ( 0 )
        XX - imagedata ( can span multiple packets )
    """
    def __init__(self, uid, device_name="", icontype=ICON_NONE, iconfile=None):
        Packet.__init__(self, uid)
        self.packet_type = PT_HELO

        self.device_name = device_name
        self.icontype = icontype
        self.myport = 0
        if icontype != ICON_NONE and iconfile:
            self.imagedata = iconfile
        else:
            self.imagedata = b""

    def getpayload(self):
        device_name = (self.device_name + '\0').encode('UTF-8')[0:128]
        payload = pack(b"!{0}sBH4x4x{1}s".format(len(device_name), len(self.imagedata)), device_name, self.icontype, self.myport, self.imagedata)
        self.payload_size = len(payload)
        return payload

class Packet_NOTIFICATION(Packet):
    """
        Payload format
        %s - caption
        %s - message
        %c - icontype ( 0=>NOICON, 1=>JPEG , 2=>PNG , 3=>GIF )
        %d - reserved ( 0 )
        XX - imagedata ( can span multiple packets )
    """
    def __init__(self, uid, caption="", message="", icontype=ICON_NONE, iconfile=None):
        Packet.__init__(self, uid)
        self.packet_type = PT_NOTIFICATION

        self.caption = caption
        self.message = message
        self.icontype = icontype
        if icontype != ICON_NONE and iconfile:
            self.imagedata = iconfile
        else:
            self.imagedata = b""

    def getpayload(self):
        caption = self.caption.encode('UTF-8')
        message = self.message.encode('UTF-8')
        payload = pack(b"!{0}s{1}sB4x{2}s".format(len(caption)+1, len(message)+1, len(self.imagedata)), caption, message, self.icontype, self.imagedata)
        self.payload_size = len(payload)
        return payload

class Packet_ACTION(Packet):
    """
        Payload format
        %c - action type
        %s - action message
    """
    def __init__(self, uid, message, action_type=ACTION_BUTTON):
        Packet.__init__(self, uid)
        self.packet_type = PT_ACTION

        self.action_type = action_type
        self.message = message

    def getpayload(self):
        message = self.message.encode('UTF-8')
        payload = pack(b"!B{0}s".format(len(message)+1), self.action_type, message)
        self.payload_size = len(payload)
        return payload

class Packet_BUTTON(Packet):
    """
        Payload format
        %i - button code
        %i - flags  0x01 => use button map/name instead of code
                    0x02 => btn down
                    0x04 => btn up
                    0x08 => use amount
                    0x10 => queue event
                    0x20 => do not repeat
                    0x40 => virtual key
                    0x80 => axis key
        %i - amount ( 0 => 65k maps to -1 => 1 )
        %s - device map (case sensitive and required if flags & 0x01)
            "KB" - Standard keyboard map
            "XG" - Xbox Gamepad
            "R1" - Xbox Remote
            "R2" - Xbox Universal Remote
            "LI:devicename" - valid LIRC device map where 'devicename'
                            is the actual name of the LIRC device
            "JS<num>:joyname" - valid Joystick device map where
                                'joyname' is the name specified in
                                the keymap. JS only supports button code
                                and not button name currently (!0x01).
        %s - button name (required if flags & 0x01)
    """
    def __init__(self, uid, button_code=0, amount=None, device_map='', button_name='', button_down=True, queue_event=False, repeat=False, virtual_key=False, axis=0):
        Packet.__init__(self, uid)
        self.packet_type = PT_BUTTON

        flags = 0x00
        if device_map and button_name:
            flags |= BT_USE_NAME
            #print("BT_USE_NAME")
        else:
            if isinstance(button_code, unicode):
                flags |= BT_UNICODE
                #print(repr(button_code))
                #print(ord(button_code))
                #print(chr(button_code))
                button_code = ord(button_code)
                #print("BT_UNICODE")
            #print("BT_USE_CODE")
        if button_down:
            flags |= BT_DOWN
            #print("BT_DOWN")
        else:
            flags |= BT_UP
            #print("BT_UP")
        if amount is not None:
            flags |= BT_USE_AMOUNT
        else:
            amount = 0
        if queue_event:
            flags |= BT_QUEUE
            #print("BT_QUEUE")
        if not repeat:
            flags |= BT_NO_REPEAT
            #print("BT_NO_REPEAT")
        if axis == 1:
            flags |= BT_AXISSINGLE
        elif axis > 1:
            flags |= BT_AXIS
        if virtual_key:
            flags |= BT_VKEY

        self.button_code = button_code
        self.flags = flags
        self.amount = amount
        self.device_map = device_map
        self.button_name = button_name

    def getpayload(self):
        device_map = self.device_map.encode('UTF-8')
        button_name = self.button_name.encode('UTF-8')
        payload = pack(b"!HHH{0}s{1}s".format(len(device_map)+1, len(button_name)+1), self.button_code, self.flags, self.amount, device_map, button_name)
        self.payload_size = len(payload)
        return payload

class Packet_BYE(Packet):
    """
        no payload
    """
    def __init__(self, uid):
        Packet.__init__(self, uid)
        self.packet_type = PT_BYE

class Packet_PING(Packet):
    """
        no payload
    """
    def __init__(self, uid):
        Packet.__init__(self, uid)
        self.packet_type = PT_PING
