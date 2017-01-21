# pyMicroloader
A program loader for embedded microprocessors

The intent of this loader it for use with a cross-development
environment for embedded microprocessors.  This loader is
intended to run in the development environment (or similar).

This program expects a bootloader of some sort to run in
the microprocessor.  It currently has a class that corresponds
to the AltusMetrum boot loader.  A class could be written to use
(for example) the ST-Link dongle or a built-in ROM loader in a
processor.

Similarly, there (will be) a class to represent an ELF file.  A 
similar class could be written to represent, say, an iHex file.

The main program understands something about the Altus Metrum
scheme, including the serial number and config check locations.
You can modify this easily using the same classes

Usage:

  python pyMicroloader filename.elf [--serial n [--force]]

Dependencies:
	It depends on the 'pyserial' and 'pyelftools' packages

Packages and Classes created (which pyMicroloader.py depends on):
	pyMicromem.py contains classes as follows:
		MemoryPage, which represents a page in the microprocessor
		Device, which represents all of memory in a micro
		AltosFlash, which represents the flash loader in the
			loader with minimal changes elsewhere)
	pySimpleElf
	        This package contains the class SimpleElf, which is reall
		a simple wrapper around the pyelftools class ELFFile

TODO:
-Fix try/except to better deal with cases when files are not found
 or microprocessors are not connected

-Deal with other error conditions like the elf file containing more
 data than the processor has memory.
