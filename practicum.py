import usb

####################################
def findDevices(vid=0x16c0,pid=0x05dc):
    '''
    Find all Practicum MCU boards attached to the machine, then return a list
    of USB device handles for all the boards.  This function can also find
    other devices given that the VID/PID pair is specified.

    >>> devs = findDevices()
    >>> first_board = McuBoard(devs[0])
    '''
    boards = []
    for bus in usb.busses():
        for dev in bus.devices:
            if (dev.idVendor,dev.idProduct) == (vid,pid):
                boards.append(dev)
    return boards

####################################
class McuBoard(object):
    '''
    Generic class for accessing Practicum MCU board via USB connection.
    '''

    ################################
    def __init__(self, dev):
        self.device = dev
        self.handle = dev.open()

    ################################
    def getVendorName(self):
        '''
        Return board's vendor name (i.e., manufacturer name)
        '''
        return self.handle.getString(self.device.iManufacturer, 256)

    ################################
    def getDeviceName(self):
        '''
        Return board's device name (i.e., product name)
        '''
        return self.handle.getString(self.device.iProduct, 256)

    ################################
    def usbWrite(self, request, data=[], index=0, value=0):
        '''
        Send data output to the USB device (i.e., MCU board)
           request: request number to appear as bRequest field on the USB device
           index: 16-bit value to appear as wIndex field on the USB device
           value: 16-bit value to appear as wValue field on the USB device
        '''
        reqType = usb.TYPE_VENDOR | usb.RECIP_DEVICE | usb.ENDPOINT_OUT
        self.handle.controlMsg(
                reqType, request, data, value=value, index=index)

    ################################
    def usbRead(self, request, length=1, index=0, value=0):
        '''
        Request data input from the USB device (i.e., MCU board)
           request: request number to appear as bRequest field on the USB device
           length: number of bytes to read from the USB device
           index: 16-bit value to appear as wIndex field on the USB device
           value: 16-bit value to appear as wValue field on the USB device

        If successful, the method returns a tuple of length specified
        containing data returned from the MCU board.
        '''
        reqType = usb.TYPE_VENDOR | usb.RECIP_DEVICE | usb.ENDPOINT_IN
        buf = self.handle.controlMsg(
                reqType, request, length, value=value, index=index)
        return buf

