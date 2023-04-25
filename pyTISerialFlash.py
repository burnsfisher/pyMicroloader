# /* Copyright (C) 2022 Heimir Thor Sverrisson
#  *
#  */

#
# This module is used with the AMSAT pyMicroloader module to access the Texas
# Instruments serial port flash loader. This flash loader uses the ymodem
# protocol with 1k packets and CRC on the wire
#

import platform
import sys
from tkinter import Y
import traceback
import serial
import serial.tools.list_ports
import re
from pyYmodem import YmodemMCU
import logging

class FlashLdr:
    "Texas Instruments host loader"
    #
    # All host loader classes have the same public methods
    #

    def __init__(self, device=None, debug=False):
        self.dev = ""
        self.found_flash_loader = False
        self.flash_loader_version = None
        self.flash_start = None
        self.flash_end = None
        self.low_address_as_int = None
        self.high_address_as_int = None
        self.download_application_command = [ord('1')]
        self.execute_application_command = [ord('3')]
        self.flash_loader_version_command = [ord('4')]
        self.device_version_command = [ord('5')]
        self.gotDevice = False
        if(device == None):
            if platform.system() == 'Windows':
                baseDevice = 'COM'
            else:
                baseDevice = '/dev/ttyUSB'
        else:
            baseDevice = device

        portInfos = serial.tools.list_ports.grep(baseDevice)
        for pi in portInfos:
            # This for is iterating over the available serial devices
            try:
                # Ok, we'll try to open the device names that we found
                # only stop if we get something or run out of devices.
                # If the creation fails, or if it works, but it does not
                # look like a flash loader, SerialException is raised
                # and we try again

                devName = pi.device
                logging.info(f"Trying {devName}")
                self.port = serial.Serial(devName, timeout=1, write_timeout=1, baudrate=115200)
                self.gotDevice = True

                while True:
                    if self._check_for_flash_loader(debug):
                        self._get_device_information(debug)
                        self.low_address_as_int = int(self.flash_start, 16)
                        self.high_address_as_int = int(self.flash_end, 16) - 1
                        logging.info(
                            f"Flash loader version: {self.flash_loader_version}")
                        break
                    if not self.found_flash_loader:
                        self.gotDevice = False
                        raise serial.SerialException

            except serial.SerialException as e:
                logging.error(f"Serial Exception: {e}")
            except:
                traceback.print_exc()
            if(self.found_flash_loader):
                break
        if(not self.gotDevice):
            raise ValueError(f"No loader responding in {baseDevice} ports")
        else:
            self.dev = devName

    def _check_for_flash_loader(self, debug):
        """
        Issue the flash loader version command and expect a string like:
           'Flash Loader TI: 1.0.0'
        Set the 'found_flash_loader' flag and the 'flash_loader_version string
        based on the response.
        """
        self.port.write(self.flash_loader_version_command)
        self.port.flush()
        self.port.readline()    # Response starts with a new line
        response = self.port.readline()
        if(len(response) == 0):
            return False
        flash_loader_string = (response.decode("utf-8")).strip()
        if re.match('^Flash Loader TI:', flash_loader_string):
            self.found_flash_loader = True
            m = re.search('([0-9.]+$)', flash_loader_string)
            self.flash_loader_version = m.group(1)
            if debug:
                logging.info(
                    f"Flash loader found!")
            return True

    def _get_device_information(self, debug):
        """
        Issue the device version command and pluck the values
        of 'FLASH START:' and 'FLASH END:' from the response
        """
        self.port.reset_input_buffer()
        self.port.write(self.device_version_command)
        self.port.flush()
        while True:
            response = self.port.readline()
            if(len(response) == 0 or self.flash_end):
                if debug:
                    logging.info(f"Flash 0x{self.flash_start} - 0x{self.flash_end}")
                return
            dev_info_string = (response.decode("utf-8")).strip()
            if re.match('^FLASH START:', dev_info_string):
                m = re.search('([0-9A-F]+$)', dev_info_string)
                self.flash_start = m.group(1)
            if re.match('^FLASH END:', dev_info_string):
                m = re.search('([0-9A-F]+$)', dev_info_string)
                self.flash_end = m.group(1)

    def GetDevice(self):
        "Get the OS name of the device that communicates with the loader"
        return self.dev

    def GetLowAddr(self):
        "Get the low address that the loader has told us its embedded device has"
        return self.low_address_as_int

    def GetHighAddr(self):
        "Get the high address that the loader has told us its embedded device has"
        return self.high_address_as_int

    def GetPageSize(self):
        "Get the page size of this device"
        return 0x100  # If we could get it from the loader, we should

    def ReadPage(self, address, size):
        assert False, "Not used by TI MCUs"

    def WritePage(self, outBuf, address):
        assert False, "Not used by TI MCUs"

    def StartExecution(self):
        """
        Issue the execute command
        """
        self.port.reset_input_buffer()
        self.port.write(self.execute_application_command)
        self.port.flush()

    def download_application(self, filename):
        """
        Download the binary (not elf) file to the MCU
        """
        self.port.reset_input_buffer()
        self.port.write(self.download_application_command)
        self.port.flush()
        ymodem = YmodemMCU(self.port)
        ymodem.send(filename)
        logging.info('')


def main():
    loader = FlashLdr(debug=True)


if __name__ == '__main__':
    main()
