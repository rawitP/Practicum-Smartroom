from time import sleep
import threading
from practicum import *

# DEBUG CONFIG
MONITOR_STATUS = False

class BabeMCU():

    MCU_NAME = b'ID 5910500147'
    RQ_SET_LIGHT = 0
    RQ_GET_TEMP = 1
    RQ_GET_HUMID = 2
    RQ_GET_LDR = 3
    RQ_GET_SWITCH = 4
    RQ_GET_BUFFER_DATA = 9
    # Data length must be the same in MCU's firmware
    TEMP_BYTE = 2
    HUMID_BYTE = 2
    LDR_BYTE = 2
    SWITCH_BYTE = 4
    BUFFER_DATA_LENGTH = 8

    def __init__(self, myRoom):
        self.myRoom = myRoom
        self.mcu = None
        devs = findDevices()
        for dev in devs:
            mcu = McuBoard(dev)
            if mcu.getDeviceName() == BabeMCU.MCU_NAME:
                self.mcu = mcu
                break
        if self.mcu is None:
            print("*** Babe's MCU not found")
            exit(1)
        self.prev_switch_state = [0, 0, 0, 0]
        self.cur_switch_state = [0, 0, 0, 0]

    def set_light(self, light_index, val):
        self.mcu.usbWrite(BabeMCU.RQ_SET_LIGHT, index=light_index, value=val)

    def set_air(self, val):
        self.mcu.usbWrite(BabeMCU.RQ_SET_LIGHT, index=3, value=val)

    def polling(self):
        # !!! Very risky except !!!
        # Use to prevent Input/Output error
        #try:
            raw_data = self.mcu.usbRead(BabeMCU.RQ_GET_BUFFER_DATA,
                                        length=BabeMCU.BUFFER_DATA_LENGTH)
            #print(raw_data)
            self.myRoom.set_temp_data(raw_data[4])
            self.myRoom.set_humid_data(raw_data[6])
            self.prev_switch_state = list(self.cur_switch_state)
            self.cur_switch_state = [raw_data[0], raw_data[1],
                                     raw_data[2], raw_data[3]]
            switch_data = [] # Real data will be send to myRoom
            for cur, prev in zip(self.prev_switch_state, self.cur_switch_state):
                if cur != prev:
                    switch_data.append(1)
                else:
                    switch_data.append(0)
            self.myRoom.set_switch_state(switch_data)
            '''
            raw_temp_data = self.mcu.usbRead(BabeMCU.RQ_GET_TEMP,
                                             length=BabeMCU.TEMP_BYTE)
            self.myRoom.set_temp_data((raw_temp_data[1] * 256) + raw_temp_data[0])
            raw_humid_data = self.mcu.usbRead(BabeMCU.RQ_GET_HUMID,
                                              length=BabeMCU.HUMID_BYTE)
            self.myRoom.set_humid_data((raw_humid_data[1] * 256) + raw_humid_data[0])
            # Polling switch state
            raw_switch_data = self.mcu.usbRead(BabeMCU.RQ_GET_SWITCH,
                                               length=BabeMCU.SWITCH_BYTE)
            self.prev_switch_state = list(self.cur_switch_state)
            self.cur_switch_state = [raw_switch_data[0], raw_switch_data[1],
                                     raw_switch_data[2], raw_switch_data[3]]
            switch_data = [] # Real data will be send to myRoom
            for cur, prev in zip(self.prev_switch_state, self.cur_switch_state):
                if cur != prev:
                    switch_data.append(1)
                else:
                    switch_data.append(0)
            self.myRoom.set_switch_state(switch_data)
            '''
        #except usb.core.USBError as err:
        #    print("USBError: {0}".format(err))


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
        if self.mcu is None:
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
            return
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

    IS_MONITOR = MONITOR_STATUS
    CONNECT_MCU = [True, True] # Please config before running
                                # Check, Babe
    POLLING_INTERVAL = 0.5
    UNLOCK_RFID_DATA = ([213, 8, 171, 137, 255], [125, 52, 171, 169, 75])

    def __init__(self):
        threading.Thread.__init__(self)
        self.mcu_list = []
        self.checkMCU = None
        self.babeMCU = None
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
        # Babe
        self.temp_data = 0
        self.humid_data = 0
        self.light_status = [0, 0, 0]
        self.air_status = 0
        self.ldr_data = 0
        self.switch_state = [0, 0, 0, 0] # O: Not Press,
                                         # 1: Press

    def mcu_list_setup(self):
        if self.CONNECT_MCU[0] is True:
            self.checkMCU = CheckMCU(self)
            self.mcu_list.append(self.checkMCU)
        if self.CONNECT_MCU[1] is True:
            self.babeMCU = BabeMCU(self)
            self.mcu_list.append(self.babeMCU)

    # ----------------------------- Check section ---------------------------- #
    def set_rfid_data(self, val):
        self.rfid_data = val

    LOCK_STATUS_MAP = {0: "Unlock", 1: "Lock"}
    def set_lock(self, val):
        self.lock_status = val
        if self.checkMCU != None:
            self.checkMCU.set_lock_servo(val)
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

    # ------------------------------ Babe Section ---------------------------- #
    LIGHT_STATUS_MAP = {0: 'Off', 1: 'On'}
    def set_light(self, light_index, val):
        self.light_status[light_index] = val
        if self.babeMCU != None:
            self.babeMCU.set_light(light_index, val)
        print("* Light %d: %s" % (light_index, MyRoom.LIGHT_STATUS_MAP[val]))

    def toggle_light(self, light_index):
        val = 1
        if self.light_status[light_index] == 1:
            val = 0
        self.set_light(light_index, val)

    def get_light_status(self, light_index):
        return self.light_status[light_index]

    def set_temp_data(self, val):
        self.temp_data = val

    def get_temp(self):
        return self.temp_data

    def set_humid_data(self, val):
        self.humid_data = val

    def get_humid(self):
        return self.humid_data

    def set_ldr_data(self, val):
        self.ldr_data = val

    def get_ldr_data(self):
        return self.ldr_data

    def get_air_status(self):
        return self.air_status

    AIR_STATUS_MAP = {0: 'Off', 1: 'On'}
    def set_air(self, val):
        self.air_status = val
        if self.babeMCU != None:
            self.babeMCU.set_air(val)
        print("* Air conditioner: %s" % MyRoom.AIR_STATUS_MAP[val])

    def toggle_air(self):
        val = 1
        if self.air_status == 1:
            val = 0
        self.set_air(val)

    def set_switch_state(self, val):
        self.switch_state = list(val)

    # --------------------------- Process section ---------------------------- #
    def stop(self):
        self.is_running = False

    def setup(self):
        self.set_lock(self.lock_status)
        self.set_air(self.air_status)
        for light_index, status in enumerate(self.light_status):
            self.set_light(light_index, status)

    def monitor(self):
        if self.IS_MONITOR:
            print("**********************************")
            print("* Switch state in myRoom: ", end='')
            print(self.switch_state)
            print("* Temperature: %d" % self.temp_data)
            print("* Humid: %d" % self.humid_data)
            print("* LDR value: %d" % self.ldr_data)
            print("* Air conditioner: %s" % self.AIR_STATUS_MAP[self.air_status])
            print("* Light relay: ", end='')
            print(self.light_status)
            print("**********************************")

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
        if self.switch_state[0] == 1:
            self.toggle_light(0)
        if self.switch_state[1] == 1:
            self.toggle_light(1)
        if self.switch_state[2] == 1:
            self.toggle_light(2)
        if self.switch_state[3] == 1:
            self.toggle_air()

    def run(self):
        print("*** Start MyRoom Thread")
        self.setup()
        while self.is_running:
            self.polling()
            self.monitor() # For viewing variable value
            self.process()
            sleep(MyRoom.POLLING_INTERVAL)
        print("*** Stop MyRoom Thread")

    def polling(self):
        for mcu in self.mcu_list:
            mcu.polling()

# ------------------------------- Main Program ------------------------------- #
if __name__ == "__main__":
    myRoom = MyRoom()
    myRoom.start()
    while True:
        try:
            inp = int(input())
            if inp == 1:
                myRoom.toggle_air()
                myRoom.toggle_light(0)
                myRoom.toggle_light(1)
                myRoom.toggle_light(2)
            if inp == -1:
                break
        except ValueError:
            print("--- Invalid command ---")
    myRoom.stop()
