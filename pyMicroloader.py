import os
import sys
import threading
import traceback
import time
import pyMicromem
import pySimpleElf

forceSerialNumber = False
specifiedSerialNumber=False
waitForDevice=False
if len(sys.argv)==1:
    elffile='test.elf'
if(len(sys.argv)>=2):
   elffile=sys.argv[1]
skip=0
for i in range(2,len(sys.argv)):
    if i == skip:
        continue
    if '--serial' in sys.argv[i]:
        skip=i+1
        inputSerialNumber=int(sys.argv[skip])
        specifiedSerialNumber=True
    elif '--force' in sys.argv[i]:
        forceSerialNumber = True
    elif '--wait' in sys.argv[i]:
        waitForDevice = True
    else:
	print("\npyMicroloader V1.1--Usage:\n")
        print("  python pyMicroloader.py filename [--serial n] [--force]\n")
        print("     --serial is optional if the device has been flashed before;")
        print("       otherwise, you must specify it.  If you specified serial")
        print("       it must match the serial already flashed unless --force")
        print("       is added.")
        print("    --force overrides the check for serial number matching")
	print("    --wait keeps retrying until the loader device is available")
        sys.exit()
retry = True
while retry:
    try:
        loader = pyMicromem.AltosFlash(debug=True) # Connect to the MCU
	retry = False
    except ValueError as er:
        print(er)
	retry = waitForDevice
        if retry:
	    print("Retrying in 5 sec...")
            time.sleep(5)
	else:
            sys.exit()

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
        


