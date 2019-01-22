# pyMicroloader
A program loader for embedded microprocessors

V1.1, June 3, 2018: Search for serial devices rather than just taking the first one.
V1.2, Jan 22, 2019: Change design of pyMicroMem slightly to allow multiple loader types

The intent of this loader it for use with a cross-development
environment for embedded microprocessors.  This loader is
intended to run in the development environment (or similar);
I developed it on Linux (Ubuntu 14) but also tested it on
Windows 7, at least a while ago.

This program expects a bootloader of some sort to run in
the microprocessor.  It currently has a class that corresponds
to the AltusMetrum boot loader and a separate class that corresponds
to the AMSAT Golf-T loader.  A class could be written to use
(for example) the ST-Link dongle or a built-in ROM loader in a
processor. NOTE: For Windows 7, it needs a driver (well really 
an INF file) from Altus Metrum to recognize the loader device when
it is plugged into the USB port.

Similarly, there is class to represent an ELF file.  A 
similar class could be written to represent, say, an iHex file.


Usage:

  python pyMicroloader filename.elf [--serial n [--force]]
   --serial n specifies the serial number of the device. It must be
     specified if the device has not been flashed.  It it is specified
     and it does not match the flashed device S/N, it will not be
     accepted unless you use:
   --force Ignore the serial number currently flashed and use a newly
     specified one.
   --wait  If the boot loader is not available for some reason keep
     retrying
   --usb  Assume the Altus Metrum usb-based boot loader (default)
   --uart Assume the AMSAT Golf serial UART loader

Dependencies:
	It depends on the 'pyserial' and 'pyelftools' packages

Packages and Classes created (which pyMicroloader.py depends on):
	pyMicromem.py contains classes as follows:
		MemoryPage, which represents a page in the microprocessor
		Device, which represents all of memory in a microprocessor
   
		AltosFlash, which represents the boot loader within the
			device.
	pyAltosFlash and pySerial flash both contain the class
        FlashLdr, which represents the loader to be used
        	
	pySimpleElf
	        This package contains the class SimpleElf, which is
		really a simple wrapper around the pyelftools class ELFFile


Installation:
	(Seems to work for both Ubuntu Linux and Windows 7)
		1) Install Python2.7 from python.org if it is not already
                   on your system. Choose the latest update (there will
		           likely be no more of 2.7). You also have to pay attention
                   to the OS version that you are using in order to choose
                   the right Python.  (pyMicroloader may work on Python 3.  Not tested)
		2) Download and unzip pyserial from github and pip install pyserial
		3) Download and unzip elftools from github and pip install pyelftools.
		4) Download and unzip pyMicroloader (no install necessary)


TODO:

o Generally fix errors to work more cleanly.  In particular:
    -Fix try/except to better deal with cases when files are not found
    -Deal with cases where the elf file contains more data than the processor
     has memory

o There may be elf sections and segments that I have not dealt with, but which are
  required by some uProcs

o The AltosLoader class can take an explicit device name to open for the loader.  This
  is not used by the pyMicroloader main program.  It should be.

