# import socket
# import struct
# import sys
# import os
# import random

# MULTICAST_GROUP = '224.0.0.1'
# BUFFER_SIZE = 1024
# PORT_RANGE = (49152, 65535)  # Dynamic/private ports range

# def find_available_port():
#     while True:
#         port = random.randint(*PORT_RANGE)
#         try:
#             with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
#                 s.bind(('', port))
#                 return port
#         except OSError:
#             continue

# def admin_send_file(filename):
#     sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#     sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, struct.pack('b', 1))

#     port = find_available_port()
#     print(f"Using port: {port}")

#     try:
#         with open(filename, 'rb') as file:
#             print(f"Sending file: {filename}")

#             # Send port number first
#             sock.sendto(str(port).encode(), (MULTICAST_GROUP, port))

#             # Send filename
#             sock.sendto(filename.encode(), (MULTICAST_GROUP, port))

#             # Send file content
#             while True:
#                 data = file.read(BUFFER_SIZE)
#                 if not data:
#                     break
#                 sock.sendto(data, (MULTICAST_GROUP, port))

#             # Send end-of-file marker
#             sock.sendto(b'EOF', (MULTICAST_GROUP, port))

#         print("File sent successfully")
#     except FileNotFoundError:
#         print(f"File not found: {filename}")
#     finally:
#         sock.close()

# def user_receive_file():
#     sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#     sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

#     # Bind to any available port to receive the initial port number
#     sock.bind(('', 0))
#     _, listen_port = sock.getsockname()
#     print(f"Listening on port: {listen_port}")

#     # Tell the operating system to add the socket to the multicast group
#     group = socket.inet_aton(MULTICAST_GROUP)
#     mreq = struct.pack('4sL', group, socket.INADDR_ANY)
#     sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

#     print("Waiting for file...")

#     try:
#         # Receive port number
#         port_data, _ = sock.recvfrom(BUFFER_SIZE)
#         port = int(port_data.decode())
#         print(f"Received port number: {port}")

#         # Rebind to the received port
#         sock.close()
#         sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#         sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#         sock.bind(('', port))
#         sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

#         # Receive filename
#         filename, _ = sock.recvfrom(BUFFER_SIZE)
#         filename = filename.decode()
#         print(f"Receiving file: {filename}")

#         with open(f"received_{filename}", 'wb') as file:
#             while True:
#                 data, _ = sock.recvfrom(BUFFER_SIZE)
#                 if data == b'EOF':
#                     break
#                 file.write(data)

#         print(f"File received and saved as: received_{filename}")
#     finally:
#         sock.close()

# if __name__ == "__main__":
#     if len(sys.argv) < 2:
#         print("Usage: python script.py [admin|user] [filename]")
#         sys.exit(1)

#     role = sys.argv[1]

#     if role == 'admin':
#         if len(sys.argv) != 3:
#             print("Usage for admin: python script.py admin <filename>")
#             sys.exit(1)
#         filename = sys.argv[2]
#         admin_send_file(filename)
#     elif role == 'user':
#         user_receive_file()
#     else:
#         print("Invalid role. Use 'admin' or 'user'.")
#         sys.exit(1)




import pandas
import socket
import struct
import sys
import os
import hashlib

MULTICAST_GROUP = '224.0.0.1'
BUFFER_SIZE = 32768  # 16384
PORT = 5000


def calculate_checksum(filename):
    hash_md5 = hashlib.md5()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def admin_send_file(filename):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL,
                    struct.pack('b', 1))

    try:
        file_size = os.path.getsize(filename)
        checksum = calculate_checksum(filename)

        print(f"Sending file: {filename} (Size: {file_size} bytes)")

        # Send filename, size, and checksum
        header = f"{filename}|{file_size}|{checksum}"
        sock.sendto(header.encode(), (MULTICAST_GROUP, PORT))

        sent_bytes = 0
        with open(filename, 'rb') as file:
            while True:
                data = file.read(BUFFER_SIZE)
                if not data:
                    break
                sock.sendto(data, (MULTICAST_GROUP, PORT))
                sent_bytes += len(data)
                print(
                    f"\rProgress: {sent_bytes/file_size*100:.2f}%", end="", flush=True)

        # Send end-of-file marker
        sock.sendto(b'EOF', (MULTICAST_GROUP, PORT))
        print("\nFile sent successfully")

    except FileNotFoundError:
        print(f"File not found: {filename}")
    finally:
        sock.close()


def user_receive_file():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', PORT))

    group = socket.inet_aton(MULTICAST_GROUP)
    mreq = struct.pack('4sL', group, socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    print("Waiting for file...")

    try:
        # Receive file info
        file_info, _ = sock.recvfrom(BUFFER_SIZE)
        filename, file_size, expected_checksum = file_info.decode().split('|')
        file_size = int(file_size)

        print(f"Receiving file: {filename} (Size: {file_size} bytes)")

        received_bytes = 0
        with open(f"received_{filename}", 'wb') as file:
            while True:
                data, _ = sock.recvfrom(BUFFER_SIZE)
                if data == b'EOF':
                    break
                file.write(data)
                received_bytes += len(data)
                print(
                    f"\rProgress: {received_bytes/file_size*100:.2f}%", end="", flush=True)

        print("\nFile reception complete. Verifying integrity...")
        received_checksum = calculate_checksum(f"received_{filename}")
        if received_checksum == expected_checksum:
            print(f"File integrity verified. Saved as: received_{filename}")
        else:
            print("Warning: File integrity check failed. The file may be corrupted.")

    finally:
        sock.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py [admin|user] [filename]")
        sys.exit(1)

    role = sys.argv[1]

    if role == 'admin':
        if len(sys.argv) != 3:
            print("Usage for admin: python script.py admin <filename>")
            sys.exit(1)
        filename = sys.argv[2]
        admin_send_file(filename)
    elif role == 'user':
        user_receive_file()
    else:
        print("Invalid role. Use 'admin' or 'user'.")
        sys.exit(1)
