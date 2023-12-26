import datetime
import os
import socket
import time


class FTPHandler:

    def __init__(self, serv_socket: socket):
        self.server_socket = serv_socket
        self.hand_shake = False
        self.store_path = ''
        host = 'localhost'
        port = 8090
        server_socket.bind((host, port))
        server_socket.listen(1)
        print(f"Server is listening on http://{host}:{port}")

    @classmethod
    def get_user(cls, user: str):
        pass

    @classmethod
    def get_password(cls, password: str):
        pass

    @classmethod
    def show_list(cls, path_name: str, client_socket: socket) -> None:
        base_path = os.getcwd() if path_name is None else path_name
        is_file = os.path.isfile(base_path)
        if is_file:
            client_socket.sendall(cls.show_file_context(base_path))
            return
        ls = os.listdir(base_path)
        files_list = list()
        for obj in ls:
            obj_path = os.path.join(base_path, obj)
            size = f' {os.path.getsize(obj_path)} bytes' if os.path.isfile(obj_path) else ''
            read = 'r' if os.access(obj_path, os.R_OK) else '-'  # Check for read access
            write = 'w' if os.access(obj_path, os.W_OK) else '-'  # Check for write access
            execute = 'x' if os.access(obj_path, os.X_OK) else '-'  # Check for execution access
            birth_time = datetime.datetime.fromtimestamp(os.stat(obj_path).st_ctime).strftime("%b %d %H:%M")
            files_list.append(f'{birth_time} {read}{write}{execute} {obj}{size}'.encode())
        client_socket.sendall("\n".encode().join(files_list))

    @staticmethod
    def show_file_context(file_path: str):
        fo = open(file_path, "rb")
        f = fo.read()
        fo.close()
        return f

    @classmethod
    def send_file(cls, file_path: str, client_socket: socket) -> None:
        if os.path.isfile(file_path):
            fo = open(file_path, 'rb')
            f = fo.read()
            client_socket.sendall(f)
            fo.close()
        else:
            client_socket.sendall('Invalid file path'.encode())

    def receive_file(self, file: bytes, client_socket: socket):
        fw = open(self.store_path, "wb")
        fw.write(file)
        fw.close()
        self.hand_shake = False
        self.store_path = ''
        client_socket.send("OK2".encode())

    def main(self):
        while True:
            if not self.hand_shake:
                client_socket, client_address = self.server_socket.accept()
            request = ''
            counter = 0
            while counter != 3:
                request = client_socket.recv(1048576)
                request += request
                time.sleep(1)
                print(counter)
                print(len(request))
                counter += 1
            print(len(request))
            if self.hand_shake:
                self.receive_file(request, client_socket)
            else:
                request = request.decode()
            if request[:4] == "USER":
                self.get_user(request.split(" ")[1].strip())
            elif request[:4] == "PASS":
                self.get_password(request.split(" ")[1].strip())
            elif request[:4] == "LIST":
                path_name = request.split(" ")[1].strip() if len(request.split(" ")) > 1 else None
                self.show_list(path_name, client_socket)
            elif request[:4] == "RETR":
                self.send_file(request.split(" ")[1].strip(), client_socket)
            elif request[:4] == "STOR":
                if not self.hand_shake:
                    self.store_path = request.split(" ")[2].strip()
                    client_socket.send("OK1".encode())
                    self.hand_shake = True
                # else:
                #     self.receive_file(request.split("EOF")[0].replace("STOR", "").strip(), client_socket)
            if not self.hand_shake:
                client_socket.close()


if __name__ == '__main__':
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ftp_handler = FTPHandler(server_socket)
    ftp_handler.main()
