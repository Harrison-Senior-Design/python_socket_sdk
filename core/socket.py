import zmq

class Socket:
    SOCKET_TYPE = zmq.ROUTER;

    def __init__(self, addr):
        self.addr = addr

        ctx = zmq.Context()
        self.socket = ctx.socket(Socket.SOCKET_TYPE)

    def connect(self):
        self.socket.bind(self.addr)

    def recv(self):
        return self.socket.recv()
