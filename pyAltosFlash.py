# /* Copyright (C) 2017,2018,2019,2021 Burns Fisher
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
# This module is to access a microprocessor with built-in loader.  Currently
# we assume the loader is AltosFlash, the Altus Metrum loader.  It could be
# modified to use, say, the ST-Link dongle or even the STM32L built-in USB or
# serial loader.
#

import os
import platform
import sys
import traceback
import serial
import serial.tools.list_ports
import time


class FlashLdr:
    "A representation of the Altos Flash Loader"
    #
    # Note:  You should be able to make different classes to represent different
    # loaders with the same methods, and get this whole thing to work
    #
    def __init__(self,device=None,debug=False):
        #First, for the Altos device on Linux, it will be one of these
        self.IsAltosFlash=False
        output = bytearray([118]) # This is a bytearray of 1 with the letter 'v'
        self.gotDevice=False
        if(device==None):
            if platform.system() == 'Windows':
                baseDevice='COM'
            else:
                baseDevice='/dev/ttyACM'
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
                print(devName)
                self.port=serial.Serial(devName,timeout=1)
                self.gotDevice=True
                if(debug):
                    print("Checking device "+devName)
                self.port.flush()
                self.port.write(output)

                while True:
                    # Ok, we have a device.  Read the prolog info from it
                    # and parse to confirm that it is an AltosFlash and get
                    # the memory range.
                    #
                    # This while is iterating through the lines that returned
                    # in response to writing 'v' above.

                    string = self.port.readline().decode()
                    if(len(string)==0):
                        # We have read all there is.  We should have found it.
                        sys.stdout.flush()
                        print("No more input")
                        if(not self.IsAltosFlash):
                            self.gotDevice=False
                            raise serial.SerialException
                        break
                    stringFields = string.split()
                    if 'flash-range' in stringFields[0]:
                        self.devLowAddr=int(stringFields[1],16)
                        self.devHighAddr = int(stringFields[2],16)-1
                    if 'product' in stringFields[0] and 'AltosFlash' in stringFields[1]:
                        self.IsAltosFlash=True
                    if 'AltosFlash' in stringFields[0]:
                        self.IsAltosFlash=True
                    if(debug):
                        sys.stdout.write(string)
            except serial.SerialException:
                pass
            except:
                traceback.print_exc()
            if(self.IsAltosFlash):
                break;
        if(not self.gotDevice):
            raise ValueError('No loader responding in '+baseDevice+' ports')
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
        self.port.flushInput()
        self.port.flushOutput()
        command = 'R '+ hex(address)[2:]+'\n' #Don't want the 0x in front
        self.port.write(command.encode())
        contents = bytearray(size)   
        self.port.readinto(contents)
        return contents

    def WritePage(self,outBuf,address):
        sys.stdout.write('.')
        sys.stdout.flush()
        self.port.flushInput()
        self.port.flushOutput()
        command = 'W '+ hex(address)[2:]+'\n' #Don't want the 0x in front
        self.port.write(command.encode())
        self.port.write(outBuf)
        return
    def StartExecution(self):
        self.port.flushInput()
        self.port.flushOutput()
        self.port.write('a'.encode())
        return

    
if __name__ == '__main__':
 
    loader = AltosFlash(device="ttyUSB",debug=True)
    print(loader.GetDevice())
    ihu = Device(loader.GetLowAddr(),loader.GetHighAddr(),loader)
    data = ihu.GetByte(0x8001104)
    print('IHU Serial number='+str(data))
    ihu.PutByte(7,0x8001104)
    data = ihu.GetInt32(0x8001104)
    print('Modified Serial Number='+str(data))
    #ihu.MemoryFlush()
    exit()
