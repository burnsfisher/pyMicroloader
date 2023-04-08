# pyMicroloader

A host loader for embedded microprocessors

## Revision history
* V1.1, June 3, 2018: Search for serial devices rather than just taking the first one.
* V1.2, Jan 22, 2019: Change design of pyMicroMem slightly to allow multiple loader types
* V2.0, Aug 06, 2021: Debug and fix up the serial loader.  It is now slow but working at 57.6K baud
* V2.1, Feb 01, 2022: Port to Python3
* V2.2, Sep 10, 2022: Support added for Texas Instruments, TMS570 MCUs over serial

## Concepts

In this context a **host loader** is a program, like `pyMicroloader`, running
on a PC computer used by a human to load a program from its disk to an embedded microprocessor (MCU).

A **flash loader** is code running on the embedded microprocessor communicating with the host loader and saving the program into flash memory.

The intent of this host loader it for use with a cross-development
environment for embedded microprocessors.  This loader is
intended to run in the development environment (or similar);
I developed it on Linux (Ubuntu 14 and 18) but also tested it on
Windows 7, a while ago.

This program expects a flash loader of some sort to run in the microprocessor.
It currently has a class that corresponds
to the AltusMetrum flash loader and a separate class that corresponds
to the AMSAT Golf-Tee serial loader.  The most recent addition is a
class communicating with a flash loader running in the Texas Instruments TMS570 MCUs using the ymodem serial protocol.

A new class could be written to use
(for example) the ST-Link dongle or a built-in ROM loader in a
processor. NOTE: For Windows 7, it needs a driver (well really
an INF file) from Altus Metrum to recognize the USB loader device when
it is plugged into the USB port.

Similarly, there is class to represent an ELF file. A similar class could be written to represent, say, an iHex file.

## Usage

```
  python pyMicroloader.py filename.elf [--serial n [--force]]
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
   --ti-uart Use serial loader (ymodem) for Texas Instruments MCUs
```

## Dependencies

This code depends on the `pyserial`, `pyelftools` and `modem` python packages. See further the Installation section below.

## Packages and Classes

`pyMicroloader.py` depends on files:

* `pyMicromem.py` contains classes as follows:
		- `MemoryPage` which represents a page in the microprocessor
		- `Device` which represents all of memory in a microprocessor
* `pyAltosFlash.py`, which represents the boot loader within the device.
* `pySimpleElf.py`. This package contains the class `SimpleElf`, which is really a simple wrapper around the `pyelftools` class `ELFFile`.

`pyAltosFlash.py`, `pySerialFlash.py` and `pyTISerialFlash.py` all contain the class `FlashLdr`, which represents the flavor of the loader to be used.


## Installation

  Works for both Linux and Windows

1. **Install Python 3** for your computer or from `python.org` if it is not already on your system. Choose the latest update. You also have to pay attention to the OS version that you are using in order to choose the right Python.
2. `pip install pyserial`
3. `pip install pyelftools`
4. `pip install install/modem-1.1-py3-none-any.whl`
5. Clone this repository or download and unzip `pyMicroloader` (no install necessary)

## Installation for developing GUI

To develop the Qt GUI application create a python virtual environment
that will not interfere with the local python setup on the development
machine and will not be stored in git.

1.  create the virtual environment, run `python3 -m venv venv`
2.  activate the virtual environment
    1. run `source env/bin/activate` on Linux or Mac
    2. run `env\Scripts\activate.bat` on Windows
1.  run `pip install pyserial pyelftools install/modem-1.1-py3-none-any.whl`
2.  run `pip install PyQt5 pyqt5-tools`
3.  optionally do `pip install pyinstaller` if you want to create a binary executable

To change the GUI itself run `./design.sh`. This will fire up the Qt design
tool. The file to change is `ui/main_window.ui`. If an update is made to
the UI it has to be compiled into a python file. That is done with
running the `./make.sh` script that updates the `main_window_ui.py` file.

Optionally a binary executable can be created from the `Hostloader.py` with
all its dependencies. That is done by running
`pyinstaller --onefile Hostloader.py`. This will create a binary for current
platform as `dist/Hostloader`.

Note that both `venv` and `dist` directories are excluded from `git` as
it is usually not a good idea to store a boatload of binary files there.

## TODO

* Generally fix errors to work more cleanly.  In particular:
  - Fix try/except to better deal with cases when files are not found
  - Deal with cases where the elf file contains more data than the processor has memory
* There may be elf sections and segments that I have not dealt with, but which are
required by some uProcs
* The `AltosLoader` class can take an explicit device name to open for the loader.This is not used by the `pyMicroloader.py` main program. It should be. In fact, both loaders should be able to take an explicit device name.
