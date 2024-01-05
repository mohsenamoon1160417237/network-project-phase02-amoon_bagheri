import socket
import os

HOST = "localhost"  # The server's hostname or IP address
PORT = 8083  # The port used by the server
hand_shake = False
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))

while 1:
    user_input = input("Enter input: ")
    if user_input[:4] == "STOR":
        if not os.path.isfile(user_input.split(" ")[1]):
            print("invalid file path")
            continue
    if user_input[:4] == "QUIT":
        s.sendall(user_input.encode())
        response = s.recv(4096).decode()
        print(response)
        s.close()
        break
    if user_input[:4] == "DELE":
        s.sendall(user_input.encode())
        confirmation_request = s.recv(4096).decode()
        print(confirmation_request)
        if confirmation_request == "File not found":
            continue
        confirmation = input()
        s.sendall(confirmation.encode())
        delete_response = s.recv(4096).decode()
        print(delete_response)
        continue
    s.sendall(user_input.encode())
    data = s.recv(8192).decode()
    if data == "OK1" and not hand_shake:
        print("entered ok1")
        hand_shake = True
        fo = open(user_input.split(" ")[1], "rb")
        f = fo.read()
        fo.close()
        s.sendall(f)
        data = s.recv(8192).decode()
    if data == "OK2" and hand_shake:
        hand_shake = False
    if user_input[:4] == "RETR":
        if data != 'Invalid file path':
            file_name = user_input.split(" ")[1].split("/")[-1]
            fw = open(os.path.join(os.getcwd(), file_name), "w")
            fw.write(data)
            fw.close()
    if user_input[:4] == "QUIT":
        s.sendall(user_input.encode())
        response = s.recv(4096).decode()
        print(response)
        s.close()
        break

    else:
        print(data)
