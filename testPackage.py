import time

def main():
    print('Already imported.')

LIGHT_VALUE = 0
main()

def increase_light():
    global LIGHT_VALUE
    LIGHT_VALUE += 5;

def polling_forever():
    while(True):
        time.sleep(1)
        print("Current LIGHT VALUE: %d" % LIGHT_VALUE)
