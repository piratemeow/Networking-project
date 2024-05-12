import json
import socket
import os
import threading
from login import login
import cv2
import pickle
import struct

IP = socket.gethostbyname('localhost')
PORT = 8888
ADDR = (IP, PORT)
SIZE = 5024

options = {
    "Download Item": 1,
    "Upload Item": 2,
    "Play Video": 3,
    "Delete Item": 4
}

def get_http_header(message):
    header = message.split("/n/n")[0]
    return header
def get_http_data(message):
    data = message.split("/n/n")[-1]
    return  data

def get_request_method(header):
    method = header.split()[0]
    return  method

def get_request_url(header):
    url = header.split()[1].strip("/")
    return url

def make_http_header(method,url):
    request_line = method+" "+url+" "+"HTTP/1.1/n"
    host = "localhost:8889/n"
    connection = "keep-alive/n"
    accept_language = "eng/n"
    new_line = "/n"
    return request_line+host+connection+accept_language+new_line

def make_http_request(method,url,data:bytes):
    header = make_http_header(method,url)
    header = header.encode()
    message = header+data
    return message

def make_http_response_header(code,response_message):
    status_line = "HTTP/1.1/n" + " " + code + " "+ response_message
    host = "localhost:8889/n"
    connection = "keep-alive/n"
    accept_language = "eng/n"
    content_type = "text"
    new_line = "/n"
    return status_line+host+connection+accept_language+content_type+new_line

def make_http_response(code,response_message,data:bytes):
    header = make_http_response_header(code,response_message)
    header = header.encode()
    message = header+data
    return message

def POST_method(header,client_socket,addr):
    url = get_request_url(header)
    url = int(url)
    if (url==2):
        receive_item(client_socket,addr)

def DELETE_method(header,client_socket,addr):
    url = get_request_url(header)
    delete_item(url)

def GET_method(header,client_socket,addr):
    url = get_request_url(header)
    filename = "Server\\video.mp4"
    if len(url) == 1:
        url = int(url.split("/")[-1])

    else:
        filename = f"Server\{url.split('/')[-1]}"
    if url == 1:
        send_item(client_socket,addr)
    elif url == 3:
        play_video(client_socket,addr,filename)



def delete_item(filename):
    file_path = f"Server\{filename}"
    try:
        os.remove(file_path)
        print(f"File '{file_path}' deleted successfully.")
    except OSError as e:
        print(f"Error: {e.strerror}")

def send_item(client_socket,addr):

    message = client_socket.recv(SIZE).decode()
    filename = message
    filesize = os.path.getsize(f"Server\{filename}")
    only_filename = filename.split('/')[-1]

    client_socket.send(only_filename.encode())
    client_socket.send(str(filesize).encode())

    msg = client_socket.recv(SIZE).decode()
    print(f"SERVER: {msg}")

    with open(f"Server\{filename}", "rb") as f:
        while True:
            data = f.read(SIZE)
            if not data:
                break
            client_socket.send(data)
    print("Done with sending")

def receive_item(client_socket,addr):

    filename = client_socket.recv(SIZE).decode().strip()
    filesize = int(client_socket.recv(SIZE).decode().strip())

    print("[+] Filename and filesize received from the client.")
    client_socket.send("Filename and filesize received".encode())

    with open(f"Server\{filename}", "wb") as f:
        while filesize > 0:
            data = client_socket.recv(min(filesize, SIZE))
            if not data:
                break
            f.write(data)
            filesize -= len(data)
            # bar.update(len(data))


def play_video(client_socket,addr,videoname):
    cap = cv2.VideoCapture(videoname)
    while True:
        ret, frame = cap.read()
        frame_data = pickle.dumps(frame)
        client_socket.sendall(struct.pack("Q", len(frame_data)))
        client_socket.sendall(frame_data)
        cv2.imshow('Server', frame)
        if cv2.waitKey(1) == 13:
            break
    cap.release()
    cv2.destroyAllWindows()


def packet_data_json(data):
    data = json.dumps(data)           # Convert the json data to string
    message = data.encode()
    return message
def serve_client(client_socket,addr):
    message = packet_data_json(options)
    print("Options Send")
    client_socket.send(message)
    response_message = client_socket.recv(SIZE).decode()
    header = get_http_header(response_message)
    http_method = get_request_method(header)
    # response_message = int(response_message)
    if (http_method=="POST"):
        POST_method(header,client_socket,addr)
    elif (http_method=="DELETE"):
        DELETE_method(header,client_socket,addr)
    elif(http_method=="GET"):
        GET_method(header,client_socket,addr)

    serve_client(client_socket,addr)






def validate_client(client_socket,addr):
    print(f"[+] Client connected from {addr[0]}:{addr[1]}")
    message = b"Please enter your name and password"
    message = make_http_request("POST","/0",message)
    client_socket.send(message)

    response_message = client_socket.recv(SIZE).decode()
    response_message = get_http_data(response_message)
    name_and_pass = response_message.split('\n')
    name = name_and_pass[0]
    password = name_and_pass[1]
    if login(name,password):
        response_message = b"Login Successful"
        client_socket.send(response_message)
        print("Login Successful")
        serve_client(client_socket,addr)

    else:
        response_message = b"Login Unsuccessful"
        client_socket.send(response_message)
        print("Invalid Credentials")


def start():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(ADDR)
    server.listen()
    print("[+] Listening...")
    while True:
        client_socket,addr = server.accept()
        thread = threading.Thread(target=validate_client,args=(client_socket,addr))
        thread.start()



start()