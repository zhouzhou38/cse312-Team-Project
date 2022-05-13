// Establish a WebSocket connection with the server
const socket = new WebSocket('ws://' + window.location.host + '/websocket');

let webRTCConnection;

// Allow users to send messages by pressing enter instead of clicking the Send button
document.addEventListener("keypress", function (event) {
    if (event.code === "Enter") {
        sendMessage();
    }
});

// Read the comment the user is sending to chat and send it to the server over the WebSocket as a JSON string
function sendMessage() {
    let friendName = document.getElementById("sendTo").value
    const chatBox = document.getElementById("friendName_"+friendName);
    const comment = chatBox.value
    chatBox.value = "";
    chatBox.focus();
    if (comment !== "") {
        let receiver = document.getElementById("sendTo").value
        let sender = document.getElementById("me").value
        socket.send(JSON.stringify({'messageType': 'chatMessage', 'sender': sender,'receiver':receiver,'msg':comment}));
    }
}

// Renders a new chat message to the page
function displayChatHistory(all_chats) {
    // all_chats = {friend1:["0hello","1hi","1how are you","0im good"],friend2:["1im kylin"]}
    console.log("all_chat",all_chats)
    for (const [key, value] of Object.entries(all_chats)) {
        let friendName = key;
        let chats = value;
        let chat_temp = ""
        for(let i=0;i<chats.length;i++){
            let msg = chats[i]
            if(msg[0] === '0'){
                chat_temp += "<p style=\"text-align: left\">"+msg.slice(1)+"</p>"

            }else{

                chat_temp += "<p style=\"text-align: right\">"+msg.slice(1)+"</p>"
            }
        }

        console.log("temp",chat_temp) // <p dir="rtl"></p >
        console.log("id: ","chat"+friendName) //chatfirefox
        document.getElementById("chat"+friendName).innerHTML = chat_temp;
    }

}

// called when the page loads to get the chat_history
function get_chat_history() {
    const request = new XMLHttpRequest();
    request.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            console.log("recv from server!")
            const messages = JSON.parse(this.response);
            displayChatHistory(messages)
        }
    };

    request.open("GET", "/chat-history");
    request.send();
}

function addMessage(msg){
    console.log("msg: ",msg)
    let sender = msg['sender']
    let receiver = msg['receiver']
    let me = document.getElementById("me").value
    let m = msg['msg']

    if (sender===me){
        document.getElementById("chat"+receiver).innerHTML += "\n<p style=\"text-align: right\">"+m+"</p>\n"
    }else{
        document.getElementById("chat"+sender).innerHTML += "\n<p style=\"text-align: left\">"+m+"</p>\n"
    }
}

// Called whenever data is received from the server over the WebSocket connection
socket.onmessage = function (ws_message) {
    const message = JSON.parse(ws_message.data);
    const messageType = message.messageType

    switch (messageType) {
        case 'chatMessage':

            addMessage(message);
            break;
        case 'webRTC-offer':
            webRTCConnection.setRemoteDescription(new RTCSessionDescription(message.offer));
            webRTCConnection.createAnswer().then(answer => {
                webRTCConnection.setLocalDescription(answer);
                socket.send(JSON.stringify({'messageType': 'webRTC-answer', 'answer': answer}));
            });
            break;
        case 'webRTC-answer':
            webRTCConnection.setRemoteDescription(new RTCSessionDescription(message.answer));
            break;
        case 'webRTC-candidate':
            webRTCConnection.addIceCandidate(new RTCIceCandidate(message.candidate));
            break;
        default:
            console.log("received an invalid WS messageType");
    }
}

function startVideo() {
    const constraints = {video: true, audio: true};
    navigator.mediaDevices.getUserMedia(constraints).then((myStream) => {
        const elem = document.getElementById("myVideo");
        elem.srcObject = myStream;

        // Use Google's public STUN server
        const iceConfig = {
            'iceServers': [{'url': 'stun:stun2.1.google.com:19302'}]
        };

        // create a WebRTC connection object
        webRTCConnection = new RTCPeerConnection(iceConfig);

        // add your local stream to the connection
        webRTCConnection.addStream(myStream);

        // when a remote stream is added, display it on the page
        webRTCConnection.onaddstream = function (data) {
            const remoteVideo = document.getElementById('otherVideo');
            remoteVideo.srcObject = data.stream;
        };

        // called when an ice candidate needs to be sent to the peer
        webRTCConnection.onicecandidate = function (data) {
            socket.send(JSON.stringify({'messageType': 'webRTC-candidate', 'candidate': data.candidate}));
        };
    })
}


function connectWebRTC() {
    // create and send an offer
    webRTCConnection.createOffer().then(webRTCOffer => {
        socket.send(JSON.stringify({'messageType': 'webRTC-offer', 'offer': webRTCOffer}));
        webRTCConnection.setLocalDescription(webRTCOffer);
    });

}

function welcome() {


    get_chat_history()

    // use this line to start your video without having to click a button. Helpful for debugging
    // startVideo();
}