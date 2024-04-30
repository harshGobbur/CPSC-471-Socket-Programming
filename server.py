import socket
import os
import sys

def main():
    listenPort = get_port_from_args()
    welcomeSock = setup_server_socket(listenPort)
    print(f"Server listening on port {listenPort}...")
    
    try:
        accept_connections_forever(welcomeSock)
    finally:
        welcomeSock.close()

def get_port_from_args():
    if len(sys.argv) != 2:
        print("Usage: python server.py <portnumber>")
        sys.exit(1)

    try:
        listenPort = int(sys.argv[1])
    except ValueError:
        print("Please input a valid port number.")
        sys.exit(1)

    if listenPort not in range(65536):
        print("Port number must be in the range 0-65535.")
        sys.exit(1)
    
    return listenPort

def setup_server_socket(listenPort):
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.bind(('', listenPort))
    serverSocket.listen(1)
    return serverSocket

def accept_connections_forever(serverSocket):
    while True:
        print("Waiting for connections...")
        clientSock, addr = serverSocket.accept()
        print(f"Accepted connection from {addr}")
        handle_client(clientSock)

def handle_client(clientSock):
    try:
        while True:
            command = clientSock.recv(1024).decode()
            if not command or command == "quit":
                break
            process_command(clientSock, command)
    finally:
        clientSock.close()

def process_command(clientSock, command):
    split_command = command.split()
    if len(split_command) < 2:
        return  # Ignore malformed commands

    command_type, filename = split_command[0], split_command[1]
    
    if command_type == "put":
        handle_put(clientSock, filename)
    elif command_type == "ls":
        handle_ls(clientSock)
    elif command_type == "get":
        handle_get(clientSock, filename)

def handle_put(clientSock, filename):
    dataConn = setup_data_connection(clientSock)
    fileSize = int(recvAll(dataConn, 10))
    fileData = recvAll(dataConn, fileSize)
    save_file(filename, fileData)
    dataConn.close()

def handle_ls(clientSock):
    try:
        dataConn = setup_data_connection(clientSock)
        files = os.listdir('.')
        files_list = '\n'.join(files).encode()
        dataConn.sendall(files_list)
        print("Files sent to client:", files)
    except Exception as e:
        print("Error handling ls command:", e)
    finally:
        dataConn.close()

def handle_get(clientSock, filename):
    if not os.path.isfile(filename):
        clientSock.send(b"File not found")
        return

    dataConn = setup_data_connection(clientSock)
    send_file(dataConn, filename)
    dataConn.close()

def setup_data_connection(clientSock):
    dataSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    dataSock.bind(('', 0))
    dataSock.listen(1)
    ephemeral_port = dataSock.getsockname()[1]
    clientSock.send(str(ephemeral_port).encode())
    dataConn, _ = dataSock.accept()
    return dataConn

def send_file(dataConn, filename):
    with open(filename, 'rb') as file:
        fileData = file.read()
        dataSizeStr = str(len(fileData)).zfill(10)
        dataConn.sendall(dataSizeStr.encode() + fileData)

def save_file(filename, fileData):
    with open(filename, 'wb') as file:
        file.write(fileData)
    print(f"SUCCESS: Received {filename} from the client with the 'put' command")

def recvAll(sock, numBytes):
    recvBuff = b""
    while len(recvBuff) < numBytes:
        tmpBuff = sock.recv(numBytes - len(recvBuff))
        if not tmpBuff:
            break
        recvBuff += tmpBuff
    return recvBuff

if __name__ == "__main__":
    main()