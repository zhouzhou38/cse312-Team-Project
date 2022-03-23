import hashlib
import json
import socketserver
import sys
import random
from pymongo import MongoClient
from base64 import b64encode,b64decode


class MyTCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        received_data = self.request.recv(1024)
        sys.stdout.flush()
        sys.stderr.flush()
        receivedStr = received_data.split(b'/')






if __name__ == '__main__':
    host = '0.0.0.0'
    port = 5454
    server = socketserver.ThreadingTCPServer((host, port), MyTCPHandler)
    server.serve_forever()