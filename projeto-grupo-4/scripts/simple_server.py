import socket
import threading
import struct
import signal, types
import time

from simple_msg import ControlMsg

HEADER = 24
HEADER_FORMAT = "!I20s"
FORMAT = "utf-8"

SERVER_PATTERN = types.SimpleNamespace(
    socket=None,
    ip="127.0.0.1",
    port=5050,
    is_alive=False,
    clients_connected={},
)
OVERHEAD = 10
DISCARD = 2


class Server:
    def __init__(self, ip=None, port=None, print_msg=False, msg_per_second=100):

        # Public attributes
        self.lock = threading.Lock()  # Lock for threads

        signal.signal(signal.SIGINT, self.end_server)  # Signal to end server

        # Print attributes
        self.__verbose = print_msg  # Print messages

        self.__msg_frequency = msg_per_second  # Messages per second

        # Private attributes
        self.__server = SERVER_PATTERN

        if ip is not None:
            self.__server.ip = ip

        if port is not None:
            self.__server.port = port

        self.__start_server()  # Start server

    def __log_function(self, msg):
        if self.__verbose:
            print(msg)

    def __start_server(self):
        try:
            # Initialize server like a TCP/IP socket
            self.__server.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Set server to reuse address and port for restart events
            self.__server.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # Bind server to ip and port
            self.__server.socket.bind((self.__server.ip, self.__server.port))

            # Start listening for connections
            self.__server.socket.listen()

        except Exception as e:
            self.__log_function(f"Problem starting server: {e}")
            self.end_server()

        self.__server.is_alive = True
        self.__log_function(
            f"Server started at {self.__server.ip}:{self.__server.port}"
        )

        # start a accepting thread
        threading.Thread(target=self.accept_connections).start()

        while not self.__server.is_alive:
            time.sleep(1 / self.__msg_frequency)

    def end_server(self, signal_received=None, frame=None):
        if signal_received is not None:
            print("Signal received: ", signal_received)

        if self.__server.socket is not None:
            self.warning_down_server()
            self.__server.socket.close()
            self.__server.is_alive = False
            self.__log_function("Server ended")
            exit(0)

    def warning_down_server(self):
        for client_id, client in self.__server.clients_connected.items():
            try:
                msg = ControlMsg("/end_connection").pack_msg()
                header = self.pack_header(msg, "ControlMsg")
                client.socket.sendall(header)
                client.socket.sendall(msg)
            except Exception as e:
                self.__log_function(f"Error sending warning to {client_id}: {e}")

    def accept_connections(self):
        while self.__server.is_alive:
            try:
                client_socket, address = self.__server.socket.accept()
                # client_socket.settimeout(10)  # Optional: Prevent hanging connections

                current_client = self.add_new_client(client_socket, address)
                self.__log_function(f"New connection from {address}")

                # Send welcome message
                command_msg = ControlMsg("/new_peer", current_client.id).pack_msg()
                header = self.pack_header(command_msg, "ControlMsg")

                self.send_broadcast(
                    client=current_client, header=header, msg=command_msg
                )

                id_name = ControlMsg("/change_id", current_client.id).pack_msg()
                header_id = self.pack_header(id_name, "ControlMsg")

                current_client.socket.sendall(header_id)
                current_client.socket.sendall(id_name)

                # Start threads for client handling
                threading.Thread(
                    target=self.handle_client, args=(current_client,)
                ).start()
                threading.Thread(
                    target=self.sending_thread, args=(current_client,)
                ).start()

            except socket.error as e:
                self.__log_function(f"Socket error while accepting connection: {e}")
            except Exception as e:
                self.__log_function(f"Unexpected error: {e}")

    def add_new_client(self, client_socket, address):
        current_client = types.SimpleNamespace(
            socket=None, addr=None, id="", data=None, peer="broadcast", is_alive=True
        )
        current_client.socket = client_socket
        current_client.addr = address
        current_client.id = f"client_{len(self.__server.clients_connected)}"
        current_client.data = types.SimpleNamespace(header=[], body=[])

        with threading.Lock():
            self.__server.clients_connected[current_client.id] = current_client

        # Send new client broadcast
        msg = ControlMsg("/new_peer", current_client.id).pack_msg()
        header = self.pack_header(msg, "ControlMsg")
        self.send_broadcast(client=current_client, header=header, msg=msg)

        return current_client

    def handle_client(self, client):
        while self.__server.is_alive:
            try:
                length_message, type_message, header = self.receive_header(client)

                if not header:
                    self.__log_function("No header received")
                    break

            except Exception as e:
                self.__log_function(f"Error receiving header: {e}")
                break

            if not self.receive_message(client, length_message, type_message, header):
                break

    def receive_header(self, client):
        header_length = HEADER
        header = b""

        while len(header) < header_length:
            try:
                # Receives the header
                chunk = client.socket.recv(header_length - len(header))
                if not chunk:
                    # If the client disconnects while receiving the header
                    self.__log_function("Client disconnected while receiving header.")
                    self.remove_client(client)
                    return 0, "", b""

                header += chunk

            except Exception as e:
                self.__log_function(header)
                self.__log_function(f"Error receiving header: {e}")
                return 0, "", b""

        try:
            # Unpack the header
            length_message, type_message = self.unpack_header(header)
            return length_message, type_message, header

        except Exception as e:
            self.__log_function(f"Error unpacking header: {e}")
            return 0, "", b""

    def receive_message(self, client, length_message, type_message, header):
        body_msg = b""
        msg_to_receive = length_message

        while len(body_msg) < length_message:
            try:
                # Receive the remaining part of the message
                chunk = client.socket.recv(msg_to_receive)
                if not chunk:
                    # Client disconnected
                    self.__log_function("Client disconnected while receiving body.")
                    return False  # Indicates failure in receiving

                body_msg += chunk
                msg_to_receive = length_message - len(body_msg)

            except Exception as e:
                self.__log_function(f"Error receiving body: {e}")
                return False  # Indicates failure in receiving

        if type_message != "ControlMsg":
            # Store the received data in the client
            client.data.header.append(header)
            client.data.body.append(body_msg)
            return True  # Indicates successful reception

        # Handle control messages
        self.handle_control_msg(client, body_msg, header)
        return True  # Indicates successful reception

    def remove_client(self, client):
        with threading.Lock():
            self.update_peer_lost(client.id)
            self.__server.clients_connected.pop(client.id)
            client.socket.close()
            self.__log_function(f"Client {client.id} disconnected")

    def update_peer_lost(self, client_id):
        for _, client in self.__server.clients_connected.items():
            if client.peer == client_id:
                lost_msg = ControlMsg("/peer_lost", client_id).pack_msg()
                header = self.pack_header(lost_msg, "ControlMsg")

                client.socket.sendall(header)
                client.socket.sendall(lost_msg)

                client.peer = "broadcast"

    def pack_header(self, message, type_message):
        # Get the length of the message and the type of the message
        length_message = len(message)
        type_message = type_message  # Pack the header with the length of the message and the type of the message
        header = struct.pack(HEADER_FORMAT, length_message, type_message.encode(FORMAT))

        header_bytes = header + b" " * (HEADER - len(header))

        return header_bytes

    def unpack_header(self, header):
        # Unpack the header to get the length of the message and the type of the message
        length_message, type_message = struct.unpack(HEADER_FORMAT, header)
        type_message = type_message.decode(FORMAT).rstrip("\x00")

        return length_message, type_message

    def send_to_peer(self, client, msg, header):
        with threading.Lock():
            peer = next(
                (
                    peer_client
                    for peer_client in self.__server.clients_connected.keys()
                    if peer_client == client.peer
                ),
                None,
            )

            if peer is None:
                self.__log_function(f"Peer {client.peer} not found")
                return

            try:
                peer = self.__server.clients_connected[peer]
                peer.socket.sendall(header)
                peer.socket.sendall(msg)
            except Exception as e:
                self.__log_function(f"Error sending to peer {client.peer}: {e}")

    def send_broadcast(self, client, header, msg):
        with threading.Lock():
            for recipient_id, recipient in self.__server.clients_connected.items():
                if recipient.id == client.id:
                    continue  # Skip the sender

                try:
                    recipient.socket.sendall(header)
                    recipient.socket.sendall(msg)
                except Exception as e:
                    self.__log_function(
                        f"Error sending broadcast to {recipient_id}: {e}"
                    )

    def sending_thread(self, client):
        while self.__server.is_alive:
            try:
                if len(client.data.body) > 0:
                    header = client.data.header.pop(0)
                    msg = client.data.body.pop(0)

                    if client.peer == "broadcast":
                        self.send_broadcast(client=client, header=header, msg=msg)

                    else:
                        self.send_to_peer(client=client, header=header, msg=msg)

                if len(client.data.body) > OVERHEAD:
                    # Remove the oldest messages
                    client.data.header = client.data.header[-(OVERHEAD - DISCARD) :]
                    client.data.body = client.data.body[-(OVERHEAD - DISCARD) :]

            except Exception as e:
                self.__log_function(f"Error sending message: {e}")
                continue

            time.sleep(1 / self.__msg_frequency)

    def handle_control_msg(self, client, msg, header):
        command, arg1, arg2 = ControlMsg().unpack_msg(msg)

        if command.startswith("/change_peer"):
            client.peer = arg1
            self.__log_function(f"Peer changed to {arg1}")
            return

        if command.startswith("/change_id"):
            self.update_peers(client.id, arg1)
            client.id = arg1

            id_name = ControlMsg("/change_id", client.id).pack_msg()
            header_id = self.pack_header(id_name, "ControlMsg")

            client.socket.sendall(header_id)
            client.socket.sendall(id_name)

            return

    def update_peers(self, client_id, new_id):
        for _, clients in self.__server.clients_connected.items():
            if clients.peer == client_id:
                clients.peer = new_id

    def get_is_alive(self):
        return self.__server.is_alive
