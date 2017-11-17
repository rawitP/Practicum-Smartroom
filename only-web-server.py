import http.server
import threading
import os
import urllib

# Constant Variable
SERVER_PORT = 30000
SERVER_ADDRESS = ('', SERVER_PORT)
ROOT_DIR = os.path.dirname(os.path.realpath(__file__))

def toBytes(data):
    return bytes(data, "utf-8")

class MyHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        path_split = self.path.split('?')
        print(path_split)
        try:
            if path_split[0].endswith('.html'):
                f = open(ROOT_DIR + path_split[0])
                self._set_headers()
                self.wfile.write(toBytes(f.read()))
                f.close()
                return
        except IOError:
            self.send_error(404, 'file not found')

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
        print("Starting serverThread:%d" % self.threadID)
        self.httpd.serve_forever()
        print("Exiting serverThread:%d" % self.threadID)

def main():
    request_handler = MyHTTPRequestHandler
    thread_server = serverThread(1, SERVER_ADDRESS, request_handler)
    thread_server.start()
    print('After serve_forever()')
    while True:
        val = int(input())
        if val == -1:
            thread_server.httpd.shutdown()
            thread_server.join()
            break

if __name__ == "__main__":
    main()
