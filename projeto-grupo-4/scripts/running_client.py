from simple_client import Client
from simple_msg import LabelString
import signal
import threading
import time

def finish_connection(signal_received, frame):
    print('SIGINT or CTRL-C detected. Exiting gracefully')
    client.close_connection()
    exit(0)

def check_client_alive():
    while client.client_is_alive():
        time.sleep(1)  # Aguarda 1 segundo antes de verificar novamente
    print("Client is no longer alive. Exiting.")
    client.close_connection()
    exit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, finish_connection)  # Signal to end server
    client = Client(print_msg=True)
    client.start_connection(id_client='Client_teste', peer='broadcast')

    # Inicia um thread para monitorar se o cliente está vivo
    client_alive_thread = threading.Thread(target=check_client_alive, daemon=True)
    client_alive_thread.start()

    # O loop principal de input
    while True:
        msg = input('')
        if msg:
            client.send_message(msg)



