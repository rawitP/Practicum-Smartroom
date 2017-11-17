import http.server
import threading
import testPackage

class MyHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        self._set_headers()
        self.wfile.write(b"<html><head><title>My Title</title></head>")
        self.wfile.write(bytes("<body><p>You accessed path: %s</p>" % self.path,"utf-8"))
        self.wfile.write(bytes("Light Value: %d" % testPackage.LIGHT_VALUE,"utf-8"))
        self.wfile.write(b"</body></html>")
        print("Sent light value")

    def do_POST(self):
        testPackage.increase_light()
        self._set_headers()
        self.wfile.write(b"Success")
        print("Increasing Light value")

class serverThread (threading.Thread) :
    def __init__(self, threadID):
        threading.Thread.__init__(self)
        self.threadID = threadID

    def run(self):
        print ("Starting serverThread: %d" % self.threadID)
        httpd = http.server.HTTPServer(server_address, request_handler)
        httpd.serve_forever()
        print ("Exiting thread")

port = 30000
server_address = ('',port)
request_handler = MyHTTPRequestHandler
thread_server = serverThread(1)
thread_server.start()
testPackage.polling_forever()
print('After serve_forever()')
