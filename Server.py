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
imageID_info = mydb['imageID']


class MyTCPHandler(socketserver.BaseRequestHandler):

    def handle(self):
        global myimage
        data = self.request.recv(1024)
        data_arr = data.split(b'/')
        if data_arr[0] == b'GET ' and b' HTTP' == data_arr[1]:
            f = open("HTMLtemplates/SignIn.html", 'rb')
            content = f.read()
            header = b"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nX-Content-Type-Options: nosniff\r\nContent-length:"
            header += str(os.path.getsize("HTMLtemplates/SignIn.html")).encode()
            header += b'\r\n\r\n'
            header += content
            self.request.sendall(header)

        elif data_arr[0] == b'GET ' and data_arr[1] == b'Signup HTTP':

            f = open("HTMLtemplates/Signup.html", 'rb')
            content = f.read()

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
                f = open('wallpaper.jpg', 'rb')
                content = f.read()
                toolBox.inserUsertoDB(userName, password)
                user_list.update_one({'UserName': userName}, {'$set': {'head_image': content}})


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

                    # f = open("HTMLtemplates/new_homepage.html", 'rb')
                    # content = f.read()
                    # start_idx = content.find(b'{{start_moment}}')
                    # end_idx = content.find(b'{{end_moment}}')
                    # print('start_idx :', start_idx)
                    # sys.stdout.flush()
                    # if moment_info.find_one({}) is None:
                    #     print('nothing post here')
                    #     sys.stdout.flush()
                    #     empty_moment = b'<h1 style=\"text-align:center; color:#F1D5EF;\">Make first Post On The Moment!</h1>'
                    #     content = content[:start_idx] + empty_moment + content[end_idx + len(b'{{end_moment}}'):]
                    # else:
                    #     # for moment in list(moment_info.find({})):
                    #     print(list(moment_info.find({})))
                    #     sys.stdout.flush()
                    # # self.request.sendall(toolBox.general_sender("HTMLtemplates/new_homepage.html", content))
                    # header = b"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nX-Content-Type-Options: nosniff\r\nSet-Cookie: token=" + mytoken + b'; Max-Age=4000; HttpOnly\r\nContent-length:'
                    # header += str(len(content)).encode()
                    # header += b'\r\n\r\n'
                    # header += content
                    # self.request.sendall(header)

                    header = b"HTTP/1.1 301 Moved Permanently\r\nContent-length: 0\r\nSet-Cookie: token=" + mytoken + b'; Max-Age=4000; HttpOnly\r\nLocation: http://localhost:8080/profile'
                    self.request.sendall(header)
                else:
                    header = b"HTTP/1.1 301 Permanent Redirect\r\nContent-Length:0\r\nLocation:http://localhost:8080/?error=password\r\n\r\n"
                    self.request.sendall(header)
            else:
                header = b"HTTP/1.1 301 Permanent Redirect\r\nContent-Length:0\r\nLocation:http://localhost:8080/?error=username\r\n\r\n"
                self.request.sendall(header)

        elif data_arr[0] == b'GET ' and b'profile' in data_arr[1]:

            # headerLst = data.split(b"\r\n")
            header_dict = toolBox.parse_to_dict(data)

            userName = toolBox.find_userName(header_dict)

            if userName is None:
                self.request.sendall(
                    "HTTP/1.1 301 Moved Permanently\r\nContent-Length: 0\r\nLocation:http://localhost:8080/\r\n\r\n".encode())
            else:
                with open('HTMLtemplates/new_homepage.html', 'r') as f:
                    text = f.read()
                del_idx_1 = text.find('{{start_moment}}')
                del_idx_2 = text.find('{{end_moment}}')
                text = text.replace('{{username}}', userName)
                if moment_info.find_one({}) is None:
                    new_content = text[:del_idx_1] + '' + text[del_idx_2 + len('{{end_moment}}'):]
                    b_new_content = new_content.encode()
                    length_text = len(b_new_content)
                    byte_txt = (
                            "HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=UTF-8" + "\r\nContent-Length: ").encode()
                    self.request.sendall(byte_txt + str(length_text).encode() + (
                            '\r\nX-Content-Type-Options: nosniff' + '\r\n\r\n').encode() + b_new_content)

                else:
                    # update the token on the index.html
                    contentList = moment_info.find({})
                    contentList = list(contentList)
                    advised_body = ''
                    for i in contentList:

                        moment_template = text[del_idx_1 + len('{{start_moment}}'):del_idx_2]
                        if len(i['comment']) != 0 and len(i['upload']) == 0:

                            moment_template = moment_template.replace('{{post_username}}', i['username'])
                            moment_template = moment_template.replace('{{content_begin_here}}',
                                                                      i['comment'].decode('UTF-8'))
                            moment_template += '<hr>'
                            advised_body += moment_template
                            advised_body += '<br/>'
                            advised_body += '<br/>'
                        elif len(i['comment']) == 0 and len(i['upload']) != 0:

                            image_id = i['id']
                            str_image_id = str(image_id)
                            moment_template = moment_template.replace('{{post_username}}', i['username'])
                            revised = "\"" + "image/upload_image{{id}}.jpg" + "\""
                            revised = revised.replace('{{id}}', str_image_id)
                            sampleLink = "<img src= " + revised + " class=" + "\"" + "my_image" + "\"" + "/>"
                            moment_template = moment_template.replace('{{content_begin_here}}', sampleLink)
                            moment_template += '<hr>'
                            advised_body += moment_template
                            advised_body += '<br/>'
                            advised_body += '<br/>'
                        elif len(i['comment']) != 0 and len(i['upload']) != 0:

                            moment_template = moment_template.replace('{{post_username}}', i['username'])

                            image_id = i['id']
                            str_image_id = str(image_id)
                            revised = "\"" + "image/upload_image{{id}}.jpg" + "\""
                            revised = revised.replace('{{id}}', str_image_id)
                            sampleLink = "<img src= " + revised + " class=" + "\"" + "my_image" + "\"" + "/>"
                            combo_content = i['comment'].decode('UTF-8') + '<br>' + sampleLink
                            moment_template = moment_template.replace('{{content_begin_here}}', combo_content)
                            moment_template += '<hr>'

                            advised_body += moment_template
                            advised_body += '<br/>'
                            advised_body += '<br/>'

                    new_del_idx_1 = text.find('{{start_moment}}')
                    new_del_idx_2 = text.find('{{end_moment}}')
                    new_content = text[:new_del_idx_1 - 1] + advised_body + text[new_del_idx_2 + len('{{end_moment}}'):]
                    b_new_content = new_content.encode()
                    length_text = len(b_new_content)

                    byte_txt = (
                            "HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=UTF-8" + "\r\nContent-Length: ").encode()
                    self.request.sendall(byte_txt + str(length_text).encode() + (
                            '\r\nX-Content-Type-Options: nosniff' + '\r\n\r\n').encode() + b_new_content)

        elif data_arr[0] == b'GET ' and data_arr[1] == b'style.css HTTP':

            self.request.sendall(toolBox.css_sender('style.css'))

        elif data_arr[0] == b'GET ' and b'sakura.jpg HTTP' in data_arr[1]:
            self.request.sendall(toolBox.image_sender('sakura.jpg'))

        elif data_arr[0] == b'GET ' and b'wallpaper.jpg HTTP' in data_arr[1]:
            self.request.sendall(toolBox.image_sender('wallpaper.jpg'))
        elif data_arr[0] == b'GET ' and b'user_head.jpg' in data_arr[1]:
            # headerLst = data.split(b"\r\n")
            header_dict = toolBox.parse_to_dict(data)
            userName = toolBox.find_userName(header_dict)
            if userName is None:
                self.request.sendall(
                    "HTTP/1.1 301 Moved Permanently\r\nContent-Length: 0\r\nLocation:http://localhost:8080/\r\n\r\n".encode())
            else:
                filename = 'headImage/image' + userName + ".jpg"
                try:
                    myimage = open(filename)
                    self.request.sendall(toolBox.image_sender(filename))
                except:
                    myuser = user_list.find_one({"UserName":userName.encode()})
                    image = myuser["head_image"]
                    f = open(filename,'wb')
                    f.write(image)
                    self.request.sendall(toolBox.image_sender(filename))


        elif data_arr[0] == b'GET ' and data_arr[1] == b'direct_message_box HTTP':
            pass
        elif data_arr[0] == b'GET ' and data_arr[1] == b'moment_box HTTP':
            pass
        elif data_arr[0] == b'POST ' and data_arr[1] == b'changeImage HTTP':

            header_dict = toolBox.parse_to_dict(data)
            userName = toolBox.find_userName(header_dict)
            if userName is None:
                self.request.sendall(
                    "HTTP/1.1 301 Moved Permanently\r\nContent-Length: 0\r\nLocation:http://localhost:8080/\r\n\r\n".encode())
            else:
                boundary = toolBox.findBoundary(data)
                finalBoundary = boundary + b'--'
                totaldata = data
                while totaldata.find(finalBoundary) == -1:
                    totaldata += self.request.recv(1024)
                imagedata = toolBox.findUserName(totaldata,boundary)
                filename = 'headImage/image' + userName + ".jpg"
                myimage = open(filename,'wb')
                myimage.write(imagedata)
                user_list.update_one({"UserName":userName.encode()},{'$set': {'head_image': imagedata}})
                infor = "Update Your image Success"
                self.request.sendall(
                    'HTTP/1.1 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\nContent-length: {}\r\n\r\n{}'.format(
                        len(infor.encode()), infor).encode())

        elif data_arr[0] == b'POST ' and data_arr[1] == b'createMoment HTTP':
            b_blankLine = b'\r\n\r\n'
            header_bytes = data.split(b_blankLine)[0]
            res_dict = toolBox.parse_to_dict(header_bytes)
            contentLen = int(res_dict['Content-Length'])
            contentLen = contentLen + len(header_bytes) - len(data)
            while contentLen > 0:
                new_recv = self.request.recv(1024)
                data += new_recv
                contentLen -= len(new_recv)

            visitorName = ''
            cookieDic = {}
            CookieLst = (res_dict['Cookie']).split(';')
            for i in CookieLst:
                i = i.strip()
                a = i.split('=')
                cookieDic[a[0]] = a[1]
            identity_checker = False

            for i in list(user_list.find({})):

                if 'cookie' in i and 'token' in cookieDic:

                    if bcrypt.checkpw(cookieDic['token'].encode(), i['cookie']):

                        identity_checker = True
                        visitorName = i['UserName'].decode()
                        visitorName = visitorName.replace('&', '&amp')
                        visitorName = visitorName.replace('<', '&lt')
                        visitorName = visitorName.replace('>', '&gt')
                        visitorName = visitorName.replace('\r\n', '<br>')

            if identity_checker:
                ContentOfBoundary = res_dict['Content-Type'].replace('multipart/form-data; boundary=', '')
                realContent = '--' + ContentOfBoundary + '\r\n'
                b_realContent = realContent.encode()
                b_requestLst = data.split(b_realContent)

                # delete header here
                b_requestLst.pop(0)

                content_dict = {'username': visitorName}
                # verify user's identity through the cookie token

                for b_request in b_requestLst:
                    # parse the comment,and get the content of the comment
                    if b_requestLst.index(b_request) == 0:
                        split_index = b_request.find(b_blankLine)
                        subHeaders = 'comment'
                        subBody = b_request[split_index + 4:len(b_request) - 2]
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
                # moment_info.insert_one(content_dict)
                # set identity for images
                if imageID_info.find_one({}) is None:
                    imageID_info.insert_one({'id': 1})
                    imageID_info.update_one({'id': 1}, {'$set': {'apple': 8}})
                    new_value = 1
                else:
                    dictLst = imageID_info.find()
                    id_dict = dictLst[0]
                    id_value = id_dict['id']
                    new_value = id_value + 1
                    imageID_info.update_one({'apple': 8}, {'$set': {'id': new_value}})

                with open('image/upload_image' + str(new_value) + '.jpg', 'wb') as f:
                    f.write(content_dict['upload'])

                content_dict['id'] = new_value
                moment_info.insert_one(content_dict)
                self.request.sendall(
                    "HTTP/1.1 301 Moved Permanently\r\neContent-Length: 0\r\nX-Content-Type-Options: "
                    "nosniff\r\nLocation:http://localhost:8080/profile\r\n\r\n".encode())

        elif data_arr[1] == b'image':
            if data_arr[0].find(b'..') > 0:
                self.request.sendall(
                    "HTTP/1.1 404 Not Found\r\nContent-Type: text/plain; charset=UTF-8\r\nContent-Length: "
                    "36\r\nX-Content-Type-Options: nosniff\r\n\r\nThe requested content does not exist".encode())

            filename = data_arr[2].decode('UTF-8').replace(' HTTP', '')
            filename = 'image/' + filename
            with open(filename, 'rb') as f:
                image = f.read()
                l_image = len(image)
                self.request.sendall(('HTTP/1.1 200 OK\r\nContent-Type: image/jpeg\r\nContent-Length: ' + str(
                    l_image) + '\r\nX-Content-Type-Options: nosniff' + "\r\n\r\n").encode() + image)

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
