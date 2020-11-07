import socket


class Network:

    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = "192.168.1.8"
        self.port = 5050
        self.addr = (self.host, self.port)
        self.game_id, self.id = self.connect()
        print(self.game_id, self.id)

    def connect(self):
        self.client.connect(self.addr)
        recv_msg = self.client.recv(4096).decode().split(",")
        return recv_msg[0], recv_msg[1]

    def send(self, data):
        try:
            self.client.send(str.encode(data))
            reply = self.client.recv(4096).decode()
            return reply
        except socket.error as e:
            return str(e)
