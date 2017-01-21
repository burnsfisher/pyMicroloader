# /* Copyright (C) 2017 Burns Fisher
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
import sys
import traceback
import serial

class MemoryPage(object):
    'A representation of a page of memory in the microprocessor'
    size=0x100 #Default assumption
    loaded = False

    def __init__(self,address,loader):
        self.lowAddress = address & ~(self.size-1)
        self.highAddress=self.lowAddress+self.size-1;
        self.loaded = False
        self.dirty = False
        self.loader = loader
        self.size = loader.GetPageSize()

    def TestPage(self):
        # If we have never written, don't bother.  Plus there might be no
        # contents.
        if(not self.dirty):
            return
        tempContents = self.loader.ReadPage(self.lowAddress,self.size)
        for i in range(0,self.size):
            if(tempContents[i] != self.contents[i]):
                print("Compare fail for address="+hex(self.lowAddress+i)+': Device='+
                      str(tempContents[i])+ ' File='+str(self.contents[i]))
                      
    def LoadPage(self):
        self.contents = self.loader.ReadPage(self.lowAddress,self.size)
        self.loaded = True
        self.dirty = False
        
    def WritePage(self,force=False):
        if(force or self.dirty):
            self.loader.WritePage(self.contents,self.lowAddress)
            self.dirty=False

    def GetSize(self):
        return self.size

    def PutByte(self,data,address):
        if(address<self.lowAddress or address>self.highAddress):
            raise ValueError('Address out of range of object:'+
                             hex(self.lowAddress)+' '+hex(self.highAddress))
        if(not self.loaded):
            self.LoadPage()
        offset = address-self.lowAddress
        self.contents[offset] = data
        self.dirty=True
        return
    
    def GetByte(self,address):
        if(address<self.lowAddress or address>self.highAddress):
            raise ValueError('Address out of range of object:'+
                             hex(self.lowAddress)+' '+hex(self.highAddress))
        if(not self.loaded):
            self.LoadPage()
            
        offset = address-self.lowAddress
        return self.contents[offset]

    def GetByteArray(self,address,length):
        if(not self.loaded):
            raise ValueError('Page not loaded')

        if(address<self.lowAddress or (address+length-1)>self.highAddress):
            raise ValueError('Address out of range of object:'+str(self.lowAddress)+' '+str(self.highAddress))
        offset = address-self.lowAddress
        return self.contents[offset:offset+length-1]
    def GetRange(self):
        return ([self.lowAddress],[self.highAddress])

class Device(object):
    'A representation of the entire microprocessor--mainely the memory'
    
    def __init__(self,low,high,loader):
        self.loader = loader
        self.pageSize = MemoryPage.size
        self.lowAddress = low
        self.highAddress = high
        self.highIndex = int(high/self.pageSize)
        self.lowIndex = int(low/self.pageSize)
        self.memory = [MemoryPage(i,loader) for i in
                       range(low,high,self.pageSize)]
    def _GetPageIndex(self,address):
        return (int(address/self.pageSize))-self.lowIndex
    
    def GetByte(self,address):
        return self.memory[self._GetPageIndex(address)].GetByte(address)

    def PutByte(self,data,address):
        pageNum = int(address/self.pageSize)
        offset = pageNum - self.lowIndex
        self.memory[self._GetPageIndex(address)].PutByte(data,address)
        return
    def PutInt16(self,data,address):
        self.PutByte(data&0xff,address)
        self.PutByte((data>>8)&0xff,address+1)
        
    def GetInt16(self,address):
        lowVal=self.GetByte(address)
        highVal=self.GetByte(address+1)
        return (highVal<<8)|lowVal

    def GetInt32(self,address):
        lowVal=self.GetInt16(address)
        highVal=self.GetInt16(address+2)
        return (highVal<<16)|lowVal

    def MemoryFlush(self):
        maxIndex = int((self.highAddress - self.lowAddress)/self.pageSize)
        for i in range(0,maxIndex):
            self.memory[i].WritePage(False) #Write, but only if it is dirty
        return
    def MemoryLoad(self):
        maxIndex = int((self.highAddress - self.lowAddress)/self.pageSize)
        for i in range(0,maxIndex):
            self.memory[i].LoadPage()
    def MemoryCompare(self):
        maxIndex = int((self.highAddress - self.lowAddress)/self.pageSize)
        for i in range(0,maxIndex):
            self.memory[i].TestPage()
        

class AltosFlash:
    "A representation of the Altos Flash Loader"
    #
    # Note:  You should be able to make different classes to represent different
    # loaders with the same methods, and get this whole thing to work
    #
    def __init__(self,debug):
        #First, for the Altos device on Linux, it will be one of these
        possibleDevices = ['ttyACM0','ttyACM1','ttyACM2']
        self.IsAltosFlash=False
        output = bytearray([118])
        self.gotDevice=False
        for self.dev in possibleDevices:
            try:
                # Ok, we'll try to open the device names one by one and
                # only stop if we get something or run out of devices
                # If the creation fails, gets caught by SerialException below
                # and we try again
                self.port=serial.Serial('/dev/'+self.dev,timeout=1)
                gotDevice=True
                self.port.flush()
                self.port.write(output)
                while True:
                    # Ok, we have a device.  Read the prolog info from it
                    # and parse to confirm that it is an AltosFlash and get
                    # the memory range.
                    string = self.port.readline()                   
                    if(len(string)==0):
                        sys.stdout.flush()
                        assert self.IsAltosFlash
                        break
                    stringFields = string.split()
                    if 'flash-range' in stringFields[0]:
                        self.devLowAddr=int(stringFields[1],16)
                        self.devHighAddr = int(stringFields[2],16)-1
                    if 'product' in stringFields[0] and 'AltosFlash' in stringFields[1]:
                        self.IsAltosFlash=True
                    if(debug):
                        sys.stdout.write(string)
            except serial.SerialException:
                pass
            except:
                traceback.print_exc()
        if(not gotDevice):
            raise ValueError('No ttyACMx port found')
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
        self.port.write(command)
        contents = bytearray(size)   
        self.port.readinto(contents)
        return contents

    def WritePage(self,outBuf,address):
        sys.stdout.write('. ')
        sys.stdout.flush()
        self.port.flushInput()
        self.port.flushOutput()
        command = 'W '+ hex(address)[2:]+'\n' #Don't want the 0x in front
        self.port.write(command)
        self.port.write(outBuf)
        return
    def StartExecution(self):
        self.port.flushInput()
        self.port.flushOutput()
        self.port.write('a')
        return

    
if __name__ == '__main__':

    loader = AltosFlash(True)
    print(loader.GetDevice())
    ihu = Device(loader.GetLowAddr(),loader.GetHighAddr(),loader)
    data = ihu.GetByte(0x8001104)
    print('IHU Serial number='+str(data))
    ihu.PutByte(7,0x8001104)
    data = ihu.GetInt32(0x8001104)
    print('Modified Serial Number='+str(data))
    #ihu.MemoryFlush()
    exit()
