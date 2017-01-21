import os
import sys
import threading
import traceback
import time
import serial
from elftools import __version__
from elftools.common.exceptions import ELFError
from elftools.common.py3compat import (
        ifilter, byte2int, bytes2str, itervalues, str2bytes)
from elftools.elf.elffile import ELFFile
from elftools.elf.dynamic import DynamicSection, DynamicSegment
from elftools.elf.enums import ENUM_D_TAG
from elftools.elf.segments import InterpSegment, NoteSegment
from elftools.elf.sections import SymbolTableSection
from elftools.elf.gnuversions import (
    GNUVerSymSection, GNUVerDefSection,
    GNUVerNeedSection,
    )
from elftools.elf.relocation import RelocationSection
from elftools.elf.descriptions import (
    describe_ei_class, describe_ei_data, describe_ei_version,
    describe_ei_osabi, describe_e_type, describe_e_machine,
    describe_e_version_numeric, describe_p_type, describe_p_flags,
    describe_sh_type, describe_sh_flags,
    describe_symbol_type, describe_symbol_bind, describe_symbol_visibility,
    describe_symbol_shndx, describe_reloc_type, describe_dyn_tag,
    describe_ver_flags, describe_note
    )
from elftools.elf.constants import E_FLAGS
from elftools.dwarf.dwarfinfo import DWARFInfo
from elftools.dwarf.descriptions import (
    describe_reg_name, describe_attr_value, set_global_machine_arch,
    describe_CFI_instructions, describe_CFI_register_rule,
    describe_CFI_CFA_rule,
    )
from elftools.dwarf.constants import (
    DW_LNS_copy, DW_LNS_set_file, DW_LNE_define_file)
from elftools.dwarf.callframe import CIE, FDE
import pyMicromem

specifiedSerialNumber=0
if len(sys.argv)==1:
    elffile='test.elf'
if(len(sys.argv)>=2):
   elffile=sys.argv[1]
if len(sys.argv)>3:
    if '-serial' in sys.argv[2]:
        specifiedSerialNumber=int(sys.argv[3])

loader = pyMicromem.AltosFlash(True) # Connect to the MCU
ihu = pyMicromem.Device(loader.GetLowAddr(),loader.GetHighAddr(),loader)

with open(elffile,'rb') as file:
    try:
        myElffile = ELFFile(file)
        if(myElffile.elfclass != 32):
            print("64-bit Elf file.  Can't deal right now")
            sys.exit(1)
            
        #Find the address of the serial number and the ROM config variables

        for section in myElffile.iter_sections():
            if  not isinstance(section,SymbolTableSection):
                continue
            if(section['sh_entsize']==0):
               continue
            for nsym, symbol in enumerate(section.iter_symbols()):
                if symbol.name == 'ao_serial_number':
                    pSerialNumber = symbol['st_value']
                if symbol.name == 'ao_romconfig_version':
                    pRomConfigVersion = symbol['st_value']
                if symbol.name == 'ao_romconfig_check':
                    pRomConfigCheck=symbol['st_value']
               

        deviceSerial = ihu.GetInt32(pSerialNumber)
        deviceConfig = ihu.GetInt16(pRomConfigVersion)
        deviceConfigChk = ihu.GetInt16(pRomConfigCheck)

        print('Ser='+str(deviceSerial)+' Cfg='+hex(deviceConfig)+' Chk='+hex(deviceConfigChk))
        if(deviceConfig == (~deviceConfigChk & 0xFFFF)):
           #Looks like there is an ok software load there
           if (not (deviceSerial == specifiedSerialNumber)):
               # Flashed before and specified serial number does not match
               if(specifiedSerialNumber):
                   #If there actually WAS a serial number specified, it is wrong
                   print('Incorrect Serial Number specified.  (Will eventually be able to override)')
                   sys.exit(1)
               else:
                    #We need to be sure to write the serial number even if it was already there
                    specifiedSerialNumber = deviceSerial        
        else:
            # Not flashed before
            if(specifiedSerialNumber == 0):
                print("This processor has not been flashed.  You must specify a serial number")
            else:
                print("This processor has not been flashed. Using serial number "+str(specifiedSerialNumber))
        elfHeader = myElffile.header
        for segment in myElffile.iter_segments():
            psecPaddr=segment['p_paddr']
            psecVaddr=segment['p_vaddr']
            psecOffset=segment['p_offset']
            psecFilesz=segment['p_filesz']
            psecMemsz=segment['p_memsz']
            #print('phdr: Paddr='+hex(psecPaddr)+' Vaddr='+hex(psecVaddr))

            for nsec, section in enumerate(myElffile.iter_sections()):
                sOffset = section['sh_offset']
                sPaddr = psecPaddr + sOffset - psecOffset
                sSize = section['sh_size']
                if(psecOffset<=sOffset and sOffset<(psecOffset+psecFilesz)):
                    #print('  Writing Section paddr='+hex(sPaddr)+' Size='+hex(sSize))
                    data = section.data()
                    for i in range(0,sSize):
                        thisAddr = sPaddr+i;
                        ihu.PutByte(data[i],thisAddr)
        ihu.PutInt16(specifiedSerialNumber,pSerialNumber)
        ihu.MemoryFlush()
        print("Loaded.  Starting compare...")
        ihu.MemoryCompare()
        print("Done--starting execution")
        time.sleep(1)
        loader.StartExecution()
        
    except ELFError as ex:
          sys.stderr.write("ELF error: %s\n" % ex)
          sys.exit(1)


