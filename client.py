import socket
import os
import time

HOST = "localhost"  # The server's hostname or IP address
PORT = 8090  # The port used by the server
hand_shake = False

while 1:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    user_input = input("Enter input: ")
    if user_input[:4] == "STOR":
        if not os.path.isfile(user_input.split(" ")[1]):
            print("invalid file path")
            continue
    s.sendall(user_input.encode())
    data = s.recv(4096).decode()
    print(data)
    if data == "OK1" and not hand_shake:
        print("entered ok1")
        hand_shake = True
        fo = open(user_input.split(" ")[1], "rb")
        f = fo.read()
        fo.close()
        s.sendall(f)
        s.send("End")
        data = s.recv(4096).decode()
    if data == "OK2" and hand_shake:
        hand_shake = False
    if user_input[:4] == "RETR":
        if data != 'Invalid file path':
            file_name = user_input.split(" ")[1].split("/")[-1]
            fw = open(os.path.join(os.getcwd(), file_name), "w")
            fw.write(data)
            fw.close()
    else:
        print(data)
    s.close()
