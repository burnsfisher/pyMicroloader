# /* Copyright (C) 2022, Heimir Thor Sverrisson
#  *
#  */

#
# This module implements the Ymodem protocol and is used with the
# AMSAT pyMicroloader module to access the Texas
# Instruments serial port flash loader.
#

import sys
from modem import YMODEM


class YmodemMCU:
    """
    This class is used to send or receive files from the Microprocessor.
    It uses the ymodem protocol to send or receive the file.

    This code assumes that a flash loader is already connected on serial_port
    and is ready to either receive or send a file. It is the responsibility
    of the calling code to ensure that it is the case.
    """

    def __init__(self, serial_port):
        self.port = serial_port
        self.ymodem = YMODEM(self._get_byte, self._put_byte)

    def _get_byte(self, size, timeout=5, debug=False):
        "Internal callback function used by ymodem to read from serial port"
        return self.port.read(size)

    def _put_byte(self, data, debug=False):
        "Internal callback function used by ymodem to write to serial port"
        return self.port.write(data)

    def send(self, file_name):
        return self.ymodem.send(file_name)

    def receive(self, directory):
        return self.ymodem.recv(directory)


def show_error(message):
    print("Command line error:", file=sys.stderr)
    print(f"\t{message}", file=sys.stderr)
    sys.exit(2)


def main():
    import serial
    import getopt
    try:
        opts, args = getopt.getopt(sys.argv[1:], "srf:p:", [
                                   "send", "receive", "file=", "port="])
    except getopt.GetoptError as err:
        print(err)
        sys.exit(1)
    # Process the command line
    send = False
    receive = False
    file_name = None
    port_name = None
    for o, a in opts:
        if o in ("-s", "--send"):
            send = True
        elif o in ("-r", "--receive"):
            receive = True
        elif o in ("-f", "--file"):
            file_name = a
        elif o in ("-p", "--port"):
            port_name = a
        else:
            show_error("Unhandled option")
    if send and receive:
        show_error("Must not select send AND receive")
    if not send and not receive:
        show_error("Must select send OR receive")
    if send and file_name == None:
        show_error("Must specify file to send")
    if port_name == None:
        show_error("Must provide a port name")
    port = serial.Serial(port_name, timeout=1, baudrate=115200)
    port.flush()

    ymodem = YmodemMCU(serial_port=port)
    if send:
        success = ymodem.send(file_name)
        if success:
            print("Successfully sent!")
        else:
            print("Transmission failed!")
    elif receive:
        files_received = ymodem.receive(".")
        print(f"Received {files_received} files")


if __name__ == "__main__":
    main()
