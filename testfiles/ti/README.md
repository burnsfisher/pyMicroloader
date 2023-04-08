# Test files for Texas Instruments MCUs

This directory contains binary files created with the `TI Code Composer Studio`
to test the flash loader.

* `Blink.bin` is a bare metal program that blinks the LEDs on the rt-ihu, counting in binary on the green, yellow and red LEDs.
* `FreeRTOSBlink.bin` does a similar thing, but runs on top of the FreeRTOS operating system. Here a separate task is running blinking each LED with different switching period.