import os
import socketserver
import sys
import secrets
import bcrypt
from pymongo import MongoClient
import toolBox

mongo_client = MongoClient('localhost')
mydb = mongo_client["CSE312db"]
user_list = mydb["user"]


class MyTCPHandler(socketserver.BaseRequestHandler):

    def handle(self):
        data = self.request.recv(1024)
        data_arr = data.split(b'/')
        if data_arr[0] == b'GET ' and b' ' in data_arr[1]:
            # load home page localhost:5454

            f = open("templates/index.html",'rb')
            content = f.read()
            header = b"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nX-Content-Type-Options: nosniff\r\n"
            header += str(os.path.getsize("templates/index.html")).encode()
            header += b'\r\n\r\n'
            header += content
            self.request.sendall(header)

        elif data_arr[0] == b'GET ' and b'Signup' in data_arr[1]:
            f = open("templates/SignUp.html",'rb')
            content = f.read()
            header = b"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nX-Content-Type-Options: nosniff\r\n"
            header += str(os.path.getsize("templates/SignUp.html")).encode()
            header += b'\r\n\r\n'
            header += content
            self.request.sendall(header)

        elif data_arr[0] == b'POST ' and b'Signup' in data_arr[1]:
            boundary = toolBox.findBoundary(data)
            finalBoundary = boundary + b'--'
            totaldata = data
            while (totaldata.find(finalBoundary) == -1):
                totaldata += self.request.recv(1024)
            userName = toolBox.findUserName(totaldata,boundary)
            password = toolBox.findUserPassword(totaldata,boundary)
            information = toolBox.findUserfromDB(userName)

            if information is None:
                toolBox.inserUsertoDB(userName,password)
                header = b"HTTP/1.1 301 Permanent Redirect\r\nContent-Length:0\r\nLocation:http://localhost:5454/\r\n\r\n"
                self.request.sendall(header)
            else:
                header = b"HTTP/1.1 301 Permanent Redirect\r\nContent-Length:0\r\nLocation:http://localhost:5454/Signup/?error=username\r\n\r\n"
                self.request.sendall(header)
            '''
            1. verify username is exist on our database
            2. If not exist, load username and password to database.
               Redirect to home page
               Else exist, send an error 
            '''

        elif data_arr[0] == b'POST ' and b'profile' in data_arr[1]:
            boundary = toolBox.findBoundary(data)
            finalBoundary = boundary + b'--'
            totaldata = data
            while (totaldata.find(finalBoundary) == -1):
                totaldata += self.request.recv(1024)
            userName = toolBox.findUserName(totaldata,boundary)
            password = toolBox.findUserPassword(totaldata,boundary)
            information = toolBox.findUserfromDB(userName)
            if information is not None:
                pwd = information['Password']
                if bcrypt.checkpw(password,pwd):
                    # localhost:5454/?name=username
                    mytoken = secrets.token_hex(16).encode()
                    tokenhashed = bcrypt.hashpw(mytoken,bcrypt.gensalt())
                    user_list.update_one({"UserName":userName},{'$set':{'cookie': tokenhashed}})
                    f = open("templates/homepage.html", 'rb')
                    content = f.read()
                    header = b"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nX-Content-Type-Options: nosniff\r\nSet-Cookie: token=" + mytoken + b'; Max-Age=4000; HttpOnly\r\nContent-length:'
                    header += str(os.path.getsize("templates/homepage.html")).encode()
                    header += b'\r\n\r\n'
                    header += content
                    self.request.sendall(header)
                else:
                    header = b"HTTP/1.1 301 Permanent Redirect\r\nContent-Length:0\r\nLocation:http://localhost:5454/?error=password\r\n\r\n"
                    self.request.sendall(header)
            else:
                header = b"HTTP/1.1 301 Permanent Redirect\r\nContent-Length:0\r\nLocation:http://localhost:5454/?error=username\r\n\r\n"
                self.request.sendall(header)

        elif data_arr[0] == b'GET ' and data_arr[2] == b'friend_request_box HTTP':
            #localhost:5454/kylin/friend_request_box
            #localhost:5454/zhou/friend_request_box
            username = data_arr[1].split(b' ')[0]
            '''
            load friend_request_box base on username
            return database from username, transfer to html
            '''

        elif data_arr[0] == b'GET ' and data_arr[1] == b'direct_message_box HTTP':
            pass
        elif data_arr[0] == b'GET ' and data_arr[1] == b'moment_box HTTP':
            pass



if __name__ == '__main__':
    host = '0.0.0.0'
    port = 5454

    server = socketserver.ThreadingTCPServer((host, port), MyTCPHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        sys.exit(0)