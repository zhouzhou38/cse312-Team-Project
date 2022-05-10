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
moment_info = mydb['moment_info']


class MyTCPHandler(socketserver.BaseRequestHandler):

    def handle(self):
        data = self.request.recv(1024)
        data_arr = data.split(b'/')
        print(data_arr[1])
        sys.stdout.flush()

        if data_arr[0] == b'GET ' and b' HTTP' == data_arr[1]:
            # load home page localhost:5454
            f = open("HTMLtemplates/new_homepage.html", 'rb')
            content = f.read()
            start_idx = content.find(b'{{start_moment}}')
            end_idx = content.find(b'{{end_moment}}')
            print('start_idx :', start_idx)
            sys.stdout.flush()
            if moment_info.find({}) is None:
                print('nothing post here')
                sys.stdout.flush()
                empty_moment = b''
                content = content[:start_idx] + empty_moment + content[end_idx + len(b'{{end_moment}}'):]

            self.request.sendall(toolBox.general_sender("HTMLtemplates/new_homepage.html", content))

        elif data_arr[0] == b'GET ' and data_arr[1] == b'Signup HTTP':
            # print('in here')
            # sys.stdout.flush()
            f = open("HTMLtemplates/Signup.html", 'rb')
            content = f.read()
            # print(content)
            # sys.stdout.flush()
            header = b"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nX-Content-Type-Options: nosniff\r\n"
            header += str(os.path.getsize("HTMLtemplates/Signup.html")).encode()
            header += b'\r\n\r\n'
            header += content
            self.request.sendall(header)

        elif data_arr[0] == b'POST ' and b'Signup' in data_arr[1]:
            boundary = toolBox.findBoundary(data)
            finalBoundary = boundary + b'--'
            totaldata = data
            while totaldata.find(finalBoundary) == -1:
                totaldata += self.request.recv(1024)
            userName = toolBox.findUserName(totaldata, boundary)
            password = toolBox.findUserPassword(totaldata, boundary)
            information = toolBox.findUserfromDB(userName)

            if information is None:
                toolBox.inserUsertoDB(userName, password)
                header = b"HTTP/1.1 301 Permanent Redirect\r\nContent-Length:0\r\nLocation:http://localhost:8080/\r\n\r\n"
                self.request.sendall(header)
            else:
                header = b"HTTP/1.1 301 Permanent Redirect\r\nContent-Length:0\r\nLocation:http://localhost:8080/Signup/?error=username\r\n\r\n"
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
            userName = toolBox.findUserName(totaldata, boundary)
            password = toolBox.findUserPassword(totaldata, boundary)
            information = toolBox.findUserfromDB(userName)
            if information is not None:
                pwd = information['Password']
                if bcrypt.checkpw(password, pwd):
                    # localhost:5454/?name=username
                    mytoken = secrets.token_hex(16).encode()
                    tokenhashed = bcrypt.hashpw(mytoken, bcrypt.gensalt())
                    user_list.update_one({"UserName": userName}, {'$set': {'cookie': tokenhashed}})
                    f = open("HTMLtemplates/new_homepage.html", 'rb')
                    content = f.read()
                    header = b"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nX-Content-Type-Options: nosniff\r\nSet-Cookie: token=" + mytoken + b'; Max-Age=4000; HttpOnly\r\nContent-length:'
                    header += str(os.path.getsize("HTMLtemplates/new_homepage.html")).encode()
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
            # localhost:5454/kylin/friend_request_box
            # localhost:5454/zhou/friend_request_box
            username = data_arr[1].split(b' ')[0]
            '''
            load friend_request_box base on username
            return database from username, transfer to html
            '''
        elif data_arr[0] == b'GET ' and data_arr[1] == b'style.css HTTP':
            print('starting request css')
            sys.stdout.flush()
            self.request.sendall(toolBox.css_sender('style.css'))

        elif data_arr[0] == b'GET ' and b'sakura.jpg HTTP' in data_arr[1]:
            self.request.sendall(toolBox.image_sender('sakura.jpg'))

        elif data_arr[0] == b'GET ' and data_arr[1] == b'direct_message_box HTTP':
            pass
        elif data_arr[0] == b'GET ' and data_arr[1] == b'moment_box HTTP':
            pass
        else:
            self.request.sendall(toolBox.function_404('This does not exist!'))


if __name__ == '__main__':
    host = '0.0.0.0'
    port = 8081

    server = socketserver.ThreadingTCPServer((host, port), MyTCPHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        sys.exit(0)
