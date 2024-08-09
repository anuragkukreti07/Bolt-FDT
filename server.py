# import socket
# import threading
# import os
# import zlib
# import ssl
# from cryptography.fernet import Fernet
# from flask import Flask, render_template, jsonify
# from datetime import datetime
# import json

# # Configuration
# HOST = '0.0.0.0'
# PORT = 65432
# WEB_PORT = 5000
# KEY = Fernet.generate_key()  # Persistent key in production
# fernet = Fernet(KEY)

# # Store active groups and transfer logs
# groups = {}
# transfer_logs = []

# app = Flask(__name__)

# # Real-time monitoring
# @app.route('/')
# def index():
#     return render_template('index.html')

# @app.route('/logs')
# def get_logs():
#     return jsonify(transfer_logs)

# def log_transfer(group_name, filename, status):
#     timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#     transfer_logs.append({
#         'group': group_name,
#         'file': filename,
#         'status': status,
#         'timestamp': timestamp
#     })

# def handle_client(conn, addr):
#     print(f"Connected by {addr}")
#     try:
#         # Receive group name
#         group_name = conn.recv(1024).decode()
#         if group_name not in groups:
#             conn.sendall(b"Group not found")
#             log_transfer(group_name, '', 'Failed: Group not found')
#             return

#         conn.sendall(b"Group found")

#         # Receive file name
#         filename = conn.recv(1024).decode()

#         # Receive file
#         encrypted_compressed_file = b''
#         while True:
#             data = conn.recv(1024)
#             if not data:
#                 break
#             encrypted_compressed_file += data

#         # Decrypt and decompress the file
#         decrypted_file = fernet.decrypt(encrypted_compressed_file)
#         decompressed_file = zlib.decompress(decrypted_file)

#         # Save the file
#         file_path = os.path.join(groups[group_name], filename)
#         with open(file_path, 'wb') as f:
#             f.write(decompressed_file)

#         print(f"File received and saved: {file_path}")
#         log_transfer(group_name, filename, 'Success')
#     finally:
#         conn.close()

# def start_server():
#     context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
#     context.load_cert_chain(certfile="server.crt", keyfile="server.key")


#     with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#         s.bind((HOST, PORT))
#         s.listen()
#         print(f"Server listening on {HOST}:{PORT}")
#         while True:
#             conn, addr = s.accept()
#             conn = context.wrap_socket(conn, server_side=True)
#             client_thread = threading.Thread(target=handle_client, args=(conn, addr))
#             client_thread.start()

# def create_group(group_name, directory):
#     if group_name in groups:
#         print(f"Group {group_name} already exists.")
#     else:
#         groups[group_name] = directory
#         print(f"Group {group_name} created with directory {directory}.")

# if __name__ == "__main__":
#     print("1. Start Server")
#     print("2. Create Group")
#     print("3. Start Web Monitoring")
#     choice = input("Enter choice: ")
#     if choice == '1':
#         start_server()
#     elif choice == '2':
#         group_name = input("Enter group name: ")
#         directory = input("Enter directory path: ")
#         create_group(group_name, directory)
#     elif choice == '3':
#         app.run(host=HOST, port=WEB_PORT)
#     else:
#         print("Invalid choice")








import socket
import os
import threading
import logging
from flask import Flask, jsonify, render_template

# Server configuration
HOST = "0.0.0.0"
PORT = 65432
BUFFER_SIZE = 4096

# Initialize Flask app for web monitoring
app = Flask(__name__)

# Directory to store group files
groups = {}

# Logger configuration
logging.basicConfig(filename='server.log', level=logging.INFO, format='%(asctime)s - %(message)s')

# Start server function
def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"Server listening on {HOST}:{PORT}")

        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_client, args=(conn, addr)).start()

# Handle client connections
def handle_client(conn, addr):
    with conn:
        print(f"Connected by {addr}")
        logging.info(f"Connected by {addr}")

        try:
            data = conn.recv(BUFFER_SIZE)
            decoded_data = data.decode('utf-8').strip()
            print(f"Received data: {decoded_data}")  # Debug print
            group_name, file_name = decoded_data.split('|')
        except UnicodeDecodeError as e:
            print(f"Unicode decode error: {e}")
            logging.error(f"Unicode decode error: {e}")
            return

        group_name = group_name.strip()
        file_name = file_name.strip()

        print(f"Group name received: '{group_name}'")  # Debug print
        print(f"File name received: '{file_name}'")    # Debug print

        if group_name in groups:
            file_path = os.path.join(groups[group_name], file_name)

            with open(file_path, 'wb') as f:
                while True:
                    bytes_read = conn.recv(BUFFER_SIZE)
                    if not bytes_read:
                        break
                    f.write(bytes_read)

            print(f"File '{file_name}' received and saved to '{groups[group_name]}'.")
            logging.info(f"File '{file_name}' received from {addr} and saved to '{groups[group_name]}'.")
        else:
            print(f"Group '{group_name}' does not exist.")
            logging.warning(f"Group '{group_name}' does not exist. Connection from {addr} closed.")

# Create group function
def create_group():
    group_name = input("Enter group name: ")
    directory = input("Enter directory path: ")

    if not os.path.exists(directory):
        os.makedirs(directory)

    groups[group_name] = directory
    print(f"Group {group_name} created with directory {directory}.")

    # Print the groups dictionary for verification
    print("Current groups:")
    for name, path in groups.items():
        print(f"Group: {name}, Path: {path}")

# Web monitoring function
@app.route('/')
def index():
    return render_template('index.html', groups=groups.keys())

@app.route('/logs')
def get_logs():
    with open('server.log', 'r') as file:
        logs = file.read()
    return f"<pre>{logs}</pre>"

def start_web_monitoring():
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == "__main__":
    while True:
        print("1. Start Server")
        print("2. Create Group")
        print("3. Start Web Monitoring")
        choice = input("Enter choice: ")

        if choice == '1':
            start_server()
        elif choice == '2':
            create_group()
        elif choice == '3':
            # Run the Flask app in a separate thread
            threading.Thread(target=start_web_monitoring).start()
        else:
            print("Invalid choice.")
