import os
import socketserver
import sys
import secrets
import bcrypt
from pymongo import MongoClient
import toolBox

mongo_client = MongoClient('mongo')
mydb = mongo_client["CSE312db"]

user_list = mydb["user"]
moment_info = mydb['moment_info']
chat_history = mydb['chat_history']


class MyTCPHandler(socketserver.BaseRequestHandler):

    def handle(self):
        data = self.request.recv(1024)
        data_arr = data.split(b'/')
        print(data_arr[1])
        sys.stdout.flush()

        if data_arr[0] == b'GET ' and b' HTTP' == data_arr[1]:
            # load home page localhost:5454
            # f = open("HTMLtemplates/new_homepage.html", 'rb')
            # content = f.read()
            # start_idx = content.find(b'{{start_moment}}')
            # end_idx = content.find(b'{{end_moment}}')
            # print('start_idx :', start_idx)
            # sys.stdout.flush()
            # if moment_info.find({}) is None:
            #     print('nothing post here')
            #     sys.stdout.flush()
            #     empty_moment = b''
            #     content = content[:start_idx] + empty_moment + content[end_idx + len(b'{{end_moment}}'):]


            f = open("HTMLtemplates/SignIn.html",'rb')
            content = f.read()
            header = b"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nX-Content-Type-Options: nosniff\r\nContent-length:"
            header += str(os.path.getsize("HTMLtemplates/SignIn.html")).encode()
            header += b'\r\n\r\n'
            header += content
            self.request.sendall(header)

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
            print('post Signup')
            boundary = toolBox.findBoundary(data)
            finalBoundary = boundary + b'--'
            totaldata = data
            while totaldata.find(finalBoundary) == -1:
                totaldata += self.request.recv(1024)
            userName = toolBox.findUserName(totaldata, boundary)
            password = toolBox.findUserPassword(totaldata, boundary)
            information = toolBox.findUserfromDB(userName)
            print(userName)
            print(password)
            if information is None:
                toolBox.inserUsertoDB(userName, password)
                print('hello')
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
            while totaldata.find(finalBoundary) == -1:
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
                    start_idx = content.find(b'{{start_moment}}')
                    end_idx = content.find(b'{{end_moment}}')
                    print('start_idx :', start_idx)
                    sys.stdout.flush()
                    if moment_info.find_one({}) is None:
                        print('nothing post here')
                        sys.stdout.flush()
                        empty_moment = b'<h1 style=\"text-align:center; color:#F1D5EF;\">Make first Post On The Moment!</h1>'
                        content = content[:start_idx] + empty_moment + content[end_idx + len(b'{{end_moment}}'):]

                    # load profile  -> zhou


                    # load moment  -> zeng


                    # load friend list -> wang
                    friend_list_temp = ""
                    friend_list_starting_pos = content.find('<p hidden>friend list class start pos</p>')+len('<p hidden>friend list class start pos</p>')
                    friend_list_ending_pos = content.find('<p hidden>friend list class end pos</p>')
                    #<button id="friend1" onclick="document.getElementById('chat01').style.display='block';pass_friend1_name()" style="width:auto;" class="button">Friend1</button><br>
                    i = 0

                    for user in user_list.find():
                        friend_list_temp += "<button id=\"friend"+str(i)+"\" onclick=\"document.getElementById('chat"+str(i)+"').style.display='block';pass_friend"+str(i)+"_name()\" style=\"width:auto;\" class=\"button\">"+user["username"]+"</button><br>\n"
                    content = content.replace(content[friend_list_starting_pos:friend_list_ending_pos])





                    # self.request.sendall(toolBox.general_sender("HTMLtemplates/new_homepage.html", content))

                    header = b"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nX-Content-Type-Options: nosniff\r\nSet-Cookie: token=" + mytoken + b'; Max-Age=4000; HttpOnly\r\nContent-length:'
                    header += str(len(content)).encode()
                    header += b'\r\n\r\n'
                    header += content
                    self.request.sendall(header)
                else:
                    header = b"HTTP/1.1 301 Permanent Redirect\r\nContent-Length:0\r\nLocation:http://localhost:8080/?error=password\r\n\r\n"
                    self.request.sendall(header)
            else:
                header = b"HTTP/1.1 301 Permanent Redirect\r\nContent-Length:0\r\nLocation:http://localhost:8080/?error=username\r\n\r\n"
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

        elif data_arr[0] == b'GET ' and b'wallpaper.jpg HTTP' in data_arr[1]:
            self.request.sendall(toolBox.image_sender('wallpaper.jpg'))
        elif data_arr[0] == b'GET ' and data_arr[1] == b'direct_message_box HTTP':
            pass
        elif data_arr[0] == b'GET ' and data_arr[1] == b'moment_box HTTP':
            pass
        elif data_arr[0] == b'POST ' and data_arr[1] == b'createMoment HTTP':
            b_blankLine = b'\r\n\r\n'
            header_bytes = data.split(b_blankLine)[0]
            print(header_bytes)
            sys.stdout.flush()
            res_dict = toolBox.parse_to_dict(header_bytes)
            contentLen = int(res_dict['Content-Length'])
            contentLen = contentLen + len(header_bytes) - len(data)
            while contentLen > 0:
                new_recv = self.request.recv(1024)
                data += new_recv
                contentLen -= len(new_recv)
            # print('whole data_recv :', data)
            # sys.stdout.flush()

            ContentOfBoundary = res_dict['Content-Type'].replace('multipart/form-data; boundary=', '')
            realContent = '--' + ContentOfBoundary + '\r\n'
            b_realContent = realContent.encode()
            b_requestLst = data.split(b_realContent)

            # delete header here
            b_requestLst.pop(0)

            print('content here :', b_requestLst)
            sys.stdout.flush()
            content_dict = {}
            # verify user's identity throught the cookie token
            for b_request in b_requestLst:
                # parse the comment,and get the content of the comment
                if b_requestLst.index(b_request) == 1:
                    split_index = b_request.find(b_blankLine)
                    subHeaders = 'comment'
                    subBody = b_request[split_index + 4:len(b_request)]
                    # replace the character here !!!! ,prevent http injection
                    subBody = subBody.replace(b'&', b'&amp')
                    subBody = subBody.replace(b'<', b'&lt')
                    subBody = subBody.replace(b'>', b'&gt')
                    subBody = subBody.replace(b'\r\n', b'<br>')
                else:
                    end_index = b_request.find(b'\r\n------')
                    split_index = b_request.find(b_blankLine)
                    subHeaders = 'upload'
                    subBody = b_request[split_index + 4:end_index]

                content_dict[subHeaders] = subBody
                # content_dict['username'] = visitorName
            print('moment_info :', content_dict)
            sys.stdout.flush()
            moment_info.insert_one(content_dict)
        else:
            self.request.sendall(toolBox.function_404('This does not exist!'))


if __name__ == '__main__':
    host = '0.0.0.0'
    port = 8080

    server = socketserver.ThreadingTCPServer((host, port), MyTCPHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        sys.exit(0)
