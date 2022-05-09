import bcrypt
from pymongo import MongoClient

mongo_client = MongoClient('mongo')
mydb = mongo_client["CSE312db"]
user_list = mydb["user"]


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
