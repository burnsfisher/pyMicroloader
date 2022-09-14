# Test files for Texas Instruments MCUs

This directory contains binary files created with the `TI Code Composer Studio`
to test the flash loader.

* `blinky.bin` is a bare metal program that blinks the LEDs on the TMS570LS1224 Dev kit
* `FreeRtosBlinky.bin` does the same thing, but runs on top of the FreeRTOS operating system. A patch wire needs to be connected on the Dev kit to see the LED blink from J5(pin 10) to J9(pin 2) or from GIOB[2] to N2HET2[8]