import bcrypt
from pymongo import MongoClient
import os
import sys

mongo_client = MongoClient("mongo")
mydb = mongo_client["CSE312db"]
user_list = mydb["user"]

def findImage(receivedStr, boundary,finalBoundary):
    boundaryIn = receivedStr.find(boundary)
    userName = receivedStr[boundaryIn + len(boundary):]
    rnindex = userName.find(b'\r\n\r\n')
    userName = userName[rnindex + len(b'\r\n\r\n'):]
    rnfinalIndex = userName.find(finalBoundary)
    # obtain UserName
    image = userName[:rnfinalIndex-2]
    return image

def findBoundary(receivedStr):
    boundary = receivedStr
    boundary_Tag = b'boundary='
    rn_end_Tag = b'\r\n'
    boundary_Tag_index = boundary.find(boundary_Tag)
    boundary = boundary[boundary_Tag_index:]
    end_index = boundary.find(rn_end_Tag)
    boundary = boundary[len(boundary_Tag):end_index]
    boundary = b'--' + boundary
    return boundary


def findUserName(receivedStr, boundary):
    boundaryIn = receivedStr.find(boundary)
    userName = receivedStr[boundaryIn + len(boundary):]
    rnindex = userName.find(b'\r\n\r\n')
    userName = userName[rnindex + len(b'\r\n\r\n'):]
    rnfinalIndex = userName.find(b'\r\n')
    # obtain UserName
    userName = userName[:rnfinalIndex]
    return userName


def findUserPassword(receivedStr, boundary):
    boundaryIn = receivedStr.find(boundary)
    restInfor = receivedStr[boundaryIn + len(boundary):]
    restNextIndex = restInfor.find(boundary)
    restInfor = restInfor[restNextIndex + len(boundary):]
    passwordIndex = restInfor.find(b'\r\n\r\n')
    password = restInfor[passwordIndex + len(b'\r\n\r\n'):]
    lastIndex = password.find(b'\r\n')
    password = password[:lastIndex]
    return password


def findUserfromDB(userName):
    userInformation = user_list.find_one({'UserName': userName})
    return userInformation


def inserUsertoDB(userName, password):
    hashedPassword = bcrypt.hashpw(password, bcrypt.gensalt())
    user_list.insert_one({'UserName': userName, 'Password': hashedPassword})


def function_404(information: str):
    myBytes = 'HTTP/1.1 404 Not Found\r\nContent-Type: text/plain; charset=utf-8\r\nContent-length: {}\r\n\r\n{}'.format(
        len(information.encode()), information).encode()
    return myBytes


def image_sender(image_path):
    f = open(image_path, 'rb')
    content = f.read()
    header = b"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nX-Content-Type-Options: nosniff\r\n" + b'Max-Age=4000; HttpOnly\r\nContent-length:'
    header += str(os.path.getsize(image_path)).encode()
    header += b'\r\n\r\n'
    header += content
    return header


def css_sender(file_path):
    f = open(file_path, 'rb')
    content = f.read()
    header = b"HTTP/1.1 200 OK\r\nContent-Type: text/css; charset=utf-8\r\nX-Content-Type-Options: nosniff\r\n" + b'Content-length:'
    header += str(os.path.getsize("style.css")).encode()
    header += b'\r\n\r\n'
    header += content
    return header


def general_sender(file_path, content):
    header = b"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nX-Content-Type-Options: nosniff\r\n"
    header += str(os.path.getsize(file_path)).encode()
    header += b'\r\n\r\n'
    header += content
    return header


def parse_to_dict(header_bytes):
    headers = header_bytes.decode('UTF-8')
    headersLst = headers.split('\r\n')
    headersLst.pop(0)
    # convert list to a dictionary
    res_dict = {}
    for s in headersLst:
        mid_idx = s.find(':')
        key = (str(s)[:mid_idx])
        val = (str(s)[mid_idx:])
        val = val.replace(': ', '')
        res_dict[key] = val

    return res_dict


def find_userName(res_dict):
    cookieDic = {}
    visitorName = ''

    print("res: ",res_dict)
    CookieLst = (res_dict['Cookie']).split(';')
    for i in CookieLst:
        i = i.strip()
        a = i.split('=')
        cookieDic[a[0]] = a[1]
    # print("cookieDic :", cookieDic)
    # sys.stdout.flush()
    for i in list(user_list.find({})):
        # print('i:', i)
        # sys.stdout.flush()
        if 'cookie' in i and 'token' in cookieDic:
            if bcrypt.checkpw(cookieDic['token'].encode(), i['cookie']):

                sys.stdout.flush()
                visitorName = i['UserName'].decode()

                sys.stdout.flush()
                visitorName = visitorName.replace('&', '&amp')
                visitorName = visitorName.replace('<', '&lt')
                visitorName = visitorName.replace('>', '&gt')
                visitorName = visitorName.replace('\r\n', '<br>')
                return visitorName

    return None

