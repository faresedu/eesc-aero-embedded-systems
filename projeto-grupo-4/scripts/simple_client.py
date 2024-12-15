import socket
import threading
import struct
import signal, types
import time

from simple_msg import ControlMsg, LabelString

HEADER = 24
HEADER_FORMAT = "!I20s"
FORMAT = "utf-8"
PORT = 5050
SERVER = "172.17.0.2"


CLIENT_PATTERN = types.SimpleNamespace(
    socket=None,
    addr=None,
    id="",
    data=types.SimpleNamespace(header=[], body=[]),
    peer="broadcast",
    is_alive=False,
)


class Client:
    def __init__(self, print_msg=False, msg_per_second=100):
        self.__verbose = print_msg

        signal.signal(signal.SIGINT, self.close_connection)  # Signal to end server

        self.__client = CLIENT_PATTERN

        self.__lock = threading.Lock()

        self.__msg_frequency = msg_per_second

        self.__start_client()

    def __log_function(self, msg):
        if self.__verbose:
            print(msg)

    def __start_client(self):
        try:
            # Initialize server like a TCP/IP socket
            self.__client.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        except Exception as e:
            self.__log_function("Client not started")
            self.__log_function(f"Error: {e}")
            return False

        return True

    def start_connection(
        self, server_ip=SERVER, server_port=PORT, id_client="", peer="broadcast"
    ):

        self.__client.peer = peer
        self.__client.id = id_client

        while not self.__client.is_alive:
            time.sleep(1)

            try:
                self.__client.socket.connect((server_ip, server_port))
                self.__client.is_alive = True
                break

            except Exception as e:
                self.__log_function(f"Error: {e}")
                self.__log_function("Trying to reconnect... Server is down?")
                self.__client.is_alive = False
                continue

        self.__log_function("Connected to server")
        self.__client.addr = self.__client.socket.getsockname()

        threading.Thread(target=self.sending_loop).start()
        threading.Thread(target=self.receiving_loop).start()
        self.connect_to_peer()

    def connect_to_peer(self):
        # id_msg = ControlMsg('/change_id', self.__client.id).pack_msg()
        # header_id = self.pack_header(id_msg, 'ControlMsg')

        peer_msg = ControlMsg("/change_peer", self.__client.peer).pack_msg()
        header_peer = self.pack_header(peer_msg, "ControlMsg")

        self.__client.data.header.append(header_peer)
        self.__client.data.body.append(peer_msg)

    def sending_loop(self):
        while self.__client.is_alive:
            if len(self.__client.data.body) < 1:
                time.sleep(1 / self.__msg_frequency)
                continue

            try:
                self.__log_function("Preparing to send a message...")
                header = self.__client.data.header.pop(0)
                data = self.__client.data.body.pop(0)

                self.__client.socket.sendall(header)
                self.__client.socket.sendall(data)
                self.__log_function("Message sent successfully.")
            except IndexError:
                self.__log_function(
                    "Error: Attempted to send a message from an empty queue."
                )
            except Exception as e:
                self.__log_function(f"Error sending message: {e}")

    def send_message(self, message=""):
        if not self.__client.is_alive:
            self.__log_function("Client is not connected")
            return

        try:
            if message.startswith("/"):
                # Handle control messages
                control_msg_parts = message.split(" ")
                control_msg_parts = control_msg_parts[:3]  # Only the first three parts
                msg = ControlMsg(*(command for command in control_msg_parts)).pack_msg()
                type_msg = "ControlMsg"

            else:
                # Handle label messages
                msg = LabelString(self.__client.id, message).pack_msg()
                type_msg = "LabelString"

            # Pack the header
            header = self.pack_header(msg, type_msg)

            # Add the message to the queue
            with self.__lock:
                self.__client.data.header.append(header)
                self.__client.data.body.append(msg)

            self.__log_function("Message added to send queue.")
        except Exception as e:
            self.__log_function(f"Error in send_message: {e}")

    def receiving_loop(self):
        while self.__client.is_alive:
            try:
                length_message, type_message = self.receive_header()

                if length_message == 0:
                    self.__log_function("No header received or error in header.")
                    time.sleep(3)  # Avoid busy waiting
                    continue

                self.receive_message(length_message, type_message)

            except Exception as e:
                self.__log_function(f"Critical error in receiving loop: {e}")
                with self.__lock:
                    self.__client.is_alive = False  # Mark the client as disconnected
                break

    def receive_header(self):
        header_length = HEADER
        header = b""

        while len(header) < header_length:
            try:
                chunk = self.__client.socket.recv(header_length - len(header))
                if not chunk:
                    # Socket was closed by the peer
                    self.__log_function(
                        "Connection reset by peer while receiving header."
                    )
                    return 0, ""
                header += chunk
            except ConnectionResetError as e:
                self.__log_function(f"Connection reset by peer: {e}")
                return 0, ""
            except Exception as e:
                self.__log_function(f"Error receiving header: {e}")
                return 0, ""

        try:
            length_message, type_message = self.unpack_msg(header)
            return length_message, type_message
        except Exception as e:
            self.__log_function(f"Error unpacking header: {e}")
            return 0, ""

    def receive_message(self, length_message, type_message):
        body_msg = b""
        msg_to_receive = length_message

        while len(body_msg) < length_message:
            try:
                chunk = self.__client.socket.recv(msg_to_receive)
                if not chunk:
                    # Socket was closed by the peer
                    self.__log_function(
                        "Connection reset by peer while receiving message."
                    )
                    return False
                body_msg += chunk
                msg_to_receive = length_message - len(body_msg)
            except ConnectionResetError as e:
                self.__log_function(f"Connection reset by peer: {e}")
                return False
            except Exception as e:
                self.__log_function(f"Error receiving body: {e}")
                return False

        if type_message != "ControlMsg":
            self.read_message(body_msg, type_message)
        else:
            self.handle_control_msg(body_msg)

        return True

    def read_message(self, body_msg, type_message):
        if type_message == "LabelString":
            label, string = LabelString().unpack_msg(body_msg)
            self.__log_function(f"{label}: {string}")

    def handle_control_msg(self, body_msg):
        command, arg1, arg2 = ControlMsg().unpack_msg(body_msg)

        if command == "/end_connection":
            self.close_connection()

        if command == "/change_peer":
            self.__client.peer = arg1
            self.__log_function(f"Peer changed to {arg1}")

        if command == "/peer_lost":
            self.__client.peer = "broadcast"
            self.__log_function("Peer lost. Changed to broadcast")

        if command == "/change_id":
            self.__client.id = arg1
            self.__log_function(f"ID changed to {arg1}")

    def close_connection(self, signal_received=None, frame=None):
        if signal_received is not None:
            print("Signal received: ", signal_received)

        if self.__client.socket is None:
            exit(0)
            return

        self.__client.is_alive = False
        self.__client.socket.close()
        self.__log_function("Connection closed")
        exit(0)

    def pack_header(self, message, type_message):
        len_msg = len(message)
        type_message = type_message.encode(FORMAT)

        header = struct.pack(HEADER_FORMAT, len_msg, type_message)

        header_bytes = header + b" " * (HEADER - len(header))

        return header_bytes

    def unpack_msg(self, header):
        length_message, type_message = struct.unpack(HEADER_FORMAT, header)
        type_message = type_message.decode(FORMAT).rstrip("\x00")

        return length_message, type_message

    def client_is_alive(self):
        return self.__client.is_alive
