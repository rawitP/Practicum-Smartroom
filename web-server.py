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
        if self.path == "/lock":
            self.wfile.write(toBytes(self.myRoom.get_lock_status()))
            return
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
    request_handler = MyHTTPRequestHandler
    request_handler.myRoom = myRoom
    thread_server = serverThread(1, SERVER_ADDRESS, request_handler)
    thread_server.start()
    # Managing usb events
    myRoom.start()
    while(True):
        try:
            val = int(input())
            if val == -1:            
                break
        except ValueError:
            print("--- Invalid command")
            pass
    myRoom.stop()
    thread_server.httpd.shutdown()

if __name__ == "__main__":
    main()

