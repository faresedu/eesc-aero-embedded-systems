from simple_server import Server
import time
import signal

if '__main__' == __name__:
    server = Server(print_msg = True, msg_per_second = 10)
