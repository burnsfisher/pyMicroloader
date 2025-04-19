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

class FlashLdr:
    "A representation of the AMSAT STM32 Serial Loader"

    def __init__(self, device=None, debug=False):
        self.dev = ""
        self.IsSerialFlash = False
        self.gotDevice = False
        self.output = bytearray([118])  # Bytearray with letter 'v'

        if device is None:
            device = self._find_device()

        self._initialize_device(device)

        if not self.gotDevice:
            raise ValueError(f'No loader responding in port {self.dev}')
        else:
            self.dev = device

    def _find_device(self):
        """Finds an appropriate serial device automatically."""
        baseDevice = 'COM' if platform.system() == 'Windows' else '/dev/ttyUSB'
        for pi in serial.tools.list_ports.grep(baseDevice):
            devName = pi[0]
            print(f"Trying {devName}")
            try:
                return devName if self._initialize_device(devName) else None
            except serial.SerialException:
                pass
            except:
                traceback.print_exc()
        return None

    def _initialize_device(self, device):
        """Attempts to open a device and check if it's the correct loader."""
        try:
            print(f"Checking {device}")
            if platform.system() == 'Windows':
                devName = device
            else: #For Linux it might be a link.  Get the real name.
                devName = os.readlink(device) if os.path.islink(device) else device
                print(f"DevName after symlink conversion={devName}")
            if "/dev" in device and not "/dev" in devName:
                devName = f"/dev/{devName}"
                print(f"Devname after adding dev is {devName}")
            self.port = serial.Serial(devName, timeout=2.0, baudrate=57600)
            self.gotDevice = True
            self.port.flush()
            self.port.write(self.output)

            while True:
                string = self.port.readline()
                if not string:
                    break
                print(string.decode().strip())
                stringFields = string.split()
                if len(stringFields) < 2:
                    break
                if b'flash-range' in stringFields[0]:
                    self.devLowAddr = int(stringFields[1], 16)
                    self.devHighAddr = int(stringFields[2], 16) - 1

                if (b'GolfSerialLoader' in stringFields[1]) or \
                        ((b'MSAT' in stringFields[0]) and (b'Serial' in stringFields[2])):
                    self.IsSerialFlash = True
                    print("\nWe found a port with a serial flash loader:\n")
                if b'Version' in stringFields[0]:
                    print("Flash loader version " + stringFields[1].decode())
                    break

            sys.stdout.flush()
            if not self.IsSerialFlash:
                self.gotDevice = False
                raise serial.SerialException
            return True

        except serial.SerialException:
            return False
        except:
            traceback.print_exc()
            return False


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
	#print("Reading page "+hex(address)+" of size "+hex(size))
        sys.stdout.flush()
        self.port.flushOutput()
        command = 'R '+ hex(address)[2:]+'\n' #Don't want the 0x in front
        #print(command)
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
        #print("CalcCheck:"+hex(calcChecksum)+" Read:"+hex(readChecksum))
        if(calcChecksum == readChecksum):
            sys.stdout.write('-')
        else:
            print(hex(calcChecksum)+" "+hex(readChecksum))
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
        self.port.write(b'a')
        return
    def __WaitAndSendCommand(self,command):
        #Waits for a prompt and then sends the command
        retval=b' '
        while(retval.decode() != 'o'):
            retval = self.port.read(size=1) #Wait for \n
        self.port.flushInput()
        self.port.write(command.encode())
	#print(command)
        return
    def __WaitAndSendByte(self,byte):
        #Waits for a prompt and then sends the byte (which must
	#be a bytearray.  This can probably be the same as SendCommand
	
        retval=b' '
        while(retval.decode() != '.'):
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
    print(loader.GetDevice())
    ihu = mem.Device(loader.GetLowAddr(),loader.GetHighAddr(),loader)
    for addr in range(0x8030000,0x8030100):
        data = ihu.GetByte(addr)
        print(hex(addr)+":"+hex(data))
    print("Writing now")
    for addr in range(0x8030000,0x8030100):
        ihu.PutByte(3,addr)
        #ihu.PutByte(ord('a')+(addr&0xf),addr)

    for addr in range(0x8030000,0x8030100):
        data = ihu.GetByte(addr)
        #print(hex(addr)+":"+hex(data))

    #ihu.PutByte(11,0x8001104)
    #data = ihu.GetByte(0x8001104)
    #print('Modified Serial Number='+str(data))
    ihu.MemoryFlush()
    sys.exit()
