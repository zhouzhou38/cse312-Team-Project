import os
import socketserver
import sys
import secrets
import bcrypt
from pymongo import MongoClient
import toolBox
import json
import hashlib
import base64

mongo_client = MongoClient()
mydb = mongo_client["CSE312db"]

user_list = mydb["user"]
moment_info = mydb['moment_info']
imageID_info = mydb['imageID']

chat_history = mydb['chat_history']

class MyTCPHandler(socketserver.BaseRequestHandler):

    ws_users = {}

    def handle(self):
        data = self.request.recv(1024)
        data_arr = data.split(b'/')
        print(data_arr)
        sys.stdout.flush()

        if data_arr[0] == b'GET ' and b' HTTP' == data_arr[1]:
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
            # print(userName)
            # print(password)
            if information is None:

                all_chat_history = {}
                for document in user_list.find():
                    all_chat_history[document['UserName'].decode()] = []
                for document in chat_history.find():
                    all_chat = document['all_chats']
                    all_chat[userName.decode()] = []
                    chat_history.update_one({"sender":document['sender']},{"$set":{"all_chats":all_chat}})
                chat_history.insert_one({"sender":userName.decode(), "all_chats":all_chat_history})

                f = open('wallpaper.jpg', 'rb')
                content = f.read()
                toolBox.inserUsertoDB(userName, password)
                user_list.update_one({'UserName': userName}, {'$set': {'head_image': content}})

                header = b"HTTP/1.1 301 Permanent Redirect\r\nContent-Length:0\r\nLocation:http://localhost:8080/\r\n\r\n"
                self.request.sendall(header)
            else:
                header = b"HTTP/1.1 301 Permanent Redirect\r\nContent-Length:0\r\nLocation:http://localhost:8080/Signup/?error=username\r\n\r\n"
                self.request.sendall(header)

        elif data_arr[0] == b'POST ' and data_arr[1] == b'profile HTTP':
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

                    header = b"HTTP/1.1 301 Moved Permanently\r\nContent-length: 0\r\nSet-Cookie: token=" + mytoken + b'; Max-Age=4000; HttpOnly\r\nLocation: http://localhost:8080/profile'
                    self.request.sendall(header)
                else:
                    header = b"HTTP/1.1 301 Permanent Redirect\r\nContent-Length:0\r\nLocation:http://localhost:8080/?error=password\r\n\r\n"
                    self.request.sendall(header)
            else:
                header = b"HTTP/1.1 301 Permanent Redirect\r\nContent-Length:0\r\nLocation:http://localhost:8080/?error=username\r\n\r\n"
                self.request.sendall(header)
        elif data_arr[0] == b'GET ' and b'profile' in data_arr[1]:
            print('enter here plz')
            sys.stdout.flush()
            # headerLst = data.split(b"\r\n")
            header_dict = toolBox.parse_to_dict(data)
            # print("header_dict :", header_dict)
            # sys.stdout.flush()
            userName = toolBox.find_userName(header_dict)
            # print("userName :", userName)
            # sys.stdout.flush()
            if userName is None:
                self.request.sendall(
                    "HTTP/1.1 301 Moved Permanently\r\neContent-Length: 0\r\nX-Content-Type-Options: "
                    "nosniff\r\nLocation:HTTP://localhost:8080/\r\n\r\n".encode())
            else:
                with open('HTMLtemplates/new_homepage.html', 'r') as f:
                    text = f.read()

                    # load friend list -> wang ------------------------------------------

                    content = text.encode()
                    friend_list_temp = ""
                    friend_list_starting_pos = content.find(b'<p hidden>friend list class start loop</p>')+len('<p hidden>friend list class start loop</p>')
                    friend_list_ending_pos = content.find(b'<p hidden>friend list class end loop</p>')
                    print("pos",friend_list_starting_pos,friend_list_ending_pos)
                    friend_list_js_temp = "<script>\n"
                    chat_box_temp = ""
                    i = 0
                    for user in user_list.find():
                        if user['UserName'] != userName.encode():
                            # display friend list template
                            friend_list_temp += "<button id=\"friend"+str(i)+"\" onclick=\"document.getElementById('chat"+str(i)+"').style.display='block';pass_friend"+str(i)+"_name()\" style=\"width:auto;\" class=\"button\">"+user["UserName"].decode()+"</button><br>\n"

                            # display friend name script template
                            friend_list_js_temp += 'function pass_friend'+str(i)+'_name(){\n'
                            friend_list_js_temp += 'document.getElementById("sendTo").value = document.getElementById("friend'+str(i)+'").innerHTML;\n'
                            friend_list_js_temp += '}\n'

                            chat_box_temp += '<div id="chat'+str(i)+'" class="modal">\n'
                            chat_box_temp += '<div class="imgcontainer" style="background:#F1D5EF">\n'
                            chat_box_temp += user['UserName'].decode('utf-8')+'\n'
                            chat_box_temp += '</div>\n'
                            chat_box_temp += '<div class="container" >\n'
                            chat_box_temp += '<div id="chat'+user['UserName'].decode('utf-8')+'" class="chatBox">\n'
                            chat_box_temp += '</div>\n\n'
                            chat_box_temp += '<div style="display: block;width: 100%;padding: 10px 100px;text-align: center;">\n'
                            chat_box_temp += '<textarea id="friendName_'+user['UserName'].decode()+'" name="message" required style="position: relative;margin-left: 0;display: inline-block;">\n'
                            chat_box_temp += 'Sending text...\n'
                            chat_box_temp += '</textarea>\n'
                            chat_box_temp += '<button onclick="sendMessage()">Send msg</button>'
                            chat_box_temp += '</div>\n'
                            chat_box_temp += '<br>\n'
                            chat_box_temp += '<button type="button" onclick="document.getElementById(\'chat'+str(i)+'\').style.display=\'none\'" class="cancelbtn">Cancel</button>\n'
                            chat_box_temp += '</div>\n'
                            chat_box_temp += '</div>\n\n'

                            i+=1

                    content = content.replace(content[friend_list_starting_pos:friend_list_ending_pos],friend_list_temp.encode())

                    friend_list_js_temp += '</script><br>\n'
                    friend_list_js_starting_pos = content.find(b"<p hidden>friend list js start loop</p>")+len(b"<p hidden>friend list js start loop</p>")
                    friend_list_js_ending_pos = content.find(b"<p hidden>friend list js end loop</p>")
                    content = content.replace(content[friend_list_js_starting_pos:friend_list_js_ending_pos],friend_list_js_temp.encode())

                    chat_box_starting_pos = content.find(b"<p hidden>chat box start loop</p>")+len(b"<p hidden>chat box start loop</p>")
                    chat_box_ending_pos = content.find(b"<p hidden>chat box end loop</p>")
                    content = content.replace(content[chat_box_starting_pos:chat_box_ending_pos],chat_box_temp.encode())

                    content = content.replace(b'<input type="text" id="me" value="',b'<input type="text" id="me" value="'+userName.encode())
                    # -------------------------------------------------------

                    text = content.decode('utf-8')
                    text = text.replace('{{username}}',userName)
                    del_idx_1 = text.find('{{start_moment}}')
                    del_idx_2 = text.find('{{end_moment}}')

                    empty_moment = b'<h1 style=\"text-align:center; color:#F1D5EF;\">Make first Post On The Moment!</h1>'

                    if moment_info.find_one({}) is None:
                        new_content = text[:del_idx_1] + empty_moment.decode('utf-8') + text[del_idx_2 + len('{{end_moment}}'):]
                        b_new_content = new_content.encode()
                        length_text = len(b_new_content)
                        byte_txt = (
                                "HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=UTF-8" + "\r\nContent-Length: ").encode()
                        self.request.sendall(byte_txt + str(length_text).encode() + (
                                '\r\nX-Content-Type-Options: nosniff' + '\r\n\r\n').encode() + b_new_content)

                    else:
                        # update the token on the index.html
                        # zeng moment template ---------------------------------------------------------------
                        contentList = moment_info.find({})
                        contentList = list(contentList)
                        advised_body = ''

                        for i in contentList:
                            # print('Id-username :', i['username'])
                            # print('len: ', len(i['comment']))

                            moment_template = text[del_idx_1 + len('{{start_moment}}'):del_idx_2]

                            sys.stdout.flush()
                            if len(i['comment']) != 0 and len(i['upload']) == 0:
                                # advised_body += i['username'] + ': '
                                # advised_body += i['comment'].decode('UTF-8')
                                image_id = i['id']
                                moment_template = moment_template.replace('user_image.jpg', 'user_image/user' + str(image_id) + '.jpg')
                                moment_template = moment_template.replace('{{post_username}}', i['username'])
                                moment_template = moment_template.replace('{{content_begin_here}}',
                                                                          i['comment'].decode('UTF-8'))
                                moment_template += '<hr>'
                                advised_body += moment_template
                                advised_body += '<br/>'
                                advised_body += '<br/>'
                            elif len(i['comment']) == 0 and len(i['upload']) != 0:
                                print('you should access here')
                                sys.stdout.flush()
                                image_id = i['id']
                                print('repaired ID :', image_id)
                                sys.stdout.flush()
                                moment_template = moment_template.replace('user_image.jpg', 'user_image/user' + str(image_id) + '.jpg')
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
                                # print('noway')
                                # sys.stdout.flush()
                                moment_template = moment_template.replace('{{post_username}}', i['username'])

                                image_id = i['id']
                                moment_template = moment_template.replace('user_image.jpg', 'user_image/user' + str(image_id) + '.jpg')
                                str_image_id = str(image_id)
                                revised = "\"" + "image/upload_image{{id}}.jpg" + "\""
                                revised = revised.replace('{{id}}', str_image_id)
                                sampleLink = "<img src= " + revised + " class=" + "\"" + "my_image" + "\"" + "/>"
                                combo_content = i['comment'].decode('UTF-8') + '<br>' + sampleLink
                                moment_template = moment_template.replace('{{content_begin_here}}', combo_content)
                                moment_template += '<hr>'
                                # print('path is ', sampleLink)
                                # sys.stdout.flush()
                                advised_body += moment_template
                                advised_body += '<br/>'
                                advised_body += '<br/>'

                        new_del_idx_1 = text.find('{{start_moment}}')
                        new_del_idx_2 = text.find('{{end_moment}}')
                        new_content = text[:new_del_idx_1 - 1] + advised_body + text[
                                                                                new_del_idx_2 + len('{{end_moment}}'):]
                        print("stop!!!!!!!!!!!!!!!!")
                        # ---------------------------------------------------------------------

                        b_new_content = new_content.encode()
                        length_text = len(b_new_content)

                        byte_txt = (
                                "HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=UTF-8" + "\r\nContent-Length: ").encode()
                        self.request.sendall(byte_txt + str(length_text).encode() + (
                                '\r\nX-Content-Type-Options: nosniff' + '\r\n\r\n').encode() + b_new_content)

        elif data_arr[0] == b'GET ' and data_arr[1] == b'style.css HTTP':
            print('starting request css')
            sys.stdout.flush()
            self.request.sendall(toolBox.css_sender('style.css'))
        elif data_arr[0] == b'GET ' and data_arr[1] == b'functions.js HTTP':
            print("doing js")
            header = "HTTP/1.1 200 OK\r\nContent-Type: text/javascript; charset=utf-8\r\nX-Content-Type-Options: nosniff\r\n"
            f = open('HTMLtemplates/functions.js', 'r')

            size = os.path.getsize("HTMLtemplates/functions.js")
            header = header + "Content-length: "
            header = header + str(size)
            header = header + "\r\n\r\n"
            for line in f:
                header = header + line
            dataToSend = header.encode()
            self.request.sendall(dataToSend)

        elif data_arr[0] == b'GET ' and b'sakura.jpg HTTP' in data_arr[1]:
            self.request.sendall(toolBox.image_sender('sakura.jpg'))

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
                imagedata = toolBox.findImage(totaldata,boundary,finalBoundary)
                filename = 'headImage/image' + userName + ".jpg"
                myimage = open(filename,'wb')
                myimage.write(imagedata)
                user_list.update_one({"UserName":userName.encode()},{'$set': {'head_image': imagedata}})
                header = b"HTTP/1.1 301 Moved Permanently\r\nContent-length: 0\r\nX-Content-Type-Options: nosniff\r\nLocation: http://localhost:8080/profile\r\n\r\n"
                self.request.sendall(header)
        elif data_arr[0] == b'GET ' and b'wallpaper.jpg HTTP' in data_arr[1]:
            self.request.sendall(toolBox.image_sender('wallpaper.jpg'))

        elif data_arr[0] == b'GET ' and data_arr[1] == b'websocket HTTP':
            token_start_pos = data.find(b"token=")+len(b"token=")
            token_end_pos = data[token_start_pos:].find(b"\r")+token_start_pos
            token = data[token_start_pos:token_end_pos]
            username = ""
            for document in user_list.find():
                if "cookie" in document:
                    if bcrypt.checkpw(token,document['cookie']):
                        username = document['UserName']
            if username == "":
                print("invalid cookie, should return 403 response")


            header = "HTTP/1.1 101 Switching Protocols\r\nConnection: Upgrade\r\nUpgrade: websocket\r\nSec-WebSocket-Accept: "
            start_pos = data.find(b"Sec-WebSocket-Key: ") + len(b"Sec-WebSocket-Key: ")
            end_pos = start_pos
            guid = b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
            for i in range(start_pos, len(data)):
                if data[i:i+1] == b'\r':
                    break
                else:
                    end_pos += 1
            key = data[start_pos:end_pos]
            toHash = key + guid
            hash_key = hashlib.sha1(toHash)
            hash_byte = hash_key.digest()
            base64_byte = base64.b64encode(hash_byte)
            header_byte = header.encode()
            header_byte += base64_byte + str.encode("\r\n\r\n")
            self.request.sendall(header_byte)

            MyTCPHandler.ws_users[username] = self

            while True:
                recv_bytes = self.request.recv(1024)

                if len(recv_bytes) > 1:

                    if recv_bytes[0] == 136:
                        MyTCPHandler.ws_users.pop(username)
                        print("username: ",username," is disconnected")
                        break

                    payload_len = recv_bytes[1]-128

                    if payload_len == 127:
                        actual_len = recv_bytes[9] + recv_bytes[8]*256 + recv_bytes[7] *65536+recv_bytes[6]*16777216 +recv_bytes[5]*4294967296+recv_bytes[4]
                        if actual_len > 1024:
                            # buffering data if we have byte not read yet
                            while (len(recv_bytes)-8) < actual_len:
                                recv_bytes += self.request.recv(1024)

                        start_pos = 112

                    elif payload_len == 126:
                        actual_len = recv_bytes[2]*256+recv_bytes[3]
                        if actual_len > 1016:
                            # buffering data if we have byte not read yet
                            while(len(recv_bytes)-8) < actual_len:
                                recv_bytes += self.request.recv(1024)
                        start_pos = 64
                    else:
                        actual_len = payload_len
                        start_pos = 48
                    recv_bin = ""

                    for b in recv_bytes:
                        recv_bin += '{0:08b}'.format(b)
                    mask = recv_bin[start_pos-32:start_pos]
                    payload_bin = ""

                    # mask payload
                    for i in range(start_pos,len(recv_bin)):
                        payload_bin += str(int(recv_bin[i])^int(mask[(i-start_pos)%32]))

                    chat_msg_bin = ''.join(format(ord(i), '08b') for i in '{"messageType":"chatMessage"')
                    offer_bin = ''.join(format(ord(i), '08b') for i in '{"messageType":"webRTC-offer"')
                    answer_bin = ''.join(format(ord(i), '08b') for i in '{"messageType":"webRTC-answer"')
                    cand_bin = ''.join(format(ord(i), '08b') for i in '{"messageType":"webRTC-candidate"')


                    # if payload is webRTC
                    if payload_bin.find(offer_bin) == 0 or payload_bin.find(answer_bin) == 0 or payload_bin.find(cand_bin) == 0:
                        print("video chat")
                        if payload_len == 127:
                            print("127")
                            lengthToSend = '{0:064b}'.format(actual_len)
                            frameToSend = "1000000101111111" + lengthToSend + payload_bin
                            bytesToSend = int(frameToSend, 2).to_bytes((len(frameToSend) + 7) // 8, byteorder='big')
                            bytesToSend = bytesToSend[:actual_len+10]
                            for k,v in MyTCPHandler.ws_users.items():
                                if k != username:
                                    print(username + " is sending to "+k)
                                    v.request.sendall(bytesToSend)
                        elif payload_len == 126:
                            print("126")
                            lengthToSend = '{0:016b}'.format(actual_len)
                            frameToSend = "1000000101111110" + lengthToSend + payload_bin
                            bytesToSend = int(frameToSend, 2).to_bytes((len(frameToSend) + 7) // 8, byteorder='big')
                            bytesToSend = bytesToSend[:actual_len+4]
                            for k,v in MyTCPHandler.ws_users.items():
                                if k != username:
                                    print(username + " is sending to "+k)
                                    v.request.sendall(bytesToSend)
                        else:
                            print("less than 126")
                            lengthToSend = '{0:08b}'.format(actual_len)
                            frameToSend = "10000001" + lengthToSend + payload_bin
                            bytesToSend = int(frameToSend, 2).to_bytes((len(frameToSend) + 7) // 8, byteorder='big')
                            bytesToSend = bytesToSend[:actual_len+2]
                            for k,v in MyTCPHandler.ws_users.items():
                                if k != username:
                                    print(username + " is sending to "+k)
                                    v.request.sendall(bytesToSend)
                    # if payload is chat message
                    elif payload_bin.find(chat_msg_bin) == 0:
                        #print("bin: ",payload_bin)

                        payload_msg = json.loads(int(payload_bin, 2).to_bytes((len(payload_bin) + 7) // 8, byteorder='big').decode('utf-8'))
                        print("payload_msg:",payload_msg)
                        sender = payload_msg['sender']
                        receiver = payload_msg['receiver']
                        message = self.escape_html(payload_msg['msg'].encode()).decode()
                        payload_msg['msg'] = message

                        for document in chat_history.find():
                            if document['sender'] == sender:
                                all_chats = document['all_chats']
                                friend_chat_history = all_chats[receiver]
                                friend_chat_history.append("0"+message)
                            if document['sender'] == receiver:
                                all_chats = document['all_chats']
                                friend_chat_history = all_chats[sender]
                                friend_chat_history.append("1"+message)

                        msg_bytes = json.dumps(payload_msg,default=str).encode()
                        payloadToSend = ""
                        for b in msg_bytes:
                            payloadToSend += '{0:08b}'.format(b)
                        new_data_len = len(json.dumps(payload_msg).encode())

                        if new_data_len >= 65536:
                            lengthToSend = '{0:064b}'.format(len(json.dumps(payload_msg).encode()))
                            frameToSend = "1000000101111111" + lengthToSend + payloadToSend
                            bytesToSend = int(frameToSend, 2).to_bytes((len(frameToSend) + 7) // 8, byteorder='big')
                            for k,v in MyTCPHandler.ws_users.items():
                                if k == sender:
                                    v.request.sendall(bytesToSend)
                                if k == receiver:
                                    v.request.sendall(bytesToSend)

                        elif new_data_len >= 126:
                            lengthToSend = '{0:016b}'.format(len(json.dumps(payload_msg).encode()))
                            frameToSend = "1000000101111110" + lengthToSend + payloadToSend
                            bytesToSend = int(frameToSend, 2).to_bytes((len(frameToSend) + 7) // 8, byteorder='big')
                            for k,v in MyTCPHandler.ws_users.items():
                                if k == sender:
                                    v.request.sendall(bytesToSend)
                                if k == receiver:
                                    v.request.sendall(bytesToSend)

                        else:
                            lengthToSend = '{0:08b}'.format(len(json.dumps(payload_msg).encode()))
                            frameToSend = "10000001" + lengthToSend + payloadToSend
                            bytesToSend = int(frameToSend, 2).to_bytes((len(frameToSend) + 7) // 8, byteorder='big')


                            for k,v in MyTCPHandler.ws_users.items():
                                if k == sender.encode():
                                    print("send",k)
                                    v.request.sendall(bytesToSend)
                                if k == receiver.encode():
                                    print("recv",k)
                                    v.request.sendall(bytesToSend)

                        for document in chat_history.find():
                            print("inserting: ",document['sender'],sender,receiver)
                            if document['sender'] == sender:
                                chats = document['all_chats']
                                chats[receiver].append("1"+message)
                                chat_history.update_one({"sender":sender},{"$set":{"all_chats":chats}})
                            if document['sender'] == receiver:
                                chats = document['all_chats']
                                chats[sender].append("0"+message)
                                chat_history.update_one({"sender":receiver},{"$set":{"all_chats":chats}})


                    else:
                        print("error 001")

        elif data_arr[0] == b'GET ' and b'chat-history' in data_arr[1]:
            token_start_pos = data.find(b"token=")+len(b"token=")
            token_end_pos = data[token_start_pos:].find(b"\r")+token_start_pos
            token = data[token_start_pos:token_end_pos]
            username = b""
            for document in user_list.find():
                if bcrypt.checkpw(token,document['cookie']):
                    username = document['UserName']

            if username == b"":
                self.request.sendall(toolBox.function_404('This does not exist!'))
            else:
                header = "HTTP/1.1 200 OK\r\nContent-Type:application/json;charset=utf-8\r\nX-Content-Type-Options: nosniff\r\n"
                chats = []
                # sender:chrome all_chats = {friend1:["0hello","1hi","1how are you","0im good"],friend2:["1im kylin"]}
                for document in chat_history.find():
                    print("for: ",document['sender'],username)
                    if document['sender'].encode() == username:
                        chats = document["all_chats"]
                print("sending chat to client",chats)
                json_chat = json.dumps(chats, default=str)
                header += "Content-length: "+str(len(json_chat)) + '\r\n\r\n'+json_chat
                self.request.sendall(header.encode())

        elif data_arr[0] == b'POST ' and data_arr[1] == b'createMoment HTTP':
            b_blankLine = b'\r\n\r\n'
            header_bytes = data.split(b_blankLine)[0]
            print('post_header :', header_bytes)
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
            # identify who post this
            identity_checker = False
            visitorName = toolBox.find_userName(res_dict)
            print("target_user :", visitorName)
            sys.stdout.flush()
            head_image = b''
            if visitorName is not None:
                identity_checker = True
                # print(list(user_list.find({})))
                sys.stdout.flush()
                user_info = user_list.find_one({'UserName': visitorName.encode()})
                # print('user_info:', user_info)
                # sys.stdout.flush()
                head_image = user_info['head_image']
                # print('image :', head_image)
                # sys.stdout.flush()

            print('id_checker :', identity_checker)
            sys.stdout.flush()
            if identity_checker:
                ContentOfBoundary = res_dict['Content-Type'].replace('multipart/form-data; boundary=', '')
                realContent = '--' + ContentOfBoundary + '\r\n'
                b_realContent = realContent.encode()
                b_requestLst = data.split(b_realContent)

                # delete header here
                b_requestLst.pop(0)

                # print('content here :', b_requestLst)
                sys.stdout.flush()

                content_dict = {'username': visitorName, 'head_image': head_image}
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
                # print('moment_info :', content_dict)
                sys.stdout.flush()
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

                    # print("result:", 'image/upload_image' + str(new_value) + '.jpg')
                sys.stdout.flush()
                with open('image/upload_image' + str(new_value) + '.jpg', 'wb') as f:
                    f.write(content_dict['upload'])
                with open('user_image/user' + str(new_value) + '.jpg', 'wb') as f1:
                    f1.write(content_dict['head_image'])

                content_dict['id'] = new_value
                sys.stdout.flush()
                moment_info.insert_one(content_dict)
                # print('dict :', content_dict)
                self.request.sendall(
                    "HTTP/1.1 301 Moved Permanently\r\neContent-Length: 0\r\nX-Content-Type-Options: "
                    "nosniff\r\nLocation:http://localhost:8080/profile\r\n\r\n".encode())
        elif data_arr[1] == b'image':
            print('preparing for images')
            sys.stdout.flush()
            if data_arr[0].find(b'..') > 0:
                print('upload image failed here')
                sys.stdout.flush()
                self.request.sendall(
                    "HTTP/1.1 404 Not Found\r\nContent-Type: text/plain; charset=UTF-8\r\nContent-Length: "
                    "36\r\nX-Content-Type-Options: nosniff\r\n\r\nThe requested content does not exist".encode())

            filename = data_arr[2].decode('UTF-8').replace(' HTTP', '')
            filename = 'image/' + filename
            print('filename :', filename)
            sys.stdout.flush()
            with open(filename, 'rb') as f:
                image = f.read()
                l_image = len(image)
                self.request.sendall(('HTTP/1.1 200 OK\r\nContent-Type: image/jpeg\r\nContent-Length: ' + str(
                    l_image) + '\r\nX-Content-Type-Options: nosniff' + "\r\n\r\n").encode() + image)
        elif data_arr[1] == b'user_image':
            print('preparing for head images')
            sys.stdout.flush()
            if data_arr[0].find(b'..') > 0:
                print('upload head image failed here')
                sys.stdout.flush()
                self.request.sendall(
                    "HTTP/1.1 404 Not Found\r\nContent-Type: text/plain; charset=UTF-8\r\nContent-Length: "
                    "36\r\nX-Content-Type-Options: nosniff\r\n\r\nThe requested content does not exist".encode())

            filename = data_arr[2].decode('UTF-8').replace(' HTTP', '')
            filename = 'user_image/' + filename
            print('filename :', filename)
            sys.stdout.flush()
            with open(filename, 'rb') as f:
                image = f.read()
                l_image = len(image)
                self.request.sendall(('HTTP/1.1 200 OK\r\nContent-Type: image/jpeg\r\nContent-Length: ' + str(
                    l_image) + '\r\nX-Content-Type-Options: nosniff' + "\r\n\r\n").encode() + image)

        elif data_arr[1] == b'logout HTTP':
            self.request.sendall(
                "HTTP/1.1 301 Moved Permanently\r\neContent-Length: 0\r\nX-Content-Type-Options: "
                "nosniff\r\nLocation:http://localhost:8080/\r\n\r\n".encode())
        else:

            self.request.sendall(toolBox.function_404('This does not exist!'))

    def escape_html(self, input):
        return input.replace(b'&', b'&amp').replace(b'<', b'&lt;').replace(b'>', b'&gt;')


if __name__ == '__main__':
    host = '0.0.0.0'
    port = 8080

    server = socketserver.ThreadingTCPServer((host, port), MyTCPHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        sys.exit(0)
