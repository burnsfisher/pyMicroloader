import sys
import time
import pyMicromem
import pySimpleElf
import logging
import os

# For other MCUs than TMS570, this function below is called.
#
def flash_and_run(elffile, loader, forceSerialNumber, specifiedSerialNumber):
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
                logging.info("\nDevice with serial number "+str(deviceSerial)+" has been loaded before")
                if (specifiedSerialNumber):
                    if(deviceSerial != inputSerialNumber):
                        if(not forceSerialNumber):
                            #If there actually WAS a serial number specified, it is wrong
                            logging.error('Incorrect Serial Number specified. If correct, use --force)')
                            sys.exit(1)
                        else:
                            logging.info("--force used to change the serial number")
                    #else:
                        #Here there was a serial specified and it matched
                else:
                    #No number specified.  We just use the one in the device
                    inputSerialNumber = deviceSerial
            else:
                # Not flashed before
                if(not specifiedSerialNumber):
                    logging.error("This processor has not been flashed.  You must specify a serial number")
                    sys.exit(1)
                else:
                    logging.info("This processor has not been flashed. Using serial number "+str(inputSerialNumber))

        while True:
            toFlash = datafile.GetCode()
            if toFlash == None:
                break

            for i in range(0,toFlash[2]):
                thisAddr = toFlash[1]+i
                ihu.PutByte(toFlash[0][i],thisAddr)
        ihu.PutInt16(inputSerialNumber,pSerialNumber)
        ihu.MemoryFlush()
        logging.info("\nLoaded.  Starting compare.")
        ihu.MemoryCompare()
        logging.info("Done--starting execution")
        time.sleep(1)
        loader.StartExecution()


def main():
    # Alternative log format: ' %(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        level = logging.DEBUG,
        format = '%(message)s'
    )

    forceSerialNumber = False
    specifiedSerialNumber=False
    waitForDevice=False
    altosLoader=True
    uartLoader=False
    tiUartLoader = False
    portName=None
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
        elif '--port' in sys.argv[i]:
            skip=i+1
            portName=sys.argv[skip]
        elif '--force' in sys.argv[i]:
            forceSerialNumber = True
        elif '--wait' in sys.argv[i]:
            waitForDevice = True
        elif '--uart' in sys.argv[i]:
            altosLoader=False
            uartLoader=True
        elif '--usb' in sys.argv[i]:
            altosLoader=True
            uartLoader=False
        elif '--ti-uart' in sys.argv[i]:
            tiUartLoader = True
            altosLoader = False
        else:
            logging.info("\npyMicroloader V2.2--Usage:\n")
            logging.info("  python pyMicroloader.py filename [--serial n] [--force]\n")
            logging.info("     --serial is optional if the device has been flashed before;")
            logging.info("       otherwise, you must specify it.  If you specified serial")
            logging.info("       it must match the serial already flashed unless --force")
            logging.info("       is added.")
            logging.info("    --force overrides the check for serial number matching")
            logging.info("    --wait keeps retrying until the loader device is available")
            logging.info("    --usb uses the Altos USB flash loader protocol")
            logging.info("    --uart uses the AMSAT serial flash loader protocol")
            logging.info("    --ti-uart uses the ymodem flash loader protocol for TI MCUs")
            sys.exit()

    if not os.path.isfile(elffile):
        logging.error(f'Flash file: "{elffile}" was not found!')
        sys.exit()

    if altosLoader:
        import pyAltosFlash as ldr
        logging.info("Using Altos USB Flash Loader")
    elif uartLoader:
        import pySerialFlash as ldr
        logging.info("Using AMSAT Serial Flash Loader")
    elif tiUartLoader:
        import pyTISerialFlash as ldr
        logging.info("Using Texas Instruments serial flash loader (ymodem)")
    else:
        logging.info("No loader specified")
        sys.exit()

    retry = True
    while retry:
        try:
            logging.info("Try loader")
            loader = ldr.FlashLdr(device=portName, debug=True) # Connect to the MCU
            retry = False
        except ValueError as er:
            logging.info(er)
            retry = waitForDevice
            if retry:
                logging.info("Retrying in 5 sec...")
                time.sleep(5)
            else:
                sys.exit()

    # The flow for TI MCUs is different as it uses ymodem protocol
    # for reliable delivery of the code, from a binary file instead
    # the .elf used by other MCUs
    if tiUartLoader:
        loader.download_application(elffile)
        loader.StartExecution()
    else:
        flash_and_run(elffile, loader, forceSerialNumber, specifiedSerialNumber)
    exit()

if __name__ == "__main__":
    main()