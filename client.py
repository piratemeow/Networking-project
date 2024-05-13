import json
import socket
import os
from tkinter import filedialog
from tkinter import Tk
import cv2
import pickle
import struct

IP = socket.gethostbyname('localhost')
PORT = 8888
ADDR = (IP, PORT)
SIZE = 5024



def get_http_header(message):
    header = message.split("/n/n")[0]
    return header
def get_http_data(message):
    data = message.split("/n/n")[-1]
    return  data
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

def get_http_response_header(message:str):

    header = message.split("/n/n")[0]
    return header
def get_http_response_data(message):
    data = message.split("/n/n")[-1]
    return  data
def get_http_response_code_and_message(message:str):
    header = get_http_response_header(message)
    response = header.split("/n")[0]
    code = response.split(" ")[1]
    message = response.split(" ")[-1]
    return code,message
def upload_file(client,filename):
    filesize = os.path.getsize(filename)
    only_filename = filename.split('/')[-1]

    client.send(only_filename.encode())
    client.send(str(filesize).encode())

    msg = client.recv(SIZE).decode()
    print(f"SERVER: {msg}")

    with open(filename, "rb") as f:
        while True:
            data = f.read(SIZE)
            if not data:
                break
            client.send(data)

    print("Done with sending")


def download_file(client,filename):

    client.send(filename.encode())
    filename = client.recv(SIZE).decode().strip()
    filesize = int(client.recv(SIZE).decode().strip())
    client.send("Filename and filesize received".encode())
    with open(f"Download\{filename}", "wb") as f:
        while filesize > 0:
            data = client.recv(min(filesize, SIZE))
            if not data:
                break
            f.write(data)
            filesize -= len(data)

def play_video(client):
    data = b""
    payload_size = struct.calcsize("Q")
    while True:
        while len(data) < payload_size:
            packet = client.recv(4 * 4024)  # 4K buffer size
            if not packet:
                break
            data += packet
        if not data:
            break
        packed_msg_size = data[:payload_size]
        data = data[payload_size:]
        msg_size = struct.unpack("Q", packed_msg_size)[0]
        while len(data) < msg_size:
            data += client.recv(4 * 4024)  # 4K buffer size
        frame_data = data[:msg_size]
        data = data[msg_size:]
        frame = pickle.loads(frame_data)
        cv2.imshow('Client', frame)
        if cv2.waitKey(16) == 13:
            break
    cv2.destroyAllWindows()

def start():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(ADDR)

    received_message = client.recv(SIZE).decode()
    message = get_http_data(received_message)
    print(message)

    name = input("Name: ")
    password = input("Password: ")
    message = name+"\n"+password
    message = message.encode()
    request = make_http_request("GET",'/0',message)
    client.send(request)
    response_message = client.recv(SIZE).decode()      # Options message
    print(response_message)

    if (response_message=="Login Successful"):
        while True:
            received_message = client.recv(SIZE).decode()
            received_message = json.loads(received_message)            # Convert string to json
            print(received_message)
            option = input("Choose: ")
            url = '/'+option
            option = int(option)
            if (option==2):
                data = b"2"
                # header = make_http_header("POST",url)
                message = make_http_request("POST",url,data)
                client.send(message)
                root = Tk()
                root.withdraw()  # Hide the main window

                file_path = filedialog.askopenfilename()

                print("Selected file:", file_path)
                upload_file(client,file_path)
            elif (option==4):
                filename = input("Name the file you want to delete: ")
                request = make_http_request("DELETE","/"+filename,b'')
                client.send(request)
                response = client.recv(SIZE).decode()
                print(response)
                printable_message = get_http_response_data(response)
                print(printable_message)

            elif(option==1):
                filename = input("Which file do you want to download: ")
                message = make_http_request("GET",url,b"")
                client.send(message)
                download_file(client,filename)
            elif option == 3:
                filename = input("Which file do you want to play: ")
                message = make_http_request("GET",url,filename.encode())
                client.send(message)
                play_video(client)




start()