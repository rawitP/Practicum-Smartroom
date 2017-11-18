# !!! Already expect for usb.core.USBError
from time import sleep
import threading
from practicum import *

# Define constant
CONNECT_MCU = [True, False] # CHECK, BABE
RQ_READ = 1
RQ_SET_LOCK = 2
RQ_GET_BUFFER_DATA = 9
BUFFER_DATA_LENGTH = 8 # Must be the same value in MCU Firmware
RQ_READ_LENGTH = 5
POLLING_INTERVAL = 0.3
UNLOCK_RFID_DATA = ([213, 8, 171, 137, 255], [125, 52, 171, 169, 75])
MCU_0_NAME = b'ID 5910500520'
MCU_1_NAME = b'ID 5910500147'
# Global variable  
mcu_0 = None
polling_data = None # Store raw data from Check's MCU
is_polling = True
rfid_data = [0, 0, 0, 0, 0]
lock_status = 0 # 0: Unlock, 1: lock
lock_button = 1 # 0: Pressed, 1: Not Pressed
counting_state = 0 # 0: Initial state, 1: Inside->Outside, 2: Outside->Inside
                   # 3: Wait for button to not pressed
outside_button = 1
inside_button = 1
counting_amount = 0
# Babe Board
mcu_1 = None
temp_data = None # Int
humid_data = None # Int
# LED and Air status

def setup_usb():
    devs = findDevices()
    if len(devs) == 0:
        print('*** No Mcu found')
        exit(1)
    # Assign device to global
    global mcu_0, mcu_1
    tmp_mcus = []
    for dev in devs:
        mcu = McuBoard(dev)
        if mcu.getDeviceName() == MCU_0_NAME:
            mcu_0 = mcu
        elif mcu.getDeviceName() == MCU_1_NAME:
            mcu_1 = mcu
    # Check require
    if CONNECT_MCU[0] and mcu_0 == None:
        print('Not found Check MCU')
        exit(1)
    if CONNECT_MCU[1] and mcu_1 == None:
        print('Not found Babe MCU')
        exit(1)
 
def set_counting_state(val):
    global counting_state
    counting_state = val

def change_counting_amount(val):
    global counting_amount
    counting_amount += val
    print("Counting amount: %d" % counting_amount)

def counting_process():
    if counting_state == 3:
        if inside_button == 0 or outside_button == 0:
            pass
        else:
            set_counting_state(0)
    if inside_button == 0:
        if counting_state == 2:
            change_counting_amount(1)
            set_counting_state(3)
        elif counting_state == 0:
            set_counting_state(1)
    elif outside_button == 0:
        if counting_state == 1:
            change_counting_amount(-1)
            set_counting_state(3)
        elif counting_state == 0:
            set_counting_state(2)

def set_lock(val):
    # TODO: Function that set servo degree
    mcu_0.usbWrite(RQ_SET_LOCK, index=7, value=val)
    global lock_status
    lock_status = val
    print("Lock status: %d" % val)

def get_lock_status():
    return lock_status

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
    global polling_data
    try:
        data = mcu_0.usbRead(RQ_GET_BUFFER_DATA, length=BUFFER_DATA_LENGTH)
        polling_data = data
    except usb.core.USBError as err: ### !!! This is a very risky command !!! ###
        print("USBError: {0}".format(err))
        pass
    #print(polling_data)
    # Managing data from MCU
    global rfid_data, lock_button, outside_button, inside_button
    rfid_data = [polling_data[0], polling_data[1], polling_data[2],
                 polling_data[3], polling_data[4]]
    lock_button = polling_data[5]
    outside_button = polling_data[6]
    inside_button = polling_data[7]

class mcuThread(threading.Thread) :
    def __init__(self):
        threading.Thread.__init__(self)
        self.is_running = True

    def stop(self):
        self.is_running = False

    def process(self):
        if lock_status == 1:
            for each_rfid in UNLOCK_RFID_DATA:
                if each_rfid == rfid_data:
                    set_lock(0)
                    break
        else:
            if lock_button == 0:
                set_counting_state(0)
                set_lock(1)
            counting_process()  

    def setup(self):
        set_lock(lock_status)

    def run(self):
        print("Starting MCU Thread")
        self.setup()
        while self.is_running:
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
    if mcu_0 != None:
        mcu_thread.start()
    else:
        exit(1)
    # Prompt
    while True:
        # For error input, exit prompt
        try:
            val = int(input("Enter request: "))
        except ValueError:
            break
        # Command
        if CONNECT_MCU[0] == True:
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
