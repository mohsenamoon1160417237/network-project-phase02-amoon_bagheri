import datetime
import os
import shutil
import socket
import threading

users = [
    {"username": "user1", "password": "1"}
]

hand_shakes = {}

authentication = {}

store_paths = {}


def authentication_required(function):
    def wrapper(*args, **kwargs):
        if authentication.get(args[3]):  # self.authenticated
            if authentication.get(args[3]).get('authenticated'):
                function(*args, **kwargs)
        else:
            args[2].sendall("Authentication not provided".encode())  # client_socket

    return wrapper


class ThreadManager:
    def __init__(self):
        self.thread_ids = list()
        self.counter = 0

    def create_new_thread(self, ftp, c_socket: socket):
        thread_id = self.counter + 1
        self.counter += 1
        th = threading.Thread(target=ftp.main, args=(c_socket, thread_id))
        self.thread_ids.append(thread_id)
        th.start()


class FTPHandler:

    def __init__(self, serv_socket: socket, thread_manager: ThreadManager):
        self.server_socket = serv_socket
        self.thread_manager = thread_manager
        host = 'localhost'
        port = 8085
        server_socket.bind((host, port))
        server_socket.listen(1)
        print(f"Server is listening on http://{host}:{port}")

    @classmethod
    def get_user(cls, user: str, client_socket: socket, thread_id: int):
        for u in users:
            if u.get('username') == user:
                authentication[thread_id] = {'username': user}
                client_socket.sendall("Retrieved username".encode())
                return
        client_socket.send("User name not found".encode())

    @classmethod
    def get_password(cls, password: str, client_socket: socket, thread_id: int):
        if authentication.get(thread_id):
            username = authentication[thread_id].get('username')
            for u in users:
                if u.get('username', '') == username and password == u.get('password', ''):
                    authentication[thread_id]['authenticated'] = True
                    client_socket.sendall("Authentication provided".encode())
                    return

            client_socket.send("Wrong password".encode())
        else:
            client_socket.send("First provide username".encode())

    @authentication_required
    def show_list(self, path_name: str, client_socket: socket, thread_id: int) -> None:
        base_path = os.getcwd() if path_name is None else path_name
        is_file = os.path.isfile(base_path)
        if is_file:
            client_socket.sendall(self.show_file_context(base_path))
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

    @authentication_required
    def send_file(self, file_path: str, client_socket: socket, thread_id: int) -> None:
        if os.path.isfile(file_path):
            fo = open(file_path, 'rb')
            f = fo.read()
            client_socket.sendall(f)
            fo.close()
        else:
            client_socket.sendall('Invalid file path'.encode())

    @authentication_required
    def receive_file(self, file: bytes, client_socket: socket, thread_id: int):
        mega_bytes_counter = 0
        total_file = b''
        while len(file) == 1000:
            if len(total_file) % 1000000 == 0:
                mega_bytes_counter += 1
                print(mega_bytes_counter)
            total_file += file
            client_socket.send("send_next_chunk".encode())
            file = client_socket.recv(4096)
        total_file += file
        client_socket.send("finished".encode())
        fw = open(store_paths[thread_id], "wb")
        fw.write(total_file)
        fw.close()
        hand_shakes[thread_id] = False
        store_paths[thread_id] = ''
        client_socket.send("OK2".encode())

    @authentication_required
    def delete_file(self, file_path: str, client_socket: socket, thread_id: int):
        if os.path.isfile(file_path):
            client_socket.send("Do you really wish to delete (Y/N)? ".encode())
            confirmation = client_socket.recv(1024).decode().strip()
            if confirmation.lower() == 'y':
                os.remove(file_path)
                client_socket.send("File deleted successfully".encode())
            else:
                client_socket.send("File deletion canceled".encode())
        else:
            client_socket.send("File not found".encode())

    @authentication_required
    def make_directory(self, dir_path: str, client_socket: socket, thread_id: int):
        try:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                client_socket.send(f"Directory created: {dir_path}".encode())
            else:
                client_socket.send("Directory already exists".encode())
        except Exception as e:
            client_socket.send(f"Error creating directory: {e}".encode())

    @authentication_required
    def remove_directory(self, dir_path: str, client_socket: socket, thread_id: int):
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            shutil.rmtree(dir_path, ignore_errors=True)
            client_socket.send(f"Directory removed: {dir_path}".encode())
        else:
            client_socket.send("Directory not found or not a directory".encode())

    @authentication_required
    def print_working_directory(self, dummy, client_socket: socket, thread_id: int):
        pwd = os.getcwd()
        client_socket.send(f"Current Directory: {pwd}".encode())

    @authentication_required
    def change_working_directory(self, dir_path: str, client_socket: socket, thread_id: int):
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            os.chdir(dir_path)
            client_socket.send(f"Changed directory to {dir_path}".encode())
        else:
            client_socket.send("Directory not found or not a directory".encode())

    @authentication_required
    def change_to_parent_directory(self, dummy, client_socket: socket, thread_id: int):
        os.chdir('..')
        pwd = os.getcwd()
        client_socket.send(f"Changed to parent directory: {pwd}".encode())

    def start(self):
        while True:
            client_socket, client_address = self.server_socket.accept()
            self.thread_manager.create_new_thread(self, client_socket)

    def main(self, client_socket: socket, thread_id: int):
        while True:
            request = client_socket.recv(1048576)
            if hand_shakes.get(thread_id):
                self.receive_file(request, client_socket, thread_id)
            else:
                request = request.decode()
            if request[:4] == "USER":
                self.get_user(request.split(" ")[1].strip(), client_socket, thread_id)
            elif request[:4] == "PASS":
                self.get_password(request.split(" ")[1].strip(), client_socket, thread_id)
            elif request[:4] == "LIST":
                path_name = request.split(" ")[1].strip() if len(request.split(" ")) > 1 else None
                self.show_list(path_name, client_socket, thread_id)
            elif request[:4] == "RETR":
                self.send_file(request.split(" ")[1].strip(), client_socket, thread_id)
            elif request[:4] == "STOR":
                if not hand_shakes.get(thread_id):
                    store_paths[thread_id] = request.split(" ")[2].strip()
                    client_socket.send("OK1".encode())
                    hand_shakes[thread_id] = True
            elif request[:4] == "DELE":
                file_path = request.split(" ")[1].strip()
                self.delete_file(file_path, client_socket, thread_id)
            elif request[:3] == "MKD":
                dir_path = request.split(" ")[1].strip()
                self.make_directory(dir_path, client_socket, thread_id)
            elif request[:3] == "RMD":
                dir_path = request.split(" ")[1].strip()
                self.remove_directory(dir_path, client_socket, thread_id)
            elif request[:4] == "PWD":
                self.print_working_directory(None, client_socket, thread_id)
            elif request[:3] == "CWD":
                dir_path = request.split(" ")[1].strip()
                self.change_working_directory(dir_path, client_socket, thread_id)
            elif request[:4] == "CDUP":
                self.change_to_parent_directory(None, client_socket, thread_id)
            elif request[:4] == "QUIT":
                client_socket.send("Connection closed".encode())
                client_socket.close()
                break


if __name__ == '__main__':
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    thread_man = ThreadManager()
    ftp_handler = FTPHandler(server_socket, thread_man)
    ftp_handler.start()
