import base64
import binascii
import hashlib
import json
import os
import socketserver

import sys
import time

import pymongo

from bson import json_util

client = pymongo.MongoClient()


class MyTCPHandler(socketserver.BaseRequestHandler):

    def handle(self):
        data = self.request.recv(1024)


        data_arr = data.split(b'/')

        if data_arr[0] == b'GET ' and data_arr[1] == b' HTTP':
        # load home page localhost:5454
            f = open("templates/index.html",'rb')
            content = f.read()
            header = b"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nX-Content-Type-Options: nosniff\r\n"
            header += str(os.path.getsize("templates/index.html")).encode()
            header += b'\r\n\r\n'
            header += content
            self.request.sendall(header)

        elif data_arr[0] == b'GET ' and data_arr[1] == b'signUp HTTP':
            f = open("templates/signUp.html",'rb')
            content = f.read()
            header = b"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nX-Content-Type-Options: nosniff\r\n"
            header += str(os.path.getsize("templates/signUp.html")).encode()
            header += b'\r\n\r\n'
            header += content
            self.request.sendall(header)

        elif data_arr[0] == b'POST ' and data_arr[1] == b'Signup HTTP':
            pass
            '''
            1. verify username is exist on our database
            2. If not exist, load username and password to database.
               Redirect to home page
               Else exist, send an error 
            '''

        elif data_arr[0] == b'GET ' and data_arr[1] == b'Profile HTTP':
            pass
            # localhost:5454/?name=username




if __name__ == '__main__':
    host = '0.0.0.0'
    port = 5454

    server = socketserver.ThreadingTCPServer((host, port), MyTCPHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        sys.exit(0)