# import socket
# import os
# import zlib
# import ssl
# from cryptography.fernet import Fernet
# import time

# # Configuration
# SERVER = '127.0.0.1'
# PORT = 65432
# KEY = Fernet.generate_key()  # Same key as the server
# fernet = Fernet(KEY)
# RETRY_LIMIT = 5

# def send_file(group_name, file_path):
#     #context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
#     context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile="server.crt")

#     context.load_verify_locations('server.crt')

#     for attempt in range(RETRY_LIMIT):
#         try:
#             with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#                 s.connect((SERVER, PORT))
#                 s = context.wrap_socket(s, server_hostname=SERVER)

#                 # Send group name
#                 s.sendall(group_name.encode())
#                 response = s.recv(1024)
#                 if response.decode() != "Group found":
#                     print("Group not found on server.")
#                     return

#                 # Send file name
#                 filename = os.path.basename(file_path)
#                 s.sendall(filename.encode())

#                 # Compress and encrypt the file
#                 with open(file_path, 'rb') as f:
#                     file_data = f.read()

#                 compressed_file = zlib.compress(file_data)
#                 encrypted_file = fernet.encrypt(compressed_file)

#                 # Send the file data
#                 s.sendall(encrypted_file)

#                 print(f"File {filename} sent to group {group_name}")
#                 break
#         except (socket.error, ssl.SSLError) as e:
#             print(f"Connection failed: {e}. Retrying {attempt + 1}/{RETRY_LIMIT}...")
#             time.sleep(5)
#     else:
#         print("Failed to send the file after multiple attempts.")

# if __name__ == "__main__":
#     group_name = input("Enter group name: ")
#     file_path = input("Enter file path: ")
#     send_file(group_name, file_path)












import socket
import os

# Server configuration
SERVER = "127.0.0.1"
PORT = 65432
BUFFER_SIZE = 4096

def send_file(file_path, group_name):
    try:
        # Connect to the server
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((SERVER, PORT))

            # Send group name and file name
            file_name = os.path.basename(file_path)
            s.sendall(f"{group_name}|{file_name}".encode())

            # Send the file
            with open(file_path, "rb") as f:
                while True:
                    bytes_read = f.read(BUFFER_SIZE)
                    if not bytes_read:
                        # File transmission is done
                        break
                    s.sendall(bytes_read)

            print(f"File '{file_name}' sent successfully.")
    
    except Exception as e:
        print(f"Failed to send the file: {e}")

if __name__ == "__main__":
    group_name = input("Enter group name: ")
    file_path = input("Enter file path: ")
    
    if os.path.exists(file_path):
        send_file(file_path, group_name)
    else:
        print(f"File '{file_path}' does not exist.")
