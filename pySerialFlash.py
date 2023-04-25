# /* Copyright (C) 2017,2018,2019 Burns Fisher
#  *
#  * This program is free software; you can redistribute it and/or modify
#  * it under the terms of the GNU General Public License as published by
#  * the Free Software Foundation; either version 2 of the License, or
#  * (at your option) any later version.
#  *
#  * This program is distributed in the hope that it will be useful,
#  * but WITHOUT ANY WARRANTY; without even the implied warranty of
#  * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  * GNU General Public License for more details.
#  *
#  * You should have received a copy of the GNU General Public License along
#  * with this program; if not, write to the Free Software Foundation, Inc.,
#  * 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#  *
#  */

#
# This module is used with the AMSAT pyMicroloader module to access the AMSAT
# serial port flash loader.  There is another module called pyAltosFlash
# which can be used to access the Altus Metrum loader.  Other modules could be
# written to use, say, the ST-Link dongle or even the STM32L built-in USB or
# serial loader.
#

import os
import platform
import sys
import traceback
import serial
import serial.tools.list_ports
import time
import logging


class FlashLdr:
    "A representation of the AMSAT Golf UART Loader"
    #
    # Note:  You should be able to make different classes to represent different
    # loaders with the same methods, and get this whole thing to work
    #
    def __init__(self,device=None,debug=False):
        #First, for the Altos device on Linux, it will be one of these
        self.dev = ""
        self.IsSerialFlash=False
        output = bytearray([118]) # This is a bytearray of 1 with the letter 'v'
        self.gotDevice=False
        if(device==None):
            if platform.system() == 'Windows':
                baseDevice='COM'
            else:
                baseDevice='/dev/ttyUSB'
        else:
            baseDevice=device
            possibleUnits=['']


        #
        # It's not 100% clear if this works with Windows, although
        # it should.  We might use the non-Grep version but in Linux
        # we might have a zillion devices to iterate through.

        portInfos = serial.tools.list_ports.grep(baseDevice)
        for pi in portInfos:
            # This for is interating through the available serial devices
            try:
                # Ok, we'll try to open the device names that we found
                # only stop if we get something or run out of devices.
                # If the creation fails, or if it works, but it does not
                # look like an Altos loader, SerialException is raised
                # and we try again

                devName = pi[0]
                logging.info("Trying "+devName)
                self.port=serial.Serial(devName,timeout=1,baudrate=57600)
                self.gotDevice=True
                self.port.flush()
                self.port.write(output)

                while True:
                    # Ok, we have a device.  Read the prolog info from it
                    # and parse to confirm that it is an AltosFlash and get
                    # the memory range.
                    #
                    # This while is iterating through the lines that returned
                    # in response to writing 'v' above.

                    string = self.port.readline()
                    if((len(string)==0)):
                        # We have read all there is.  We should have found it.
                        break
                    logging.info(string)
                    stringFields = string.split()
                    if(len(stringFields)<2):
                        break
                    if 'flash-range' in stringFields[0]:
                        self.devLowAddr=int(stringFields[1],16)
                        self.devHighAddr = int(stringFields[2],16)-1

                    if('GolfSerialLoader' in stringFields[1]):
                       self.IsSerialFlash=True
                       logging.info("Is serial flash")
                    if('Version' in stringFields[0]):
                        #Ok, that's the last line
                        logging.info("Flash loader version " + stringFields[1])
                        break
                    if(debug):
                        sys.stdout.write(string)
                sys.stdout.flush()
                if(debug):
                    logging.info("No more input")
                if(not self.IsSerialFlash):
                    self.gotDevice=False
                    raise serial.SerialException

            except serial.SerialException:
                pass
            except:
                traceback.print_exc()
            if(self.IsSerialFlash):
                break;
        if(not self.gotDevice):
            raise ValueError('No loader responding in '+baseDevice+' ports')
        else:
            self.dev = devName
    def GetDevice(self):
        "Get the OS name of the device that communicates with the loader"
        return self.dev

    def GetLowAddr(self):
        "Get the low address that the loader has told us its embedded device has"
        return self.devLowAddr

    def GetHighAddr(self):
        "Get the high address that the loader has told us its embedded device has"
        return self.devHighAddr

    def GetPageSize(self):
        "Get the page size of this device"
        return 0x100 # If we could get it from the loader, we should

    def ReadPage(self,address,size):
	#logging.info("Reading page "+hex(address)+" of size "+hex(size))
        sys.stdout.flush()
        #self.port.flushInput()
        self.port.flushOutput()
        command = 'R '+ hex(address)[2:]+'\n' #Don't want the 0x in front
        #logging.info(command)
        #self.port.write(command)
        self.__WaitAndSendCommand(command)
        contents = bytearray(size)
        self.port.readinto(contents) #Read one page of bytes
        readChecksum = 0
        for i in range(0,4):
            value = ord(self.port.read(1))
            readChecksum = readChecksum | (value << (i*8))
        calcChecksum = 0
        for i in range(0,64):
            for j in range(0,4):
                byte = contents[j+(i*4)]
                calcChecksum = (calcChecksum + (byte<<(j*8))) & 0xffffffff
        #logging.info("CalcCheck:"+hex(calcChecksum)+" Read:"+hex(readChecksum))
        if(calcChecksum == readChecksum):
            sys.stdout.write('-')
        else:
            logging.info(hex(calcChecksum)+" "+hex(readChecksum))
            sys.stdout.write('X')
        return contents

    def WritePage(self,outBuf,address):
        sys.stdout.flush()
        self.port.flushOutput()
        command = 'W '+ hex(address)[2:]+'\n' #Don't want the 0x in front
        self.__WaitAndSendCommand(command)
        bytes = bytearray(4)
        calcChecksum = 0
        for i in range(0,64):
            for j in range(0,4):
                #Speed it up a bit by sending 4 bytes at a time
                byte = outBuf[j+(i*4)]
                bytes[j] = byte
                calcChecksum = calcChecksum + (byte<<(j*8))
            self.__WaitAndSendByte(bytes)

        for i in range (0,4):
            bytes[i] = (calcChecksum>>(i*8))&0xff
        self.__WaitAndSendByte(bytes)
        self.port.flushOutput()
        sys.stdout.write('.')
        return
    def StartExecution(self):
        #self.port.flushInput()
        self.port.flushOutput()
        self.port.write('a')
        return
    def __WaitAndSendCommand(self,command):
        #Waits for a prompt and then sends the command
        retval=' '
        while(retval != 'o'):
            retval = self.port.read(size=1) #Wait for \n
            #if(len(retval)>0):
                #sys.stdout.write('b')
                #sys.stdout.write(retval[0])
        self.port.flushInput()
        self.port.write(command)
	#logging.info(command)
        return
    def __WaitAndSendByte(self,byte):
        #Waits for a prompt and then sends the byte (which must
	#be a bytearray.  This can probably be the same as SendCommand

        retval=' '
        while(retval != '.'):
            retval = self.port.read(size=1) #Wait for \n
            #if(len(retval)>0):
                #sys.stdout.write('b')
                #sys.stdout.write(retval[0])
        self.port.flushInput()
        self.port.write(byte)
        return

if __name__ == '__main__':
    import pyMicromem as mem
    loader = FlashLdr(device="ttyUSB",debug=False)
    logging.info(loader.GetDevice())
    ihu = mem.Device(loader.GetLowAddr(),loader.GetHighAddr(),loader)
    for addr in range(0x8030000,0x8030100):
        data = ihu.GetByte(addr)
        logging.info(hex(addr)+":"+hex(data))
    logging.info("Writing now")
    for addr in range(0x8030000,0x8030100):
        ihu.PutByte(3,addr)
        #ihu.PutByte(ord('a')+(addr&0xf),addr)

    for addr in range(0x8030000,0x8030100):
        data = ihu.GetByte(addr)
        #logging.info(hex(addr)+":"+hex(data))

    #ihu.PutByte(11,0x8001104)
    #data = ihu.GetByte(0x8001104)
    #logging.info('Modified Serial Number='+str(data))
    ihu.MemoryFlush()
    sys.exit()
