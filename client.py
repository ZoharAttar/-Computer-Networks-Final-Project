import socket
import struct
import threading
import time
from colorama import Fore


LISTEN_PORT = 13117


class Client:

    def __init__(self, name):
        self.name = name
        self.first = True
        self.address = 0
        self.server_port = 0
        self.disconnect = False

    def receive_udp_message(self):
        # Create a UDP socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind(('', LISTEN_PORT))  # Bind to all available interfaces

                if self.first:
                    print(Fore.YELLOW + "Client started, listening for offer requests...")

                # Receive data from the socket
                while True:
                    sock.setblocking(True)
                    data, address = sock.recvfrom(1024)
                    address = address[0]
                    magic_cookie, message_type, server_name, server_port = struct.unpack('!IB32sH', data)
                    server_name = server_name.rstrip(b'\0').decode('utf-8')
                    if magic_cookie != 0xabcddcba or message_type != 0x2:
                        continue
                    else:
                        print(Fore.CYAN + f"Received offer from server '{server_name}' at address {address}, attempting to connect...")
                        self.address = address
                        self.server_port = server_port
                        break
            sock.close()
        except KeyboardInterrupt:
            self.disconnect = True
            print(Fore.RED + 'Disconnecting.... Goodbye!')

    def get_input(self):
        """
        Get user input
        :return: user input
        """
        flag = False

        def timeout():
            nonlocal flag
            flag = True
            print(Fore.RED + 'Time is up! Enter any input to proceed')

        my_timer = threading.Timer(10, timeout)
        my_timer.start()
        user_input = input(Fore.YELLOW + 'Please enter your answer: \n').strip()
        my_timer.cancel()
        if flag:
            return 'NONE'
        else:
            return user_input

    def answering_questions(self, client_socket):
        answer = self.get_input()
        client_socket.sendall(answer.encode())

    def tcp_client(self, host, port, isBot = False):
        try:
            # Create a TCP/IP socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                try:
                    client_socket.connect((host, port))
                    client_socket.sendall(self.name.encode())
                    while True:
                        client_socket.settimeout(None)
                        data = client_socket.recv(1024)
                        if data.decode().startswith("Game over!") or data.decode().startswith("Game is tied"):
                            if not isBot:
                                print(Fore.RED + data.decode())
                            if isBot:
                                self.disconnect = True
                            break
                        elif data.decode().startswith(f"True or False:"):
                            if not isBot:
                                print(Fore.CYAN + data.decode())
                            self.answering_questions(client_socket)
                        elif data.decode() != "":
                                if not isBot:
                                    print(Fore.LIGHTMAGENTA_EX + data.decode())
                        elif data.decode() == "":
                            break
                except ConnectionRefusedError:
                    print(Fore.YELLOW + "Game currently in progress. Trying again in 10 seconds....\n")
                    time.sleep(10)

        except OSError:
            pass
        except KeyboardInterrupt:
            self.disconnect = True

        finally:
            client_socket.close()
            self.first = False
            if not isBot:
                if self.disconnect:
                    print(Fore.RED + 'Shutting down client.... Goodbye!')
                else:
                    print(Fore.RED + 'Server disconnected, listening for offer requests...\n\n')

    def run(self):
        while not self.disconnect:
            self.receive_udp_message()
            if not self.disconnect:
                self.tcp_client(self.address, self.server_port)


if __name__ == "__main__":
    player_name = 'ZOZO'
    client = Client(player_name)
    client.run()

