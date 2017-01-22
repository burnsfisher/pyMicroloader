# pyMicroloader
A program loader for embedded microprocessors

The intent of this loader it for use with a cross-development
environment for embedded microprocessors.  This loader is
intended to run in the development environment (or similar);
I developed it on Linux (Ubuntu 14) but also tested it on
Windows 7.

This program expects a bootloader of some sort to run in
the microprocessor.  It currently has a class that corresponds
to the AltusMetrum boot loader.  A class could be written to use
(for example) the ST-Link dongle or a built-in ROM loader in a
processor. NOTE: For Windows 7, it needs a driver (well really 
an INF file) from Altus Metrum to recognize the loader device when
it is plugged into the USB port.

Similarly, there is class to represent an ELF file.  A 
similar class could be written to represent, say, an iHex file.


Usage:

  python pyMicroloader filename.elf [--serial n [--force]]

Dependencies:
	It depends on the 'pyserial' and 'pyelftools' packages

Packages and Classes created (which pyMicroloader.py depends on):
	pyMicromem.py contains classes as follows:
		MemoryPage, which represents a page in the microprocessor
		Device, which represents all of memory in a microprocessor
		AltosFlash, which represents the boot loader within the
			device.
			
	pySimpleElf
	        This package contains the class SimpleElf, which is
		really a simple wrapper around the pyelftools class ELFFile


Installation:
	(Seems to work for both Ubuntu Linux and Windows 7)
		1) Install Python2.7 if it is not already there from
		   python.org.  Choose the latest update (there will
		   likely be no more) and the Windows version you
		   have.  (This may work on Python 3.  Not tested)
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

o The AltosLoader class currently thinks that the first device it comes across within
  the specified namespace (ttyACMx for Linux; COMn for Windows) is the right device.
  This needs to be a lot more clever.

o The AltosLoader class can take an explicit device name to open for the loader.  This
  is not used by the pyMicroloader main program.  It should be
