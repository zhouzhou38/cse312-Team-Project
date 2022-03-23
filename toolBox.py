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

def findUserName(receivedStr,boundary):
    boundaryIn = receivedStr.find(boundary)
    userName = receivedStr[boundaryIn+len(boundary):]
    rnindex = userName.find(b'\r\n\r\n')
    userName = userName[rnindex+len(b'\r\n\r\n'):]
    rnfinalIndex = userName.find(b'\r\n')
    # obtain UserName
    userName = userName[:rnfinalIndex]
    return userName