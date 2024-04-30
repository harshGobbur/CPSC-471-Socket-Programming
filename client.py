import socket
import os
import sys

def recvAll(sock, numBytes):
    # The buffer to all data received from the client.
    recvBuff = "b"
    
    # Keep receiving till all is received
    while len(recvBuff) < numBytes:
        
        # Attempt to receive bytes
        tmpBuff = sock.recv(numBytes - len(recvBuff))
        
        # The other side has closed the socket
        if not tmpBuff:
            break
        
        # Add the received bytes to the buffer
        recvBuff += tmpBuff
    
    return recvBuff

# make sure there's 3 command line arguments
if len(sys.argv) != 3:
    print("Usage: python client.py <serveraddress> <portnumber>")
    sys.exit(1)


adress = sys.argv[1]


try:
    serverPort = int(sys.argv[2])
except ValueError:
    print("Please enter a port number.")
    sys.exit(1)


if serverPort not in range(1, 65536):
    print("Port number must be in the range 1-65535.")
    sys.exit(1)

controlSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect to the server
controlSock.connect((adress, serverPort))

# Create data connections with ephemeral ports to  
# listen for ls, get, put, or quit commands
while True:
    command = input("ftp> ")
    split_command = command.split()

    if split_command[0] == "put" and len(split_command) == 2:
        fileName = split_command[1]
        if os.path.isfile(fileName):
            # Send the put command to the server
            controlSock.send(command.encode())

            # Receive the ephemeral port number
            ephemeral_port = int(controlSock.recv(1024).decode())

            # Create a new socket for the data connection
            dataSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            dataSock.connect((adress, ephemeral_port))

            # Open the file
            with open(fileName, "rb") as fileObj:
                # Read the entire file at once
                fileData = fileObj.read()

            # Get the size of the data read and convert it to string
            dataSizeStr = str(len(fileData))

            # Prepend 0's to the size string until the size is 10 bytes
            while len(dataSizeStr) < 10:
                dataSizeStr = "0" + dataSizeStr

            # Prepend the size of the data to the file data
            fileData = dataSizeStr.encode() + fileData

            # Send the file data over the data connection
            dataSock.sendall(fileData)
            print(f"Sent {fileName} with size {len(fileData)} to the server.")

            # Close the data connection
            dataSock.close()
        else:
            print("File not found.")
            
    elif split_command[0] == "ls":
        # Send the ls command to the server
        controlSock.send(command.encode())

        # Receive the ephemeral port number
        ephemeral_port = int(controlSock.recv(1024).decode())

        # Create a new socket for the data connection
        dataSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        dataSock.connect((adress, ephemeral_port))

        # Receive the list of files
        files_list = recvAll(dataSock, 4096)  # Adjust buffer size as needed
        print("Files on the server:\n", files_list.decode())

        # Close the data connection
        dataSock.close()
        
    elif split_command[0] == "get" and len(split_command) == 2:
        # Send the get command to the server
        controlSock.send(command.encode())

        # Receive the ephemeral port number or file not found message
        serverResponse = controlSock.recv(1024).decode()

        if serverResponse.isdigit():
            ephemeral_port = int(serverResponse)

            # Create a new socket for the data connection
            dataSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            dataSock.connect((adress, ephemeral_port))

            # Receive the file size
            fileSizeBuff = recvAll(dataSock, 10)
            fileSize = int(fileSizeBuff)

            print(f"Receiving file of size {fileSize} bytes")

            # Receive the file data
            fileData = recvAll(dataSock, fileSize)

            # Save the file data to a file
            with open(split_command[1], 'wb') as file:
                file.write(fileData)

            print(f"Received and saved file as {split_command[1]}")

            # Close the data connection
            dataSock.close()
        else:
            print(serverResponse)  # Print the file not found message or any other message
    elif split_command[0] == "quit":
        controlSock.send(command.encode())
        break
    else:
        print("Unknown command.")

# Close the control socket
controlSock.close()