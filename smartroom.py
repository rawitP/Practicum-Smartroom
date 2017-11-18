from time import sleep
import threading
from practicum import *

class CheckMCU():
    MCU_NAME = b'ID 5910500520'
    RQ_SET_LOCK = 2
    RQ_GET_BUFFER_DATA = 9
    BUFFER_DATA_LENGTH = 8

    def __init__(self, myRoom):
        self.myRoom = myRoom
        self.mcu = None
        devs = findDevices()
        for dev in devs:
            mcu = McuBoard(dev)
            if mcu.getDeviceName() == CheckMCU.MCU_NAME:
                self.mcu = mcu
                break
        if self.mcu == None:
            print("*** Check's MCU not found")
            exit(1)
        self.polling_data = []

    def set_lock_servo(self, val):
        self.mcu.usbWrite(CheckMCU.RQ_SET_LOCK, index=7, value=val)

    def polling(self):
        # !!! Very risky except !!!
        # Use to prevent Input/Output error
        try:
            self.polling_data = self.mcu.usbRead(CheckMCU.RQ_GET_BUFFER_DATA,
                                                 length=CheckMCU.BUFFER_DATA_LENGTH)
        except usb.core.USBError as err: 
            print("USBError: {0}".format(err))
            pass
        rfid_data = [self.polling_data[0], self.polling_data[1], self.polling_data[2],
                     self.polling_data[3], self.polling_data[4]]
        lock_button = self.polling_data[5]
        outside_button = self.polling_data[6]
        inside_button = self.polling_data[7]
        self.myRoom.set_rfid_data(rfid_data)
        self.myRoom.set_lock_button(lock_button)
        self.myRoom.set_outside_button(outside_button)
        self.myRoom.set_inside_button(inside_button)

              

class MyRoom(threading.Thread):
    Check_mcu = False
    Babe_mcu = False
    devs = findDevices()
    for dev in devs:
        mcu = McuBoard(dev)
        if mcu.getDeviceName() == b'ID 5910500520' :
            Check_mcu = True
        if mcu.getDeviceName() == b'ID 5910500147' :
            Babe_mcu = True
        if Babe_mcu and Check_mcu :
            break
    print(Check_mcu)
    print(Babe_mcu)
    CONNECT_MCU = [Check_mcu, Babe_mcu]]
    POLLING_INTERVAL = 0.3
    UNLOCK_RFID_DATA = ([213, 8, 171, 137, 255], [125, 52, 171, 169, 75])

    def __init__(self):
        threading.Thread.__init__(self)
        self.mcu_list = []
        self.mcu_list_setup()
        self.is_running = True
        self.rfid_data = [0, 0, 0, 0, 0]
        self.lock_status = 0 # 0: Unlock,
                             # 1: Lock
        self.lock_button = 1 # 0: Press,
                             # 1: Not Press
        self.counting_state = 0 # 0: Initial state,
                                # 1: Pressed Inside,
                                # 2: Pressed Outside,
                                # 3: Wait for button to not pressed
        self.outside_button = 1
        self.inside_button = 1
        self.counting_amount = 0
        self.temp_data = 0
        self.humid_data = 0

    def mcu_list_setup(self):
        if self.CONNECT_MCU[0] == True:
            self.mcu_list.append(CheckMCU(self))
        if self.CONNECT_MCU[1] == True:
            self.mcu_list.append(BabeMCU(self))
        

    def set_rfid_data(self, val):
        self.rfid_data = val

    LOCK_STATUS_MAP = {0: "Unlock", 1: "Lock"}
    def set_lock(self, val):
        self.lock_status = val
        for mcu in self.mcu_list:
            if mcu.__class__ == CheckMCU:
                mcu.set_lock_servo(val)
                break
        print("* Lock status: %s" % MyRoom.LOCK_STATUS_MAP[val])        

    def get_lock_status(self):
        return self.lock_status

    def set_lock_button(self, val):
        self.lock_button = val

    def set_outside_button(self, val):
        self.outside_button = val
    
    def set_inside_button(self, val):
        self.inside_button = val

    def set_counting_state(self, val):
        self.counting_state = val

    def change_counting_amount(self, val):
        self.counting_amount += val
        print("* Counting amount: %d" % self.counting_amount)

    def counting_process(self):
        if self.counting_state == 3:
            if self.inside_button == 0 or self.outside_button == 0:
                pass
            else:
                self.set_counting_state(0)
        if self.inside_button == 0:
            if self.counting_state == 2:
                self.change_counting_amount(1)
                self.set_counting_state(3)
            elif self.counting_state == 0:
                self.set_counting_state(1)
        elif self.outside_button == 0:
            if self.counting_state == 1:
                self.change_counting_amount(-1)
                self.set_counting_state(3)
            elif self.counting_state == 0:
                self.set_counting_state(2)

    def stop(self):
        self.is_running = False

    def setup(self):
        self.set_lock(self.lock_status)

    def process(self):
        if self.lock_status == 1:
            for each_rfid in self.UNLOCK_RFID_DATA:
                if self.rfid_data == each_rfid:
                    self.set_lock(0)
                    break
        else:
            if self.lock_button == 0:
                self.set_counting_state(0)
                self.set_lock(1)
            self.counting_process()

    def run(self):
        print("*** Start MyRoom Thread")
        self.setup()
        while self.is_running :
            self.polling()
            self.process()
            sleep(MyRoom.POLLING_INTERVAL)
        print("*** Stop MyRoom Thread")

    def polling(self):
        for mcu in self.mcu_list:
            mcu.polling()

if __name__ == "__main__":
    myRoom = MyRoom()
    myRoom.start()
    while True:
        try:
            inp = int(input("Enter request: "))
            if inp == -1:
                break
        except ValueError:
            print("--- Invalid command")
            pass
    myRoom.stop()