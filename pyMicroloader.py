import os
import sys
import threading
import traceback
import time
import pyMicromem
import pySimpleElf

forceSerialNumber = False
specifiedSerialNumber=False
if len(sys.argv)==1:
    elffile='test.elf'
if(len(sys.argv)>=2):
   elffile=sys.argv[1]
for i in range(2,len(sys.argv)):
    if '--serial' in argv[i]:
        i+=1
        inputSerialNum=num(argv[i])
        specifiedSerialNumber=True
    elif '--force' in argv[i]:
        forceSerialNumber = True
    else:
        print("Usage: (more tom come)")

loader = pyMicromem.AltosFlash(True) # Connect to the MCU
ihu = pyMicromem.Device(loader.GetLowAddr(),loader.GetHighAddr(),loader)

with open(elffile,'rb') as file:
    datafile = pySimpleElf.SimpleElf(file)
    pSerialNumber = datafile.GetSymbol('ao_serial_number')
    pConfigVersion= datafile.GetSymbol('ao_romconfig_version')
    pConfigCheck = datafile.GetSymbol('ao_romconfig_check')
    if(pSerialNumber != None and pConfigVersion!=None and pConfigCheck != None): 
        deviceSerial = ihu.GetInt32(pSerialNumber)
        deviceConfig = ihu.GetInt16(pConfigVersion)
        deviceConfigChk = ihu.GetInt16(pConfigCheck)
        if(deviceConfig == (~deviceConfigChk & 0xFFFF)):
            # Has been flashed before
            print("\nDevice with serial number "+str(deviceSerial)+" has been loaded before")
            if (specifiedSerialNumber):
                if(deviceSerial != inputSerialNumber):
                    if(not forceSerialNumber):
                        #If there actually WAS a serial number specified, it is wrong
                        print('Incorrect Serial Number specified. If correct, use --force)')
                        sys.exit(1)
                    else:
                        print("--force used to change the serial number")
                #else:
                    #Here there was a serial specified and it matched
            else:
                #No number specified.  We just use the one in the device
                inputSerialNumber = deviceSerial
        else:
            # Not flashed before
            if(not specifiedSerialNumber):
                print("This processor has not been flashed.  You must specify a serial number")
                sys.exit(1)
            else:
                print("This processor has not been flashed. Using serial number "+str(inputSerialNumber))

    while True:
        toFlash = datafile.GetCode()
        if toFlash == None:
            break

        for i in range(0,toFlash[2]):
            thisAddr = toFlash[1]+i
            ihu.PutByte(toFlash[0][i],thisAddr)
    ihu.PutInt16(inputSerialNumber,pSerialNumber)
    ihu.MemoryFlush()
    print("\nLoaded.  Starting compare.")
    ihu.MemoryCompare()
    print("Done--starting execution")
    time.sleep(1)
    loader.StartExecution()
    
##except ELFError as ex:
##    sys.stderr.write("ELF error: %s\n" % ex)
##    sys.exit(1)

exit()


##ihu.PutInt16(specifiedSerialNumber,pSerialNumber)
##ihu.MemoryFlush()
##print("Loaded.  Starting compare...")
##ihu.MemoryCompare()
##print("Done--starting execution")
##time.sleep(1)
##loader.StartExecution()
        


