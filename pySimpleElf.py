import os
import sys
import threading
import traceback
import time
import logging

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

class SimpleElf:
    def __init__(self,file):
        self.currentCodeSegment=0
        self.isOk=False
        self.startSeg=0
        self.startSec=0
        elffile = ELFFile(file)
        if(elffile.elfclass != 32):
            raise Exception("64 bit Elf File","Can't deal right now")
        else:
            self.myElffile = elffile
            self.isOk=True
        return
    def _CheckOk(self):
        if(not self.isOk):
            raise Exception("Elf file not open")
    def GetSymbol(self,symbol):
        self._CheckOk()
        for section in self.myElffile.iter_sections():
            if  not isinstance(section,SymbolTableSection):
                continue
            if(section['sh_entsize']==0):
               continue
            for nsym, symbolStruct in enumerate(section.iter_symbols()):
                if symbolStruct.name == symbol:
                    return symbolStruct['st_value']
    def GetCode(self):
        for segNum in range(self.startSeg,self.myElffile.num_segments()):
            self.startSeg = segNum #Be able to restart
            segment=self.myElffile.get_segment(segNum)
            #for segment in myElffile.iter_segments():
            #logging.info("Got segment number "+str(segNum))
            psecPaddr=segment['p_paddr']
            psecVaddr=segment['p_vaddr']
            psecOffset=segment['p_offset']
            psecFilesz=segment['p_filesz']
            psecMemsz=segment['p_memsz']
            #logging.info('phdr: Paddr='+hex(psecPaddr)+' Vaddr='+hex(psecVaddr))
            #for nsec, section in enumerate(myElffile.iter_sections()):
            for secNum in range(self.startSec,self.myElffile.num_sections()):
                self.startSec=secNum+1
                section = self.myElffile.get_section(secNum)
                sOffset = section['sh_offset']
                sPaddr = psecPaddr + sOffset - psecOffset
                sSize = section['sh_size']
                #logging.info("sSize="+hex(sSize)+" psecOffset="+hex(psecOffset)+" sOffset="+hex(sOffset)+
                 #     " sum="+hex(psecOffset+psecFilesz))
                if(sSize!=0 and psecOffset<=sOffset and sOffset<(psecOffset+psecFilesz)):
                    #logging.info('Returning Section paddr='+hex(sPaddr)+' Size='+hex(sSize))
                    data = section.data()
                    return[data,sPaddr,sSize]
                #else:
                    #logging.info("Skiping section "+str(secNum))

            self.startSec=0

if __name__ == '__main__':
    with open('test.elf','rb') as file:
        try:
            thisElf = SimpleElf(file)
            serial = thisElf.GetSymbol('ao_serial_number')
            logging.info("Serial number address is "+hex(serial))
            dataSection = thisElf.GetCode()
            logging.info("Code addr="+hex(dataSection[1])+" len="+hex(dataSection[2]))
            dataSection = thisElf.GetCode()
            logging.info("Code addr="+hex(dataSection[1])+" len="+hex(dataSection[2]))

        except ELFError as ex:
          sys.stderr.write("ELF error: %s\n" % ex)
          sys.exit(1)
