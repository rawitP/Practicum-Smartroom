import http.server
import threading
import os
import urllib
import smartroom

# Constant Variable
SERVER_PORT = 30000
SERVER_ADDRESS = ('',SERVER_PORT)
ROOT_DIR = os.path.dirname(os.path.realpath(__file__))

def toBytes(data):
    data = str(data)
    return bytes(data, "utf-8")

class MyHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    myRoom = None

    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        self._set_headers()
        # ----------------- Map path to function section --------------------- #
        if self.path == '/lock':
            self.wfile.write(toBytes(self.myRoom.get_lock_status()))
        elif self.path == '/lock?set=on':
            self.myRoom.set_lock(1)
            self.wfile.write(b"Success")
        elif self.path == '/lock?set=off':
            self.myRoom.set_lock(0)
            self.wfile.write(b"Success")
        # DHT11
        elif self.path == '/temp':
            self.wfile.write(toBytes(self.myRoom.get_temp()))
        elif self.path == '/humid':
            self.wfile.write(toBytes(self.myRoom.get_humid()))
        # Light
        elif self.path == '/light0':
            self.wfile.write(toBytes(self.myRoom.get_light_status(0)))
        elif self.path == '/light0?set=on':
            self.myRoom.set_light(0, 1)
            self.wfile.write(b"Success")
        elif self.path == '/light0?set=off':
            self.myRoom.set_light(0, 0)
            self.wfile.write(b"Success")
        elif self.path == '/light1':
            self.wfile.write(toBytes(self.myRoom.get_light_status(1)))
        elif self.path == '/light1?set=on':
            self.myRoom.set_light(1, 1)
            self.wfile.write(b"Success")
        elif self.path == '/light1?set=off':
            self.myRoom.set_light(1, 0)
            self.wfile.write(b"Success")
        elif self.path == '/light2':
            self.wfile.write(toBytes(self.myRoom.get_light_status(2)))
        elif self.path == '/light2?set=on':
            self.myRoom.set_light(2, 1)
            self.wfile.write(b"Success")
        elif self.path == '/light2?set=off':
            self.myRoom.set_light(2, 0)
            self.wfile.write(b"Success")
        # air
        elif self.path == '/air':
            self.wfile.write(toBytes(self.myRoom.get_air_status()))
        elif self.path == '/air?set=on':
            self.myRoom.set_air(1)
            self.wfile.write(b"Success")
        elif self.path == '/air?set=off':
            self.myRoom.set_air(0)
            self.wfile.write(b"Success")
        else: # If user access wrong path #
            self.wfile.write(b"<html><head><title>My Title</title></head>")
            self.wfile.write(bytes("<body><p>You accessed path: %s</p>" % self.path,"utf-8"))
            self.wfile.write(b"</body></html>")

    def do_POST(self):
        self._set_headers()
        self.wfile.write(b"Success")

class serverThread (threading.Thread) :
    def __init__(self, threadID, server_address, request_handler):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.server_address = server_address
        self.request_handler = request_handler
        self.httpd = http.server.HTTPServer(self.server_address, self.request_handler)

    def run(self):
        print ("### Start serverThread: %d" % self.threadID)
        self.httpd.serve_forever()
        print ("### Stop serverthread")

def main():
    myRoom = smartroom.MyRoom()
    myRoom.start()
    MyHTTPRequestHandler.myRoom = myRoom
    request_handler = MyHTTPRequestHandler
    thread_server = serverThread(1, SERVER_ADDRESS, request_handler)
    thread_server.start()
    # Command prompt
    while(True):
        try:
            val = int(input())
            if val == -1:            
                break
        except ValueError:
            print("--- Invalid command ---")
    thread_server.httpd.shutdown()
    myRoom.stop()

if __name__ == "__main__":
    main()

