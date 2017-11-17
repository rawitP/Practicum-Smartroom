import http.server
import threading
import os
import urllib
import practicumPackage

# Constant Variable
SERVER_PORT = 30000
SERVER_ADDRESS = ('',SERVER_PORT)
ROOT_DIR = os.path.dirname(os.path.realpath(__file__))

def toBytes(data):
    return bytes(data, "utf-8")

class MyHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        self._set_headers()
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
        print ("Starting serverThread: %d" % self.threadID)
        self.httpd.serve_forever()
        print ("Exiting thread")

def main():
    request_handler = MyHTTPRequestHandler
    thread_server = serverThread(1, SERVER_ADDRESS, request_handler)
    thread_server.start()
    print('After serve_forever()')
    # Managing usb events
    practicumPackage.mcu_thread.start()
    while(True):
        val = int(input())
        if val == -1:
            # Stop all threads
            practicumPackage.mcu_thread.stop()
            thread_server.httpd.shutdown()
            break
    practicumPackage.mcu_thread.join()

if __name__ == "__main__":
    main()

