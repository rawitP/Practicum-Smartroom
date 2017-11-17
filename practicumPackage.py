from time import sleep
import threading
from practicum import *

# Define constant
RQ_READ = 1
RQ_SET_LOCK = 2
RQ_READ_LENGTH = 5
POLLING_INTERVAL = 0.5
UNLOCK_RFID_DATA = ([213, 8, 171, 137, 255], [125, 52, 171, 169, 75])
# Global variable
mcu_0 = None
polling_data = None
is_polling = True
rfid_data = [0, 0, 0, 0, 0]
lock_status = 1 # 0: Unlock, 1: lock

def setup_usb():
    devs = findDevices()
    if len(devs) == 0:
        print('*** No Mcu found')
        exit(1)
    # Assign device to global
    global mcu_0
    mcu_0 = McuBoard(findDevices()[0])
    # Report devices's name
    print("Device manufacturer: %s" % (mcu_0.getVendorName()))
    print("*** Device name: %s" % mcu_0.getDeviceName())

def set_lock(val):
    # TODO: Function that set servo degree
    mcu_0.usbWrite(RQ_SET_LOCK, index=7, value=val)
    global lock_status
    lock_status = val
    print("Lock status: %d" % val)

def set_led(led_index, val):
    mcu_0.usbWrite(0, index=led_index, value=val)

def open_led():
    led_index = int(input("Enter LED index: "))
    mcu_0.usbWrite(0, index=led_index, value=1)

def close_led():
    led_index = int(input("Enter LED index: "))
    mcu_0.usbWrite(0, index=led_index, value=0)

def get_polling_data():
    return polling_data

def polling_once():
    data = mcu_0.usbRead(RQ_READ, length=RQ_READ_LENGTH)
    # Managing data from MCU
    global polling_data
    polling_data = data
    global rfid_data
    rfid_data = [polling_data[0], polling_data[1], polling_data[2],
                polling_data[3], polling_data[4]]

def polling_forever():
    while(is_polling):
        polling_once()
        sleep(POLLING_INTERVAL)

class mcuThread(threading.Thread) :
    def __init__(self):
        threading.Thread.__init__(self)
        self.is_running = True

    def stop(self):
        self.is_running = False

    def process(self):
        if lock_status == 1:
            print("Locking...")
            for each_rfid in UNLOCK_RFID_DATA:
                if each_rfid == rfid_data:
                    set_lock(0)
                    break

    def setup(self):
        set_lock(lock_status)

    def run(self):
        print("Starting MCU Thread")
        self.setup()
        while(self.is_running):
            polling_once()
            self.process()
            sleep(POLLING_INTERVAL)
        print("Stoped MCU Thread")

# Setup devices before using this package
setup_usb()
# Create polling thread
mcu_thread = mcuThread()

if __name__ == "__main__":
    # Create thread for polling
    mcu_thread.start()
    # Prompt
    while(True):
        # For error input, exit prompt
        try:
            val = int(input("Enter request: "))
        except ValueError:
            break
        # Command
        if val == 0:
            open_led()
        elif val == 3:
            close_led()
        elif val == 1:
            print(get_polling_data())
        elif val == 2:
            set_lock(1)
        elif val == -1:
            break
    # Stop all thread before exit program
    mcu_thread.stop()
    mcu_thread.join()
